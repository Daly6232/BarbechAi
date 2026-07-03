import { apiFetch } from "../api";
import { useState } from "react";
import { API } from "../config";

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async () => {
    if (!email || !password) {
      setError("Email et mot de passe requis");
      return;
    }
    setLoading(true);
    setError(null);
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
      minHeight: "100vh", background: "#080808", color: "#f0f0f0",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: "'Inter', sans-serif", padding: 20,
    }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');`}</style>

      <div style={{ width: "100%", maxWidth: 380 }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, background: "#ff4d00", borderRadius: 12,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 28, fontWeight: 900, margin: "0 auto 16px",
          }}>B</div>
          <div style={{ fontSize: 22, fontWeight: 800 }}>BarbechAI</div>
          <div style={{ fontFamily: "monospace", fontSize: 10, color: "#444", letterSpacing: 2, marginTop: 4 }}>
            TUNISIA BUSINESS INTELLIGENCE
          </div>
        </div>

        <div style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 10, padding: 28 }}>
          <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00", letterSpacing: 2, marginBottom: 20, textAlign: "center" }}>
            CONNEXION
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 1, marginBottom: 6 }}>EMAIL</div>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="votre@email.com"
              style={{ width: "100%", background: "#080808", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f0f0f0", padding: "11px 14px", fontSize: 14, fontFamily: "Inter, sans-serif" }}
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 1, marginBottom: 6 }}>MOT DE PASSE</div>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="••••••••"
              style={{ width: "100%", background: "#080808", border: "1px solid #2a2a2a", borderRadius: 6, color: "#f0f0f0", padding: "11px 14px", fontSize: 14, fontFamily: "Inter, sans-serif" }}
            />
          </div>

          {error && (
            <div style={{ background: "#1a0a0a", border: "1px solid #ff4d0033", borderRadius: 6, padding: "10px 14px", fontFamily: "monospace", fontSize: 12, color: "#ff4d00", marginBottom: 16 }}>
              ⚠ {error}
            </div>
          )}

          <button onClick={handleLogin} disabled={loading} style={{
            width: "100%", background: loading ? "#1a1a1a" : "#ff4d00",
            color: loading ? "#444" : "#fff", border: "none", borderRadius: 6,
            padding: "13px", fontSize: 14, fontWeight: 700,
            cursor: loading ? "not-allowed" : "pointer",
          }}>
            {loading ? "Connexion..." : "Se connecter →"}
          </button>
        </div>

        <div style={{ textAlign: "center", marginTop: 20, fontFamily: "monospace", fontSize: 10, color: "#333" }}>
          Accès réservé à l'équipe BarbechAI
        </div>
      </div>
    </div>
  );
}
