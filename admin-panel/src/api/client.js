const TOKEN_KEY = "va_token"
const TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 30 // 30 days

function readCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

let memoryToken = readCookie(TOKEN_KEY)

export function setToken(token) {
  memoryToken = token
  document.cookie = `${TOKEN_KEY}=${encodeURIComponent(token)}; path=/; max-age=${TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`
}

export function getToken() {
  return memoryToken
}

export function clearToken() {
  memoryToken = null
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0; SameSite=Lax`
}

export async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (memoryToken) headers["Authorization"] = `Bearer ${memoryToken}`
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json"
    options.body = JSON.stringify(options.body)
  }
  const response = await fetch(path, { ...options, headers })
  if (response.status === 401) {
    clearToken()
    window.location.href = "/login"
    throw new Error("Session expired")
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || "Request failed")
  }
  const contentType = response.headers.get("content-type") || ""
  if (contentType.includes("application/json")) return response.json()
  return response
}
