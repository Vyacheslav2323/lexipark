(function(){
  let panel = null
  let clickBound = false
  const DEBUG = true
  function log(...args){ if (DEBUG) try{ console.log('[LexiExt]', ...args) }catch(_){} }
  function warn(...args){ if (DEBUG) try{ console.warn('[LexiExt]', ...args) }catch(_){} }
  function isEditable(el){
    const tag = (el && el.tagName || '').toLowerCase()
    return tag==='input'||tag==='textarea'||(el && el.isContentEditable)
  }
  const POS_MAP = {
    NNG:'General Noun', NNP:'Proper Noun', NNB:'Bound Noun', NP:'Pronoun', NR:'Numeral',
    VV:'Verb', VA:'Adjective', VX:'Auxiliary Verb', VCP:'Copula', VCN:'Negative Copula',
    MM:'Determiner', MAG:'General Adverb', MAJ:'Conjunctive Adverb', IC:'Interjection',
    JKS:'Subject Particle', JKC:'Complement Particle', JKG:'Genitive Particle', JKO:'Object Particle', JKB:'Adverbial Particle', JKV:'Vocative Particle', JKQ:'Quotative Particle', JX:'Auxiliary Particle', JC:'Conjunctive Particle',
    EP:'Pre-final Ending', EF:'Final Ending', EC:'Conjunctive Ending', ETN:'Nominal Ending', ETM:'Adnominal Ending',
    XPN:'Prefix', XSN:'Noun Suffix', XSV:'Verb Suffix', XSA:'Adjective Suffix', XR:'Root',
    SF:'Sentence-final Punctuation', SP:'Separator', SS:'Symbol', SE:'Ellipsis', SO:'Opening Bracket', SW:'Closing Bracket', SL:'Foreign Word', SH:'Chinese Character', SN:'Number'
  }
  function posDesc(pos){ if (!pos) return ''; for (const k of Object.keys(POS_MAP)) if (pos.indexOf(k) !== -1) return POS_MAP[k]; return pos }
  function isInteractivePos(pos){
    if (!pos) return false
    if (pos.indexOf('VV') !== -1 || pos.indexOf('VA') !== -1 || pos.indexOf('VX') !== -1) return true
    const allowed = new Set(['NNG', 'NNP', 'NP', 'NR', 'MAG', 'MAJ', 'MM', 'XR'])
    return allowed.has(pos)
  }
  function hasHangul(text){ return /[\uAC00-\uD7A3]/.test(text) }
  function extractPageText(){
    try{
      const sel = window.getSelection && window.getSelection().toString()
      if (sel && sel.trim()) return sel
    }catch(_){ }
    try{
      return document.body && document.body.innerText ? document.body.innerText : document.documentElement.innerText
    }catch(_){ return '' }
  }
  function ensurePanel(){
    if (panel) return panel
    const host = document.createElement('div')
    const shadow = host.attachShadow({ mode:'open' })
    const style = document.createElement('style')
    style.textContent = `.interactive-word{cursor:pointer;position:relative;transition:background-color .2s;border-radius:3px}
    .interactive-word:hover{background:#e3f2fd}`
    const wrap = document.createElement('div')
    wrap.style.cssText = 'position:fixed;bottom:16px;right:16px;width:600px;max-width:80vw;max-height:60vh;overflow:auto;background:#fff;border:1px solid #e5e7eb;box-shadow:0 4px 16px rgba(0,0,0,.2);border-radius:10px;padding:12px;font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif;z-index:999999'
    shadow.appendChild(style)
    shadow.appendChild(wrap)
    document.documentElement.appendChild(host)
    panel = { host, wrap }
    return panel
  }

  function annotateInlineFromWords(words){
    try{
      const { trans, cand } = buildMaps(words || [])
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
      while (true) {
        const node = walker.nextNode()
        if (!node) break
        const text = node.nodeValue
        let lastIndex = 0
        let m2
        let changed = false
        const frag = document.createDocumentFragment()
        const re = /[\uAC00-\uD7A3]+/g
        while ((m2 = re.exec(text)) !== null) {
          const start = m2.index
          const end = start + m2[0].length
          if (start > lastIndex) frag.appendChild(document.createTextNode(text.slice(lastIndex, start)))
          const run = m2[0]
          const sub = splitHangulRun(run, cand, trans)
          if (sub.childNodes.length && Array.from(sub.childNodes).some(n => n.nodeType===1)) changed = true
          frag.appendChild(sub)
          lastIndex = end
        }
        if (lastIndex < text.length) frag.appendChild(document.createTextNode(text.slice(lastIndex)))
        if (changed) replacements.push({ node, frag })
      }
      const styleId = 'lexipark-inline-style'
      if (replacements.length && !document.getElementById(styleId)) {
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
      bindWordClicks(); bindWordHoverTranslate()
      log('inline annotate from words: applied overlays', replacements.length)
    }catch(e){ warn('inline annotate from words error', e) }
  }

  function showDemoPanel(){
    const { wrap } = ensurePanel()
    wrap.innerHTML = ''
    const title = document.createElement('div')
    title.textContent = 'LexiPark — No Korean detected'
    title.style.cssText = 'font-weight:600;margin-bottom:8px'
    const msg = document.createElement('div')
    msg.textContent = 'Run a quick demo to see how it works.'
    const btn = document.createElement('button')
    btn.textContent = 'Run demo'
    btn.style.cssText = 'margin-top:8px;padding:6px 10px;border:1px solid #e5e7eb;border-radius:6px;background:#2563eb;color:#fff;cursor:pointer'
    wrap.appendChild(title)
    wrap.appendChild(msg)
    wrap.appendChild(btn)
    btn.addEventListener('click', () => {
      const demo = '안녕하세요 저는 한국어를 공부합니다'
      chrome.runtime.sendMessage({ type:'analyze-html', text: demo })
    })
  }

  function isEligiblePos(pos){
    if (!pos) return false
    if (pos.indexOf('VV') !== -1 || pos.indexOf('VA') !== -1 || pos.indexOf('VX') !== -1) return true
    const allowed = new Set(['NNG', 'NNP', 'NP', 'NR', 'MAG', 'MAJ', 'MM', 'XR'])
    return allowed.has(pos)
  }

  function buildMaps(words){
    const trans = new Map()
    const cand = new Map()
    for (const w of words) {
      if (!isInteractivePos(w.pos || '')) continue
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
    log('buildMaps:', { tokens: words.length, transSize: trans.size, candBuckets: (cand.size||0) })
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
        const meta = trans.get(match)
        const tipText = (meta && meta.translation ? meta.translation : (meta && meta.base ? meta.base : match))
        const a = document.createElement('a')
        a.href = 'https://papago.naver.com/?sk=ko&tk=en&hn=0&st=' + encodeURIComponent(meta && meta.base ? meta.base : match)
        a.target = '_blank'
        a.rel = 'noopener noreferrer'
        a.style.color = '#fff'
        a.style.textDecoration = 'none'
        a.textContent = tipText
        tip.appendChild(a)
        if (meta && typeof meta === 'object') {
          if (meta.in_vocab) span.classList.add('in-vocab')
          if (meta.color && String(meta.color).toLowerCase() !== 'transparent') {
            span.style.backgroundColor = meta.color
          }
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

  function showToast(message){
    try{
      const id = 'lexi-toast'; const old = document.getElementById(id); if (old) old.remove()
      const t = document.createElement('div'); t.id = id
      t.textContent = message
      t.style.cssText = 'position:fixed;top:16px;right:16px;background:#333;color:#fff;padding:10px 14px;border-radius:8px;font-size:13px;z-index:999999;box-shadow:0 2px 8px rgba(0,0,0,.2)'
      document.documentElement.appendChild(t)
      setTimeout(()=>{ try{ t.remove() }catch(_){} }, 2000)
    }catch(_){}
  }

  function markAllOccurrencesAsKnown(base){
    try{
      const updateEl = (el) => {
        el.classList.add('in-vocab')
        el.style.backgroundColor = 'rgba(255,255,0,0.25)'
      }
      document.querySelectorAll('.interactive-word[data-original]').forEach(el => {
        if ((el.getAttribute('data-original')||'') === base) updateEl(el)
      })
      // also update any spans with matching text when data-original is missing
      document.querySelectorAll('.interactive-word:not([data-original])').forEach(el => {
        if ((el.textContent||'') === base) updateEl(el)
      })
      // update inside panel shadow DOM if present
      try{
        if (panel && panel.host && panel.host.shadowRoot) {
          panel.host.shadowRoot.querySelectorAll('.interactive-word[data-original]').forEach(el => {
            if ((el.getAttribute('data-original')||'') === base) updateEl(el)
          })
        }
      }catch(_){}
    }catch(_){}
  }

  function bindWordClicks(){
    if (clickBound) return
    const handler = (e) => {
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
          if (resp && resp.ok) {
            showToast(`"${p.korean_word}" added`)
            markAllOccurrencesAsKnown(p.korean_word)
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
    }
    document.addEventListener('click', handler)
    try{ if (panel && panel.host && panel.host.shadowRoot) panel.host.shadowRoot.addEventListener('click', handler) }catch(_){ }
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
      const data = msg.data || {}
      const words = data.words || []
      log('analyze-result words:', words.length)
      if (words && words.length) annotateInlineFromWords(words)
      sendResponse({ ok:true })
    }
    if (msg.type === 'analyze-html-result') {
      const data = msg.data || {}
      const html = data.html || ''
      log('analyze-html-result html length:', html.length)
      if (html) {
        const tmp = document.createElement('div')
        tmp.innerHTML = html
        const tokens = Array.from(tmp.querySelectorAll('.interactive-word')).map(el => {
          const styleAttr = el.getAttribute('style') || ''
          const m = styleAttr.match(/background-color:\s*([^;]+)/i)
          const bg = m ? (m[1] || '').trim().toLowerCase() : ''
          const isKnown = bg && bg !== 'transparent'
          return {
            surface: el.textContent || '',
            base: el.getAttribute('data-original') || '',
            translation: el.getAttribute('data-translation') || '',
            in_vocab: isKnown,
            color: bg,
            pos: el.getAttribute('data-pos') || '',
            grammar_info: el.getAttribute('data-grammar') || ''
          }
        })
        if (tokens.length) annotateInlineFromWords(tokens)
      }
      sendResponse({ ok:true })
    }
    if (msg.type === 'annotate-inplace-html') {
      const data = msg.data || {}
      const html = data.html || ''
      log('inline annotate: html length', html.length)
      if (!html) {
        if (data && Array.isArray(data.words) && data.words.length) {
          warn('inline annotate: empty html, falling back to words path')
          annotateInlineFromWords(data.words)
          return sendResponse({ ok:true })
        }
        warn('inline annotate: empty html'); return sendResponse({ ok:false })
      }
      const tmp = document.createElement('div')
      tmp.innerHTML = html
      const tokens = Array.from(tmp.querySelectorAll('.interactive-word')).map(el => {
        const styleAttr = el.getAttribute('style') || ''
        const m = styleAttr.match(/background-color:\s*([^;]+)/i)
        const bg = m ? (m[1] || '').trim().toLowerCase() : ''
        const isKnown = bg && bg !== 'transparent'
        return {
          surface: el.textContent || '',
          base: el.getAttribute('data-original') || '',
          translation: el.getAttribute('data-translation') || '',
          in_vocab: isKnown,
          color: bg,
          pos: el.getAttribute('data-pos') || '',
          grammar_info: el.getAttribute('data-grammar') || ''
        }
      })
      log('inline annotate: tokens', tokens.length, tokens.slice(0,5))
      const { trans, cand } = buildMaps(tokens)
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
      const startTs = Date.now()
      while (true) {
        const node = walker.nextNode()
        if (!node) break
        const text = node.nodeValue
        let lastIndex = 0
        let m2
        let changed = false
        const frag = document.createDocumentFragment()
        const re = /[\uAC00-\uD7A3]+/g
        while ((m2 = re.exec(text)) !== null) {
          const start = m2.index
          const end = start + m2[0].length
          if (start > lastIndex) frag.appendChild(document.createTextNode(text.slice(lastIndex, start)))
          const run = m2[0]
          const sub = splitHangulRun(run, cand, trans)
          if (sub.childNodes.length && Array.from(sub.childNodes).some(n => n.nodeType===1)) changed = true
          frag.appendChild(sub)
          lastIndex = end
        }
        if (lastIndex < text.length) frag.appendChild(document.createTextNode(text.slice(lastIndex)))
        if (changed) replacements.push({ node, frag })
      }
      log('inline annotate: replacements', replacements.length, 'timeMs', Date.now()-startTs)
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
          log('inline annotate: injected style')
        }
        for (const { node, frag } of replacements) node.parentNode.replaceChild(frag, node)
        bindWordClicks()
        bindWordHoverTranslate()
        log('inline annotate: applied overlays')
      } else {
        showDemoPanel()
        warn('inline annotate: no replacements found')
      }
      sendResponse({ ok:true })
    }
  })

  try{
    const text = extractPageText()
    if (text && hasHangul(text)) {
      chrome.runtime.sendMessage({ type:'analyze', text })
    }
  }catch(_){ }

})()

