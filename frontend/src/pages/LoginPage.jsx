import { apiFetch } from "../api";
import { useState, useEffect } from "react";
import { API } from "../config";
import { theme } from "../theme";
import logo from "../assets/zayer-logo.png";

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    if (sessionStorage.getItem("barbechai_session_expired")) {
      setSessionExpired(true);
      sessionStorage.removeItem("barbechai_session_expired");
    }
  }, []);

  const handleLogin = async () => {
    if (!email || !password) {
      setError("Email et mot de passe requis");
      return;
    }
    setLoading(true);
    setError(null);
    setSessionExpired(false);
    try {
      const res = await fetch(
        `${API}/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
        { method: "POST" }
      );
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      localStorage.setItem("barbechai_token", data.token);
      localStorage.setItem("barbechai_user", JSON.stringify(data.user));
      onLogin(data.user, data.token);
    } catch (e) {
      setError(e.message === "Invalid credentials" ? "Email ou mot de passe incorrect" : e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") handleLogin();
  };

  return (
    <div style={{
      minHeight: "100vh", background: theme.bg, color: theme.text,
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: "'Inter', sans-serif", padding: 20,
    }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');`}</style>

      <div style={{ width: "100%", maxWidth: 380 }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <img src={logo} alt="ZAYER Digital" style={{ height: 64, width: "auto", margin: "0 auto 16px" }} />
          <div style={{ fontSize: 22, fontWeight: 800, color: theme.navy }}>BarbechAi</div>
          <div style={{ fontFamily: "monospace", fontSize: 10, color: theme.gold, letterSpacing: 2, marginTop: 4 }}>
            BY ZAYER DIGITAL
          </div>
        </div>

        <div style={{ background: theme.card, border: `1px solid ${theme.border}`, borderRadius: 10, padding: 28, boxShadow: "0 1px 3px rgba(18,24,48,0.06)" }}>
          <div style={{ fontFamily: "monospace", fontSize: 10, color: theme.navy, letterSpacing: 2, marginBottom: 20, textAlign: "center" }}>
            CONNEXION
          </div>

          {sessionExpired && !error && (
            <div style={{ background: theme.goldSoft, border: `1px solid ${theme.gold}55`, borderRadius: 6, padding: "10px 14px", fontFamily: "monospace", fontSize: 12, color: theme.goldText, marginBottom: 16 }}>
              ⏱ Session expirée — veuillez vous reconnecter.
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: theme.textMuted, letterSpacing: 1, marginBottom: 6 }}>EMAIL</div>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="votre@email.com"
              style={{ width: "100%", background: theme.bg, border: `1px solid ${theme.borderStrong}`, borderRadius: 6, color: theme.text, padding: "11px 14px", fontSize: 14, fontFamily: "Inter, sans-serif" }}
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: theme.textMuted, letterSpacing: 1, marginBottom: 6 }}>MOT DE PASSE</div>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="••••••••"
              style={{ width: "100%", background: theme.bg, border: `1px solid ${theme.borderStrong}`, borderRadius: 6, color: theme.text, padding: "11px 14px", fontSize: 14, fontFamily: "Inter, sans-serif" }}
            />
          </div>

          {error && (
            <div style={{ background: theme.dangerSoft, border: `1px solid ${theme.danger}33`, borderRadius: 6, padding: "10px 14px", fontFamily: "monospace", fontSize: 12, color: theme.danger, marginBottom: 16 }}>
              ⚠ {error}
            </div>
          )}

          <button onClick={handleLogin} disabled={loading} style={{
            width: "100%", background: loading ? theme.divider : theme.navy,
            color: loading ? theme.textMuted : "#fff", border: "none", borderRadius: 6,
            padding: "13px", fontSize: 14, fontWeight: 700,
            cursor: loading ? "not-allowed" : "pointer",
          }}>
            {loading ? "Connexion..." : "Se connecter →"}
          </button>
        </div>

        <div style={{ textAlign: "center", marginTop: 20, fontFamily: "monospace", fontSize: 10, color: theme.textFaint }}>
          Accès réservé à l'équipe BarbechAi
        </div>
      </div>
    </div>
  );
}
