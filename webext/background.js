const API_BASE = 'https://lexipark.onrender.com'

async function getToken() {
  const { access } = await chrome.storage.local.get(['access'])
  return access || null
}
async function getRefresh() {
  const { refresh } = await chrome.storage.local.get(['refresh'])
  return refresh || null
}
async function getApiBase() {
  const { api_base } = await chrome.storage.local.get(['api_base'])
  return api_base || API_BASE
}
async function ensureDefaultApiBase() {
  const { api_base } = await chrome.storage.local.get(['api_base'])
  if (!api_base) await chrome.storage.local.set({ api_base: API_BASE })
}
chrome.runtime.onInstalled.addListener(() => { void ensureDefaultApiBase() })
chrome.runtime.onStartup?.addListener?.(() => { void ensureDefaultApiBase() })

async function apiFetchAt(base, path, opts={}) {
  let token = await getToken()
  const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {})
  if (token) headers.Authorization = `Bearer ${token}`
  const withCreds = (String(path || '').startsWith('/analysis/api/')) ? { credentials: 'include' } : {}
  let res = await fetch(`${base}${path}`, { ...opts, headers, ...withCreds })
  if (res.status === 401) {
    const refresh = await getRefresh()
    if (refresh) {
      const r = await fetch(`${base}/api/v1/token/refresh/`, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ refresh }) })
      const data = await r.json().catch(()=>null)
      if (data && data.access) {
        await chrome.storage.local.set({ access: data.access })
        token = data.access
        const headers2 = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {})
        headers2.Authorization = `Bearer ${token}`
        res = await fetch(`${base}${path}`, { ...opts, headers: headers2, ...withCreds })
      }
    }
  }
  return res
}

async function apiFetch(path, opts={}) {
  const base = await getApiBase()
  return apiFetchAt(base, path, opts)
}

async function apiFetchWithFallback(paths, opts={}) {
  const baseCandidates = [await getApiBase(), 'http://127.0.0.1:8082', 'http://localhost:8082', 'https://lexipark.onrender.com']
  for (const base of baseCandidates) {
    for (const p of paths) {
      const res = await apiFetchAt(base, p, opts)
      if (res.status !== 404) return res
    }
  }
  return apiFetch(paths[paths.length-1] || '/', opts)
}

function safeSendMessage(tabId, msg) {
  try {
    if (!tabId) return
    chrome.tabs.sendMessage(tabId, msg, () => { void chrome.runtime.lastError })
  } catch(_) { }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  ;(async () => {
    if (msg.type === 'analyze') {
      const text = (msg.text || '').trim()
      if (!text) return sendResponse({ ok:false, error:'Empty selection' })
      try {
        const res = await apiFetchWithFallback(['/analysis/api/analyze', '/analysis/api/v1/analyze/'], { method: 'POST', body: JSON.stringify({ text }) })
        const data = await res.json().catch(()=>({}))
        const targetId = msg.tabId || (sender && sender.tab && sender.tab.id)
        if (data && data.html) {
          safeSendMessage(targetId, { type:'analyze-html-result', data })
        } else if (data && (Array.isArray(data.words) || typeof data.words !== 'undefined')) {
          safeSendMessage(targetId, { type:'analyze-result', data })
        } else {
          safeSendMessage(targetId, { type:'annotate-inplace-html', data })
        }
        sendResponse({ ok:true })
      } catch (e) {
        sendResponse({ ok:false, error:String(e) })
      }
    }
    if (msg.type === 'analyze-html') {
      const text = (msg.text || '').trim()
      if (!text) return sendResponse({ ok:false, error:'Empty page' })
      try {
        const res = await apiFetchWithFallback(['/analysis/api/analyze', '/analysis/api/v1/analyze-html/', '/analysis/api/v1/analyze/'], { method: 'POST', body: JSON.stringify({ text }) })
        const data = await res.json().catch(()=>({}))
        const targetId = msg.tabId || (sender && sender.tab && sender.tab.id)
        if (data && data.html) {
          safeSendMessage(targetId, { type:'analyze-html-result', data })
        } else if (data && (Array.isArray(data.words) || typeof data.words !== 'undefined')) {
          safeSendMessage(targetId, { type:'analyze-result', data })
        } else {
          safeSendMessage(targetId, { type:'annotate-inplace-html', data })
        }
        sendResponse({ ok:true })
      } catch (e) {
        sendResponse({ ok:false, error:String(e) })
      }
    }
    if (msg.type === 'annotate-inplace') {
      const text = (msg.text || '').trim()
      if (!text) return sendResponse({ ok:false, error:'Empty page' })
      try {
        const res = await apiFetchWithFallback(['/analysis/api/analyze', '/analysis/api/v1/analyze/'], { method: 'POST', body: JSON.stringify({ text }) })
        const data = await res.json()
        const targetId = msg.tabId || (sender && sender.tab && sender.tab.id)
        safeSendMessage(targetId, { type:'annotate-inplace-html', data })
        sendResponse({ ok:true })
      } catch (e) {
        sendResponse({ ok:false, error:String(e) })
      }
    }
    if (msg.type === 'translate-word') {
      const word = (msg.word || '').trim()
      if (!word) return sendResponse({ ok:false, error:'Empty word' })
      try {
        const res = await apiFetchWithFallback(['/analysis/api/translate-word', '/analysis/translate-word/'], { method: 'POST', body: JSON.stringify({ word }) })
        const data = await res.json()
        sendResponse({ ok:true, data })
      } catch (e) {
        sendResponse({ ok:false, error:String(e) })
      }
    }
    if (msg.type === 'batch-recall') {
      try {
        const interactions = Array.isArray(msg.interactions) ? msg.interactions : []
        const res = await apiFetchWithFallback(['/analysis/api/batch-recall', '/analysis/api/v1/batch-recall/'], { method: 'POST', body: JSON.stringify({ interactions }) })
        const data = await res.json().catch(()=>({}))
        sendResponse({ ok: res.ok, data })
      } catch (e) {
        sendResponse({ ok:false, error:String(e) })
      }
    }
  })()
  return true
})

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  ;(async () => {
    if (msg.type === 'track-hover') {
      try {
        const res = await apiFetchWithFallback(['/analysis/track-hover/'], { method: 'POST', body: JSON.stringify({ korean_word: msg.word || '', duration: msg.duration || 0 }) })
        const data = await res.json().catch(()=>({}))
        sendResponse({ ok: res.ok, data })
      } catch (e) {
        sendResponse({ ok:false, error:String(e) })
      }
    }
  })()
  return true
})

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  ;(async () => {
    if (msg.type === 'save-vocab') {
      try {
        let base = await getApiBase()
        let res = await apiFetchAt(base, '/users/api/v1/save-vocabulary/', { method:'POST', body: JSON.stringify({
          korean_word: msg.korean_word || '',
          pos: msg.pos || '',
          grammar_info: msg.grammar_info || '',
          translation: msg.translation || ''
        }) })
        if (res.status === 401 || res.status === 403) {
          const form = new FormData()
          form.append('korean_word', msg.korean_word || '')
          form.append('pos', msg.pos || '')
          form.append('grammar_info', msg.grammar_info || '')
          form.append('translation', msg.translation || '')
          res = await fetch(`${base}/users/save-vocabulary/`, { method:'POST', body: form, credentials:'include' })
        }
        const data = await res.json().catch(()=>({}))
        sendResponse({ ok: res.ok, data })
      } catch (e) {
        sendResponse({ ok:false, error:String(e) })
      }
    }
  })()
  return true
})

