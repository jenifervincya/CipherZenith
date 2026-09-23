// auth_guard.js
// Protects the Control Center dashboard from unauthenticated access.
// This is a demo-grade guard: it checks for a session token issued by
// the backend at login and gates the dashboard route + WebSocket connect.
//
// Swap TOKEN_STORAGE_KEY / validateToken() for real backend-issued JWTs
// in production; for the hackathon demo this simulates the check.

const TOKEN_STORAGE_KEY = "cipherzenith_dashboard_token";

/**
 * Returns true if the current session has a plausible auth token.
 * Does NOT trust the token's contents on the frontend — real
 * verification always happens server-side. This only prevents casual
 * unauthenticated access to the dashboard UI.
 */
export function isAuthenticated() {
  const token = sessionStorage.getItem(TOKEN_STORAGE_KEY);
  return typeof token === "string" && token.length > 20;
}

export function setAuthToken(token) {
  if (typeof token !== "string" || token.length < 20) {
    throw new Error("Refusing to store a malformed auth token");
  }
  sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearAuthToken() {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY);
}

/**
 * React route guard. Wrap the Dashboard route with this component.
 *
 * Usage:
 *   <AuthGuard><Dashboard /></AuthGuard>
 */
export function AuthGuard({ children, fallback }) {
  if (!isAuthenticated()) {
    return fallback ?? null;
  }
  return children;
}

/**
 * Call before opening the dashboard WebSocket. Backend should also
 * independently verify the token server-side on connect — never rely
 * on the frontend gate alone.
 */
export function assertCanConnectDashboard() {
  if (!isAuthenticated()) {
    throw new Error("Blocked dashboard WebSocket connect: no valid session token");
  }
}