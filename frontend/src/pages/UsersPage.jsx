import { apiFetch } from "../api";
import { useState, useEffect } from "react";
import { API } from "../config";

const ROLE_OPTIONS = [
  { value: "field_agent", label: "Agent Terrain" },
  { value: "back_office", label: "Back Office" },
  { value: "admin", label: "Admin" },
];

const ROLE_LABEL = {
  field_agent: "Agent Terrain",
  back_office: "Back Office",
  admin: "Admin",
  master_admin: "Master Admin",
};

export default function UsersPage({ user }) {
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "field_agent" });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null); // { ok: bool, message: string }

  const [agents, setAgents] = useState([]);
  const [loadingAgents, setLoadingAgents] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [resetTarget, setResetTarget] = useState(null); // user id currently entering a new password for
  const [newPassword, setNewPassword] = useState("");

  const isMasterAdmin = user?.role === "master_admin";
  const availableRoles = isMasterAdmin ? ROLE_OPTIONS : ROLE_OPTIONS.filter(r => r.value !== "admin");

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const fetchAgents = async () => {
    setLoadingAgents(true);
    try {
      const res = await apiFetch(`${API}/auth/agents`);
      const data = await res.json();
      setAgents(data.agents || []);
    } catch {
      setAgents([]);
    } finally {
      setLoadingAgents(false);
    }
  };

  useEffect(() => { fetchAgents(); }, []);

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
        fetchAgents();
      }
    } catch (e) {
      setResult({ ok: false, message: "Échec de la connexion au serveur." });
    } finally {
      setSubmitting(false);
    }
  };

  const toggleActive = async (agent) => {
    setBusyId(agent.id);
    try {
      const endpoint = agent.is_active ? "deactivate" : "reactivate";
      await apiFetch(`${API}/auth/${endpoint}?user_id=${encodeURIComponent(agent.id)}`, { method: "POST" });
      setAgents(prev => prev.map(a => a.id === agent.id ? { ...a, is_active: !a.is_active } : a));
    } catch {} finally {
      setBusyId(null);
    }
  };

  const submitReset = async (agentId) => {
    if (newPassword.length < 8) return;
    setBusyId(agentId);
    try {
      const params = new URLSearchParams({ user_id: agentId, new_password: newPassword });
      const res = await apiFetch(`${API}/auth/reset-password?${params.toString()}`, { method: "POST" });
      const data = await res.json();
      if (!data.error) {
        setResetTarget(null);
        setNewPassword("");
      }
    } catch {} finally {
      setBusyId(null);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "32px 16px" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 8 }}>ADMINISTRATION</div>
        <h1 style={{ fontSize: 24, fontWeight: 800 }}>Créer un compte</h1>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#6B7280", marginTop: 4 }}>
          {isMasterAdmin ? "Agent terrain, back office, ou admin" : "Agent terrain ou back office"}
        </div>
      </div>

      <form onSubmit={submit} style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 8, padding: 20, display: "flex", flexDirection: "column", gap: 14, marginBottom: 36 }}>
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
            background: result.ok ? "#EAFBF1" : "#FDEDED",
            border: `1px solid ${result.ok ? "#22c55e44" : "#ef444444"}`,
            color: result.ok ? "#22c55e" : "#ef4444",
            borderRadius: 4, padding: "10px 12px", fontFamily: "monospace", fontSize: 11,
          }}>
            {result.ok ? "✓ " : "⚠ "}{result.message}
          </div>
        )}

        <button type="submit" disabled={submitting} style={{
          background: "#121830", color: "#fff", border: "none", borderRadius: 4,
          padding: "12px 16px", fontFamily: "monospace", fontSize: 12, fontWeight: 700,
          letterSpacing: 1, cursor: submitting ? "default" : "pointer", opacity: submitting ? 0.6 : 1,
        }}>
          {submitting ? "CRÉATION..." : "CRÉER LE COMPTE →"}
        </button>
      </form>

      {/* Account management */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 8 }}>COMPTES EXISTANTS</div>
        <h2 style={{ fontSize: 18, fontWeight: 800 }}>Agents & Back Office</h2>
      </div>

      {loadingAgents ? (
        <div style={{ fontFamily: "monospace", fontSize: 12, color: "#9AA0AC", padding: "20px 0" }}>Chargement...</div>
      ) : agents.length === 0 ? (
        <div style={{ fontFamily: "monospace", fontSize: 12, color: "#9AA0AC", padding: "20px 0" }}>Aucun compte pour le moment.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {agents.map(a => (
            <div key={a.id} style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 6, padding: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#121830" }}>{a.name}</div>
                  <div style={{ fontFamily: "monospace", fontSize: 10, color: "#6B7280" }}>{a.email}</div>
                  <div style={{ fontFamily: "monospace", fontSize: 9, color: "#C4A264", letterSpacing: 1, marginTop: 2 }}>
                    {(ROLE_LABEL[a.role] || a.role).toUpperCase()} · {a.is_active ? "ACTIF" : "DÉSACTIVÉ"}
                    {a.last_login ? ` · Dernière connexion ${new Date(a.last_login).toLocaleDateString()}` : " · Jamais connecté"}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  <button
                    onClick={() => { setResetTarget(resetTarget === a.id ? null : a.id); setNewPassword(""); }}
                    style={{ background: "transparent", border: "1px solid #D7DAE1", color: "#6B7280", borderRadius: 4, padding: "6px 10px", fontFamily: "monospace", fontSize: 10, cursor: "pointer" }}
                  >
                    RÉINITIALISER MDP
                  </button>
                  <button
                    onClick={() => toggleActive(a)}
                    disabled={busyId === a.id}
                    style={{
                      background: "transparent",
                      border: `1px solid ${a.is_active ? "#ef444455" : "#22c55e55"}`,
                      color: a.is_active ? "#ef4444" : "#22c55e",
                      borderRadius: 4, padding: "6px 10px", fontFamily: "monospace", fontSize: 10,
                      cursor: busyId === a.id ? "default" : "pointer", opacity: busyId === a.id ? 0.6 : 1,
                    }}
                  >
                    {a.is_active ? "DÉSACTIVER" : "RÉACTIVER"}
                  </button>
                </div>
              </div>

              {resetTarget === a.id && (
                <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    placeholder="Nouveau mot de passe (min. 8 caractères)"
                    style={{ ...inputStyle, flex: "1 1 200px" }}
                  />
                  <button
                    onClick={() => submitReset(a.id)}
                    disabled={newPassword.length < 8 || busyId === a.id}
                    style={{
                      background: "#121830", color: "#fff", border: "none", borderRadius: 4,
                      padding: "10px 14px", fontFamily: "monospace", fontSize: 10, fontWeight: 700,
                      cursor: newPassword.length < 8 ? "default" : "pointer", opacity: newPassword.length < 8 ? 0.5 : 1,
                    }}
                  >
                    CONFIRMER
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div style={{ fontFamily: "monospace", fontSize: 9, color: "#6B7280", letterSpacing: 2, marginBottom: 6 }}>{label.toUpperCase()}</div>
      {children}
    </div>
  );
}

const inputStyle = {
  width: "100%", background: "#F5F6F8", border: "1px solid #D7DAE1", borderRadius: 4,
  color: "#121830", padding: "10px 12px", fontSize: 13, fontFamily: "inherit",
};
