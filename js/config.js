/**
 * Shared configuration constants.
 * Change API_BASE here to update all pages at once.
 */
const API_BASE = "http://47.113.104.70:80/api";
const AMAP_KEY = "0190baafdb829edc71b1c2b0cb9e3dd0";

/** Read the CSRF token from the cookie set by the backend. */
function getCSRFToken() {
  const match = document.cookie.match(/(^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[2]) : "";
}

/**
 * Wrapper around fetch that automatically adds credentials and the CSRF header
 * for mutating requests (POST, PUT, DELETE, PATCH).
 */
function apiFetch(url, options = {}) {
  const opts = { credentials: "include", ...options };
  opts.headers = { ...(opts.headers || {}) };
  const method = (opts.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD" && method !== "OPTIONS") {
    opts.headers["X-CSRF-Token"] = getCSRFToken();
  }
  return fetch(url, opts);
}
