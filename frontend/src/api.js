// This backend reports auth failures as HTTP 200 with a JSON {"error": "..."}
// body — it never sends a real 401. Every page that just did
// `.then(d => setX(d.something || []))` was silently swallowing that and
// rendering an empty/broken screen with no indication that the token had
// expired. This wrapper centralizes the check in one place instead of
// requiring every call site to remember to inspect `data.error`.

const AUTH_ERROR_MESSAGES = new Set(["No token provided", "Invalid or expired token"]);

let onAuthExpired = null;

export function setAuthExpiredHandler(fn) {
  onAuthExpired = fn;
}

export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem("barbechai_token");
  const headers = {
    ...(options.headers || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  if (token) {
    // Peek at the body via a clone so the caller can still read the
    // original response normally afterward.
    try {
      const data = await res.clone().json();
      if (data && typeof data.error === "string" && AUTH_ERROR_MESSAGES.has(data.error)) {
        localStorage.removeItem("barbechai_token");
        localStorage.removeItem("barbechai_user");
        sessionStorage.setItem("barbechai_session_expired", "1");
        if (onAuthExpired) onAuthExpired();
      }
    } catch {
      // Not JSON (e.g. a binary export download) — nothing to check.
    }
  }

  return res;
}
