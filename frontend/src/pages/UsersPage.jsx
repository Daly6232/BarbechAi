import { apiFetch } from "../api";
import { useState } from "react";
import { API } from "../config";

const ROLE_OPTIONS = [
  { value: "field_agent", label: "Agent Terrain" },
  { value: "back_office", label: "Back Office" },
  { value: "admin", label: "Admin" },
];

export default function UsersPage({ user }) {
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "field_agent" });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null); // { ok: bool, message: string }

  const isMasterAdmin = user?.role === "master_admin";
  const availableRoles = isMasterAdmin ? ROLE_OPTIONS : ROLE_OPTIONS.filter(r => r.value !== "admin");

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.password) {
      setResult({ ok: false, message: "Tous les champs sont requis." });
      return;
    }
    if (form.password.length < 8) {
      setResult({ ok: false, message: "Le mot de passe doit contenir au moins 8 caractères." });
      return;
    }
    setSubmitting(true);
    setResult(null);
    try {
      // /auth/register reads these as query params server-side, not a JSON body
      const params = new URLSearchParams({
        email: form.email,
        password: form.password,
        name: form.name,
        role: form.role,
      });
      const res = await apiFetch(`${API}/auth/register?${params.toString()}`, { method: "POST" });
      const data = await res.json();
      if (data.error) {
        setResult({ ok: false, message: data.error });
      } else {
        setResult({ ok: true, message: `Compte créé pour ${form.name} (${form.role}).` });
        setForm({ name: "", email: "", password: "", role: "field_agent" });
      }
    } catch (e) {
      setResult({ ok: false, message: "Échec de la connexion au serveur." });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: "32px 16px" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00", letterSpacing: 3, marginBottom: 8 }}>ADMINISTRATION</div>
        <h1 style={{ fontSize: 24, fontWeight: 800 }}>Créer un compte</h1>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555", marginTop: 4 }}>
          {isMasterAdmin ? "Agent terrain, back office, ou admin" : "Agent terrain ou back office"}
        </div>
      </div>

      <form onSubmit={submit} style={{ background: "#1c1c1c", border: "1px solid #333333", borderRadius: 8, padding: 20, display: "flex", flexDirection: "column", gap: 14 }}>
        <Field label="Nom complet">
          <input type="text" value={form.name} onChange={set("name")} placeholder="Ahmed Ben Ali" style={inputStyle} />
        </Field>

        <Field label="Email">
          <input type="email" value={form.email} onChange={set("email")} placeholder="agent@zayerdigital.tn" style={inputStyle} />
        </Field>

        <Field label="Mot de passe">
          <input type="password" value={form.password} onChange={set("password")} placeholder="Min. 8 caractères" style={inputStyle} />
        </Field>

        <Field label="Rôle">
          <select value={form.role} onChange={set("role")} style={inputStyle}>
            {availableRoles.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </Field>

        {result && (
          <div style={{
            background: result.ok ? "#0f2a1a" : "#2a0f0f",
            border: `1px solid ${result.ok ? "#22c55e44" : "#ef444444"}`,
            color: result.ok ? "#22c55e" : "#ef4444",
            borderRadius: 4, padding: "10px 12px", fontFamily: "monospace", fontSize: 11,
          }}>
            {result.ok ? "✓ " : "⚠ "}{result.message}
          </div>
        )}

        <button type="submit" disabled={submitting} style={{
          background: "#ff4d00", color: "#fff", border: "none", borderRadius: 4,
          padding: "12px 16px", fontFamily: "monospace", fontSize: 12, fontWeight: 700,
          letterSpacing: 1, cursor: submitting ? "default" : "pointer", opacity: submitting ? 0.6 : 1,
        }}>
          {submitting ? "CRÉATION..." : "CRÉER LE COMPTE →"}
        </button>
      </form>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div style={{ fontFamily: "monospace", fontSize: 9, color: "#555", letterSpacing: 2, marginBottom: 6 }}>{label.toUpperCase()}</div>
      {children}
    </div>
  );
}

const inputStyle = {
  width: "100%", background: "#161616", border: "1px solid #3a3a3a", borderRadius: 4,
  color: "#f0f0f0", padding: "10px 12px", fontSize: 13, fontFamily: "inherit",
};
