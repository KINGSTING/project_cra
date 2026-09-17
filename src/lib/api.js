// src/lib/api.js
const TOKEN_KEY = "impcra_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * POST JSON to an API endpoint.
 * Automatically attaches Authorization header if a token is stored.
 * Throws an Error with `.status` and `.payload` if the server returns non-2xx.
 */
export async function apiPost(path, body = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  let payload = null;
  try {
    payload = await res.json();
  } catch {
    // ignore non-JSON responses
  }

  if (!res.ok) {
    const err = new Error(payload?.error || `HTTP ${res.status}`);
    err.status = res.status;
    err.payload = payload;
    throw err;
  }
  return payload;
}

export async function apiGet(path) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, { headers });
  let payload = null;
  try {
    payload = await res.json();
  } catch {
    // ignore
  }
  if (!res.ok) {
    const err = new Error(payload?.error || `HTTP ${res.status}`);
    err.status = res.status;
    err.payload = payload;
    throw err;
  }
  return payload;
}

// src/lib/api.js — APPEND these below the existing exports

export async function apiPatch(path, body = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, {
    method: "PATCH",
    headers,
    body: JSON.stringify(body),
  });
  let payload = null;
  try { payload = await res.json(); } catch {}
  if (!res.ok) {
    const err = new Error(payload?.error || `HTTP ${res.status}`);
    err.status = res.status;
    err.payload = payload;
    throw err;
  }
  return payload;
}

export async function apiDelete(path) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, { method: "DELETE", headers });
  let payload = null;
  try { payload = await res.json(); } catch {}
  if (!res.ok) {
    const err = new Error(payload?.error || `HTTP ${res.status}`);
    err.status = res.status;
    err.payload = payload;
    throw err;
  }
  return payload;
}