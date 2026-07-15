// csp_headers.js
// Content Security Policy + basic hardening for the Control Center.
//
// If served via a static host / CDN (Vercel, Netlify, nginx), prefer
// setting these as real HTTP response headers rather than a <meta> tag —
// meta tags can't set X-Frame-Options or Strict-Transport-Security.
// This file provides both: a header config for server/edge config,
// and a meta-tag fallback for local dev / static hosting without header control.

export const CSP_DIRECTIVES = {
  "default-src": ["'self'"],
  "script-src": ["'self'"],
  "style-src": ["'self'", "'unsafe-inline'"], // Tailwind injects inline styles in dev
  "img-src": ["'self'", "data:"],
  "connect-src": ["'self'", "ws://localhost:8000", "wss://*"], // dashboard + app WebSocket channels
  "font-src": ["'self'"],
  "object-src": ["'none'"],
  "base-uri": ["'self'"],
  "form-action": ["'self'"],
  "frame-ancestors": ["'none'"], // prevents the dashboard from being iframed (clickjacking)
};

export function buildCspString(directives = CSP_DIRECTIVES) {
  return Object.entries(directives)
    .map(([key, values]) => `${key} ${values.join(" ")}`)
    .join("; ");
}

/** Recommended response headers — apply at the server/edge layer. */
export const SECURITY_HEADERS = {
  "Content-Security-Policy": buildCspString(),
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
  "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
};

/**
 * Injects the CSP as a <meta> tag for environments where you can't set
 * real HTTP headers (e.g. plain static hosting). Call once at app startup.
 * Note: frame-ancestors and some directives are ignored in meta tags —
 * this is a fallback, not a replacement for server headers.
 */
export function injectCspMetaTag() {
  if (document.querySelector('meta[http-equiv="Content-Security-Policy"]')) return;
  const meta = document.createElement("meta");
  meta.httpEquiv = "Content-Security-Policy";
  meta.content = buildCspString();
  document.head.appendChild(meta);
}

/**
 * Basic client-side input sanitization for anything rendered from
 * transaction/user data (sender name, receiver name, etc). This is a
 * defense-in-depth layer — the backend must also validate/escape.
 */
export function sanitizeDisplayText(input) {
  if (typeof input !== "string") return "";
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
    .slice(0, 200); // hard length cap against payload stuffing
}

/**
 * Validates transaction-related form input before it's sent to the backend.
 * Mirrors the trust boundary described in the project rules: never assume
 * the app or backend already validated it.
 */
export function validateTransactionInput({ sender, receiver, amount }) {
  const errors = [];
  const NAME_RE = /^[a-zA-Z\s]{1,50}$/;

  if (!NAME_RE.test(sender || "")) errors.push("Invalid sender name");
  if (!NAME_RE.test(receiver || "")) errors.push("Invalid receiver name");

  const amountNum = Number(amount);
  if (!Number.isFinite(amountNum) || amountNum <= 0 || amountNum > 1_000_000) {
    errors.push("Invalid amount");
  }

  return { valid: errors.length === 0, errors };
}