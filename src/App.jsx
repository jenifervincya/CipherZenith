// App.jsx
import { useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import { AuthGuard, isAuthenticated } from "../security/auth_guard";
import { injectCspMetaTag } from "../security/csp_headers";

// DEV ONLY: set a dummy session token so the dashboard is viewable before
// the real backend login flow exists. Delete this block once Jenifer's
// auth endpoint is ready and wire up a real login screen instead.
if (import.meta.env.DEV && !isAuthenticated()) {
  sessionStorage.setItem("cipherzenith_dashboard_token", "dev-only-placeholder-token-000");
}

export default function App() {
  useEffect(() => {
    injectCspMetaTag();
  }, []);

  return (
    <AuthGuard fallback={<LoginPrompt />}>
      <Dashboard />
    </AuthGuard>
  );
}

function LoginPrompt() {
  return (
    <div className="min-h-screen bg-[#05070a] flex items-center justify-center">
      <div className="text-center space-y-2">
        <p className="text-white/70 text-sm">Dashboard access requires authentication.</p>
        <p className="text-white/30 text-xs font-mono">
          {isAuthenticated() ? "" : "No valid session token found."}
        </p>
      </div>
    </div>
  );
}