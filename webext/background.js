const API_BASE = 'https://lexipark.onrender.com'

async function getToken() {
  const { access } = await chrome.storage.local.get(['access'])
  return access || null
}
async function getRefresh() {
  const { refresh } = await chrome.storage.local.get(['refresh'])
  return refresh || null
}

async function apiFetch(path, opts={}) {
  let token = await getToken()
  const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {})
  if (token) headers.Authorization = `Bearer ${token}`
  let res = await fetch(`${API_BASE}${path}`, { ...opts, headers })
  if (res.status === 401) {
    const refresh = await getRefresh()
    if (refresh) {
      const r = await fetch(`${API_BASE}/api/v1/token/refresh/`, { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ refresh }) })
      const data = await r.json().catch(()=>null)
      if (data && data.access) {
        await chrome.storage.local.set({ access: data.access })
        token = data.access
        const headers2 = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {})
        headers2.Authorization = `Bearer ${token}`
        res = await fetch(`${API_BASE}${path}`, { ...opts, headers: headers2 })
      }
    }
  }
  return res
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  ;(async () => {
    if (msg.type === 'analyze') {
      const text = (msg.text || '').trim()
      if (!text) return sendResponse({ ok:false, error:'Empty selection' })
      try {
        const res = await apiFetch('/analysis/api/v1/analyze/', { method: 'POST', body: JSON.stringify({ text }) })
        const data = await res.json()
        // deliver to content script on the same tab
        if (sender.tab && sender.tab.id) {
          chrome.tabs.sendMessage(sender.tab.id, { type:'analyze-result', data })
        }
        if (msg.tabId) {
          chrome.tabs.sendMessage(msg.tabId, { type:'analyze-result', data })
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
        const res = await apiFetch('/analysis/api/v1/analyze-html/', { method: 'POST', body: JSON.stringify({ text }) })
        const data = await res.json()
        if (msg.tabId) {
          chrome.tabs.sendMessage(msg.tabId, { type:'analyze-html-result', data })
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
        const res = await apiFetch('/analysis/api/v1/analyze/', { method: 'POST', body: JSON.stringify({ text }) })
        const data = await res.json()
        if (msg.tabId) chrome.tabs.sendMessage(msg.tabId, { type:'annotate-inplace', data })
        sendResponse({ ok:true })
      } catch (e) {
        sendResponse({ ok:false, error:String(e) })
      }
    }
    if (msg.type === 'translate-word') {
      const word = (msg.word || '').trim()
      if (!word) return sendResponse({ ok:false, error:'Empty word' })
      try {
        const res = await apiFetch('/analysis/translate-word/', { method: 'POST', body: JSON.stringify({ word }) })
        const data = await res.json()
        sendResponse({ ok:true, data })
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
        let res = await apiFetch('/users/api/v1/save-vocabulary/', { method:'POST', body: JSON.stringify({
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
          res = await fetch(`${API_BASE}/users/save-vocabulary/`, { method:'POST', body: form, credentials:'include' })
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

