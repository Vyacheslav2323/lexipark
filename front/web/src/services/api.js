// services/api.js
import { getToken } from "./auth";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function buildHeaders({ auth = true, json = true, headers = {} } = {}) {
  const token = getToken();

  const h = { ...headers };

  if (json) {
    if (!h.Accept) h.Accept = "application/json";
    if (!h["Content-Type"]) h["Content-Type"] = "application/json";
  }

  if (auth) {
    if (!token) throw new Error("401 Missing access_token");
    h.Authorization = `Bearer ${token}`;
  }

  return h;
}

async function parseError(res) {
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    const j = await res.json().catch(() => null);
    return j?.detail || j?.message || JSON.stringify(j) || "";
  }
  return await res.text().catch(() => "");
}

export async function apiRequest(path, { method = "GET", auth = true, json = true, body, headers } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: buildHeaders({ auth, json, headers }),
    ...(body !== undefined ? { body: json ? JSON.stringify(body) : body } : {}),
  });

  if (!res.ok) {
    const msg = await parseError(res);
    throw new Error(`${res.status} ${msg}`);
  }

  if (res.status === 204) return null;

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

export const apiGet = (path, opts) => apiRequest(path, { ...opts, method: "GET" });
export const apiPost = (path, body, opts) => apiRequest(path, { ...opts, method: "POST", body });
export const apiPut = (path, body, opts) => apiRequest(path, { ...opts, method: "PUT", body });
export const apiDelete = (path, opts) => apiRequest(path, { ...opts, method: "DELETE" });
