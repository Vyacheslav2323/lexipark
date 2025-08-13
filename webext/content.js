(function(){
  let panel = null
  let clickBound = false
  function isEditable(el){
    const tag = (el && el.tagName || '').toLowerCase()
    return tag==='input'||tag==='textarea'||(el && el.isContentEditable)
  }
  function ensurePanel(){
    if (panel) return panel
    const host = document.createElement('div')
    const shadow = host.attachShadow({ mode:'open' })
    const style = document.createElement('style')
    style.textContent = `.interactive-word{cursor:pointer;position:relative;transition:background-color .2s;border-radius:3px}
    .interactive-word:hover{background:#e3f2fd}
    .interactive-word:not(.in-vocab){background:#d4edda}
    .interactive-word:not(.in-vocab):hover{background:#c3e6cb}
    .lp-tooltip{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:5px 8px;border-radius:4px;font-size:12px;white-space:nowrap;opacity:0;pointer-events:none;transition:opacity .12s;z-index:1000}
    .interactive-word:hover .lp-tooltip{opacity:1}`
    const wrap = document.createElement('div')
    wrap.style.cssText = 'position:fixed;bottom:16px;right:16px;width:600px;max-width:80vw;max-height:60vh;overflow:auto;background:#fff;border:1px solid #e5e7eb;box-shadow:0 4px 16px rgba(0,0,0,.2);border-radius:10px;padding:12px;font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif;z-index:999999'
    shadow.appendChild(style)
    shadow.appendChild(wrap)
    document.documentElement.appendChild(host)
    panel = { host, wrap }
    return panel
  }

  function isEligiblePos(pos){
    if (!pos) return false
    if (pos.indexOf('VV') !== -1 || pos.indexOf('VA') !== -1 || pos.indexOf('VX') !== -1) return true
    const allowed = new Set(['NNG','NNP','NP','NR','MAG','MAJ','MM','XR'])
    return allowed.has(pos)
  }

  function buildMaps(words){
    const trans = new Map()
    const cand = new Map()
    for (const w of words) {
      if (!isEligiblePos(w.pos)) continue
      const base = (w.base || '').trim()
      const surface = (w.surface || '').trim()
      const t = { translation: (w.translation || ''), base, in_vocab: !!w.in_vocab, color: w.color, pos: w.pos || '', grammar_info: w.grammar_info || '' }
      const add = (k) => {
        if (!k) return
        trans.set(k, t)
        const f = k[0]
        if (!cand.has(f)) cand.set(f, [])
        cand.get(f).push(k)
      }
      add(base)
      add(surface)
    }
    for (const [k, arr] of cand) arr.sort((a,b)=>b.length-a.length)
    return { trans, cand }
  }

  function splitHangulRun(run, cand, trans){
    const frag = document.createDocumentFragment()
    let i = 0
    while (i < run.length) {
      const list = cand.get(run[i]) || []
      let match = ''
      for (const key of list) {
        if (run.startsWith(key, i)) { match = key; break }
      }
      if (match) {
        const span = document.createElement('span')
        span.className = 'interactive-word'
        const tip = document.createElement('span')
        tip.className = 'lp-tooltip'
        tip.textContent = trans.get(match) || match
        const meta = trans.get(match)
        if (meta && typeof meta === 'object') {
          if (meta.color) span.style.backgroundColor = meta.color
          if (meta.in_vocab) span.classList.add('in-vocab')
          tip.textContent = meta.translation || (meta.base || match)
          span.dataset.original = meta.base || match
          span.dataset.translation = meta.translation || ''
          span.dataset.pos = meta.pos || ''
          span.dataset.grammar = meta.grammar_info || ''
        }
        span.textContent = match
        span.appendChild(tip)
        frag.appendChild(span)
        i += match.length
      } else {
        frag.appendChild(document.createTextNode(run[i]))
        i += 1
      }
    }
    return frag
  }

  function bindWordClicks(){
    if (clickBound) return
    document.addEventListener('click', (e) => {
      const el = e.target && e.target.closest && e.target.closest('.interactive-word')
      if (!el) return
      const payload = {
        korean_word: el.dataset.original || el.textContent || '',
        pos: el.dataset.pos || '',
        grammar_info: el.dataset.grammar || '',
        translation: el.dataset.translation || ''
      }
      const ensureTranslationAndSave = (p) => {
        chrome.runtime.sendMessage({ type:'save-vocab', ...p }, (resp) => {
          if (!resp) return
          if (resp.ok) {
            el.classList.add('in-vocab')
            if (!el.style.backgroundColor) el.style.backgroundColor = 'rgba(255, 255, 0, 0.25)'
            const tip = el.querySelector('.lp-tooltip')
            if (tip) tip.textContent = (p.translation || p.korean_word)
            try { console.info('Saved to vocab:', p.korean_word) } catch(_){ }
          } else if (resp.data && resp.data.message) {
            try { console.warn('Save vocab failed:', resp.data.message) } catch(_){ }
          } else if (resp.error) {
            try { console.warn('Save vocab error:', resp.error) } catch(_){ }
          }
        })
      }
      if (!payload.translation) {
        chrome.runtime.sendMessage({ type:'translate-word', word: payload.korean_word }, (tr) => {
          const t = tr && tr.data && tr.data.translation ? tr.data.translation : ''
          if (t) {
            payload.translation = t
            el.dataset.translation = t
            const tip = el.querySelector('.lp-tooltip')
            if (tip) tip.textContent = t
          }
          ensureTranslationAndSave(payload)
        })
      } else {
        ensureTranslationAndSave(payload)
      }
    })
    clickBound = true
  }

  let hoverBound = false
  function bindWordHoverTranslate(){
    if (hoverBound) return
    document.addEventListener('mouseover', (e) => {
      const el = e.target && e.target.closest && e.target.closest('.interactive-word')
      if (!el) return
      const has = el.dataset.translation && el.dataset.translation.trim().length>0
      const pending = el.dataset.trPending === '1'
      if (has || pending) return
      const word = el.dataset.original || el.textContent || ''
      if (!word) return
      el.dataset.trPending = '1'
      chrome.runtime.sendMessage({ type:'translate-word', word }, (tr) => {
        const t = tr && tr.data && tr.data.translation ? tr.data.translation : ''
        if (t) {
          el.dataset.translation = t
          const tip = el.querySelector('.lp-tooltip')
          if (tip) tip.textContent = t
        }
        delete el.dataset.trPending
      })
    })
    hoverBound = true
  }

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === 'analyze-result') {
      const { wrap } = ensurePanel()
      const data = msg.data || {}
      const words = data.words || []
      wrap.innerHTML = ''
      const title = document.createElement('div')
      title.textContent = 'LexiPark — Analysis'
      title.style.cssText = 'font-weight:600;margin-bottom:8px'
      wrap.appendChild(title)
      const container = document.createElement('div')
      container.style.cssText = 'line-height:1.8; font-size:16px'
      for (const w of words) {
        const span = document.createElement('span')
        span.className = 'interactive-word'
        const tip = document.createElement('span')
        tip.className = 'lp-tooltip'
        tip.textContent = w.translation || w.base || w.surface || ''
        span.textContent = w.base || w.surface || ''
        span.appendChild(tip)
        container.appendChild(span)
        container.appendChild(document.createTextNode(' '))
      }
      wrap.appendChild(container)
      sendResponse({ ok:true })
    }
    if (msg.type === 'analyze-html-result') {
      const { wrap } = ensurePanel()
      const data = msg.data || {}
      const html = data.html || ''
      wrap.innerHTML = ''
      const title = document.createElement('div')
      title.textContent = 'LexiPark — Interactive'
      title.style.cssText = 'font-weight:600;margin-bottom:8px'
      wrap.appendChild(title)
      const container = document.createElement('div')
      container.innerHTML = html
      container.querySelectorAll('.interactive-word').forEach(el => {
        const t = el.getAttribute('data-translation') || el.textContent || ''
        const tip = document.createElement('span')
        tip.className = 'lp-tooltip'
        tip.textContent = t
        el.appendChild(tip)
      })
      wrap.appendChild(container)
      sendResponse({ ok:true })
    }
    if (msg.type === 'annotate-inplace') {
      const data = msg.data || {}
      const words = data.words || []
      const { trans, cand } = buildMaps(words)
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) => {
          if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT
          const p = node.parentElement
          if (!p || isEditable(p)) return NodeFilter.FILTER_REJECT
          if (p.closest && p.closest('.interactive-word')) return NodeFilter.FILTER_REJECT
          return NodeFilter.FILTER_ACCEPT
        }
      })
      const replacements = []
      const hangulRe = /[\uAC00-\uD7A3]+/g
      while (true) {
        const node = walker.nextNode()
        if (!node) break
        const text = node.nodeValue
        let lastIndex = 0
        let m
        let changed = false
        const frag = document.createDocumentFragment()
        while ((m = hangulRe.exec(text)) !== null) {
          const start = m.index
          const end = start + m[0].length
          if (start > lastIndex) frag.appendChild(document.createTextNode(text.slice(lastIndex, start)))
          const run = m[0]
          const sub = splitHangulRun(run, cand, trans)
          if (sub.childNodes.length && Array.from(sub.childNodes).some(n => n.nodeType===1)) changed = true
          frag.appendChild(sub)
          lastIndex = end
        }
        if (lastIndex < text.length) frag.appendChild(document.createTextNode(text.slice(lastIndex)))
        if (changed) replacements.push({ node, frag })
      }
      if (replacements.length) {
        const styleId = 'lexipark-inline-style'
        if (!document.getElementById(styleId)) {
          const style = document.createElement('style')
          style.id = styleId
          style.textContent = `.interactive-word{cursor:pointer;position:relative;transition:background-color .2s;border-radius:3px}
          .interactive-word:hover{background:#e3f2fd}
          .interactive-word.in-vocab{background:rgba(255,255,0,0.25)}
          .interactive-word:not(.in-vocab){background:#d4edda}
          .interactive-word:not(.in-vocab):hover{background:#c3e6cb}
          .lp-tooltip{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:3px 6px;border-radius:4px;font-size:12px;white-space:nowrap;opacity:0;pointer-events:none;transition:opacity .12s;z-index:999999}
          .interactive-word:hover .lp-tooltip{opacity:1}`
          document.documentElement.appendChild(style)
        }
        for (const { node, frag } of replacements) node.parentNode.replaceChild(frag, node)
        bindWordClicks()
        bindWordHoverTranslate()
      }
      sendResponse({ ok:true })
    }
  })

  // No-op; background now pushes analyze-result directly to this tab
})()

