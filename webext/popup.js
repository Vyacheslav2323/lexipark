const API_BASE = 'https://lexipark.onrender.com'

async function checkSessionAuth() {
  const r = await fetch(`${API_BASE}/users/api/v1/me-session/`, { credentials: 'include' })
  const d = await r.json().catch(()=>({}))
  if (d && d.success) return d.username || ''
  throw new Error('Not authenticated')
}

document.getElementById('login').addEventListener('click', async () => {
  const status = document.getElementById('status')
  status.textContent = 'Logging in...'
  const usernameInput = document.getElementById('username').value.trim()
  const passwordInput = document.getElementById('password').value
  const endpoints = ['/users/api/v1/login/', '/api/v1/token/', '/api/token/']
  let lastErr = 'Login failed'
  try{
    let tokens = null
    for (const ep of endpoints) {
      try{
        const res = await fetch(`${API_BASE}${ep}`, { method:'POST', headers:{ 'Content-Type':'application/json', 'Accept':'application/json' }, body: JSON.stringify({ username: usernameInput, password: passwordInput }) })
        const data = await res.json().catch(()=>({}))
        if (res.ok && data && data.access) { tokens = { access: data.access, refresh: data.refresh }; break }
        lastErr = (data && (data.detail||data.error)) || `HTTP ${res.status}`
      }catch(err){ lastErr = String(err) }
    }
    if (!tokens) throw new Error(lastErr)
    await chrome.storage.local.set(tokens)
    let username = ''
    try{
      const r = await fetch(`${API_BASE}/users/api/v1/me/`, { headers:{ 'Authorization': `Bearer ${tokens.access}` } })
      const d = await r.json().catch(()=>({}))
      if (d && d.success) username = d.username || ''
    }catch(_){ }
    status.textContent = 'Logged in'
    const auth = document.getElementById('auth')
    const greeting = document.getElementById('greeting')
    const uname = document.getElementById('uname')
    const annotate = document.getElementById('annotate-inplace')
    if (auth) auth.style.display = 'none'
    if (greeting) greeting.style.display = ''
    if (uname) uname.textContent = username
    if (annotate) annotate.style.display = ''
  }catch(e){
    status.textContent = String(e || 'Login failed')
  }
})

// Removed analyze-selection and analyze-page buttons

document.getElementById('annotate-inplace').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  const [{ result: text }] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.body && document.body.innerText ? document.body.innerText : document.documentElement.innerText
  })
  if (!text || !text.trim()) return
  chrome.runtime.sendMessage({ type: 'annotate-inplace', text, tabId: tab.id })
})

;(async function initPopup(){
  const { access } = await chrome.storage.local.get(['access'])
  let authed = !!access
  const auth = document.getElementById('auth')
  const greeting = document.getElementById('greeting')
  const uname = document.getElementById('uname')
  const annotate = document.getElementById('annotate-inplace')
  if (authed) {
    try{
      const r = await fetch(`${API_BASE}/users/api/v1/me/`, { headers: { 'Authorization': `Bearer ${access}` } })
      const d = await r.json().catch(()=>({}))
      if (d && d.success) {
        if (auth) auth.style.display = 'none'
        if (greeting) greeting.style.display = ''
        if (uname) uname.textContent = d.username || ''
        if (annotate) annotate.style.display = ''
      } else {
        authed = false
      }
    }catch(_){ }
  }
  if (!authed) {
    try {
      const username = await checkSessionAuth()
        if (auth) auth.style.display = 'none'
        if (greeting) greeting.style.display = ''
        if (uname) uname.textContent = username || ''
        if (annotate) annotate.style.display = ''
    } catch(_) {
      
    }
  }
  const reg = document.getElementById('register')
  if (reg) reg.addEventListener('click', () => {
    chrome.tabs.create({ url: 'https://lexipark.onrender.com/users/register/' })
  })
  const myVocab = document.getElementById('my-vocab')
  if (myVocab) myVocab.addEventListener('click', () => {
    chrome.tabs.create({ url: 'https://lexipark.onrender.com/users/profile/' })
  })
  const logoutBtn = document.getElementById('logout')
  if (logoutBtn) logoutBtn.addEventListener('click', async () => {
    await chrome.storage.local.remove(['access','refresh'])
    if (auth) auth.style.display = ''
    if (greeting) greeting.style.display = 'none'
    if (uname) uname.textContent = ''
    
  })
})()

