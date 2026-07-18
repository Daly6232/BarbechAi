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

  // Self-service MFA (admin/master_admin only)
  const [mfaSetup, setMfaSetup] = useState(null); // { secret, otpauth_url }
  const [mfaCode, setMfaCode] = useState("");
  const [mfaBusy, setMfaBusy] = useState(false);
  const [mfaMsg, setMfaMsg] = useState(null);
  const [mfaEnabled, setMfaEnabled] = useState(false);

  // Audit log
  const [auditEntries, setAuditEntries] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditOffset, setAuditOffset] = useState(0);
  const [auditHasMore, setAuditHasMore] = useState(true);
  const [showAudit, setShowAudit] = useState(false);

  // GDPR retention review
  const [retentionCandidates, setRetentionCandidates] = useState(null); // null = not loaded yet
  const [retentionDays, setRetentionDays] = useState(730);
  const [showRetention, setShowRetention] = useState(false);
  const [purging, setPurging] = useState(false);

  const loadRetention = async () => {
    try {
      const res = await apiFetch(`${API}/crm/retention-review`);
      const data = await res.json();
      setRetentionCandidates(data.candidates || []);
      setRetentionDays(data.retention_days || 730);
    } catch {
      setRetentionCandidates([]);
    }
  };

  const toggleRetention = () => {
    const next = !showRetention;
    setShowRetention(next);
    if (next && retentionCandidates === null) loadRetention();
  };

  const purgeRetention = async () => {
    if (!retentionCandidates || retentionCandidates.length === 0) return;
    setPurging(true);
    try {
      const ids = retentionCandidates.map(c => c.lead_id).join(",");
      await apiFetch(`${API}/crm/retention-purge?lead_ids=${encodeURIComponent(ids)}`, { method: "POST" });
      setRetentionCandidates([]);
    } catch {} finally {
      setPurging(false);
    }
  };

  const loadAudit = async (reset = false) => {
    setAuditLoading(true);
    const offset = reset ? 0 : auditOffset;
    try {
      const res = await apiFetch(`${API}/auth/audit-log?limit=50&offset=${offset}`);
      const data = await res.json();
      const entries = data.entries || [];
      setAuditEntries(prev => reset ? entries : [...prev, ...entries]);
      setAuditOffset(offset + entries.length);
      setAuditHasMore(entries.length === 50);
    } catch {
      if (reset) setAuditEntries([]);
    } finally {
      setAuditLoading(false);
    }
  };

  const toggleAudit = () => {
    const next = !showAudit;
    setShowAudit(next);
    if (next && auditEntries.length === 0) loadAudit(true);
  };

  const isMasterAdmin = user?.role === "master_admin";
  const isMfaEligible = user?.role === "admin" || user?.role === "master_admin";
  const availableRoles = isMasterAdmin ? ROLE_OPTIONS : ROLE_OPTIONS.filter(r => r.value !== "admin");

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const fetchAgents = async () => {
    setLoadingAgents(true);
    try {
      const res = await apiFetch(`${API}/auth/agents`);
      const data = await res.json();
      setAgents(data.agents || []);
      const me = (data.agents || []).find(a => a.id === user?.id);
      if (me) setMfaEnabled(!!me.mfa_enabled);
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
      if (data.error) {
        setMfaMsg(null);
        alert(data.error); // simple surface for a rare validation failure (weak password etc.)
      } else {
        setResetTarget(null);
        setNewPassword("");
      }
    } catch {} finally {
      setBusyId(null);
    }
  };

  const startMfaSetup = async () => {
    setMfaBusy(true);
    setMfaMsg(null);
    try {
      const res = await apiFetch(`${API}/auth/mfa/setup`, { method: "POST" });
      const data = await res.json();
      if (data.error) setMfaMsg({ ok: false, text: data.error });
      else setMfaSetup(data);
    } catch {
      setMfaMsg({ ok: false, text: "Échec de connexion au serveur." });
    } finally {
      setMfaBusy(false);
    }
  };

  const confirmMfa = async () => {
    if (mfaCode.length < 6) return;
    setMfaBusy(true);
    try {
      const res = await apiFetch(`${API}/auth/mfa/confirm?code=${mfaCode}`, { method: "POST" });
      const data = await res.json();
      if (data.error) {
        setMfaMsg({ ok: false, text: data.error });
      } else {
        setMfaEnabled(true);
        setMfaSetup(null);
        setMfaCode("");
        setMfaMsg({ ok: true, text: "Authentification à deux facteurs activée." });
      }
    } catch {} finally {
      setMfaBusy(false);
    }
  };

  const disableMfa = async () => {
    if (mfaCode.length < 6) {
      setMfaMsg({ ok: false, text: "Entrez votre code actuel à 6 chiffres pour confirmer la désactivation." });
      return;
    }
    setMfaBusy(true);
    try {
      const res = await apiFetch(`${API}/auth/mfa/disable?code=${mfaCode}`, { method: "POST" });
      const data = await res.json();
      if (data.error) {
        setMfaMsg({ ok: false, text: data.error });
      } else {
        setMfaEnabled(false);
        setMfaCode("");
        setMfaMsg({ ok: true, text: "Authentification à deux facteurs désactivée." });
      }
    } catch {} finally {
      setMfaBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "32px 16px" }}>
      {/* MFA self-service */}
      {isMfaEligible && (
        <div style={{ marginBottom: 36 }}>
          <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 8 }}>SÉCURITÉ DU COMPTE</div>
          <h2 style={{ fontSize: 18, fontWeight: 800, marginBottom: 12 }}>Authentification à deux facteurs</h2>

          <div style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 8, padding: 18 }}>
            <div style={{ fontFamily: "monospace", fontSize: 11, color: mfaEnabled ? "#22c55e" : "#9AA0AC", marginBottom: 12 }}>
              {mfaEnabled ? "✓ ACTIVÉE" : "○ NON ACTIVÉE"}
            </div>

            {mfaMsg && (
              <div style={{
                background: mfaMsg.ok ? "#EAFBF1" : "#FDEDED",
                color: mfaMsg.ok ? "#22c55e" : "#ef4444",
                border: `1px solid ${mfaMsg.ok ? "#22c55e44" : "#ef444444"}`,
                borderRadius: 4, padding: "8px 12px", fontFamily: "monospace", fontSize: 11, marginBottom: 12,
              }}>
                {mfaMsg.text}
              </div>
            )}

            {!mfaEnabled && !mfaSetup && (
              <button onClick={startMfaSetup} disabled={mfaBusy} style={{ background: "#121830", color: "#fff", border: "none", borderRadius: 4, padding: "10px 16px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
                ACTIVER LA 2FA →
              </button>
            )}

            {mfaSetup && (
              <div>
                <div style={{ fontSize: 12, color: "#374151", marginBottom: 8 }}>
                  Ouvrez Google Authenticator (ou équivalent) et ajoutez une clé manuellement avec ce code :
                </div>
                <div style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 700, color: "#121830", background: "#F5F6F8", border: "1px solid #D7DAE1", borderRadius: 4, padding: "10px 12px", marginBottom: 12, wordBreak: "break-all" }}>
                  {mfaSetup.secret}
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <input
                    type="text" inputMode="numeric" value={mfaCode}
                    onChange={e => setMfaCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    placeholder="Code à 6 chiffres"
                    style={{ ...inputStyle, flex: "1 1 160px" }}
                  />
                  <button onClick={confirmMfa} disabled={mfaCode.length < 6 || mfaBusy} style={{ background: "#121830", color: "#fff", border: "none", borderRadius: 4, padding: "10px 16px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, cursor: "pointer", opacity: mfaCode.length < 6 ? 0.5 : 1 }}>
                    CONFIRMER
                  </button>
                </div>
              </div>
            )}

            {mfaEnabled && (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <input
                  type="text" inputMode="numeric" value={mfaCode}
                  onChange={e => setMfaCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="Code actuel pour désactiver"
                  style={{ ...inputStyle, flex: "1 1 160px" }}
                />
                <button onClick={disableMfa} disabled={mfaBusy} style={{ background: "transparent", border: "1px solid #ef444455", color: "#ef4444", borderRadius: 4, padding: "10px 16px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
                  DÉSACTIVER
                </button>
              </div>
            )}
          </div>
        </div>
      )}

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
          <input type="password" value={form.password} onChange={set("password")} placeholder="Min. 8 car., 1 majuscule, 1 minuscule, 1 chiffre" style={inputStyle} />
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
                    {a.mfa_enabled ? " · 2FA ✓" : ""}
                    {a.last_login ? ` · Dernière connexion ${new Date(a.last_login).toLocaleDateString()}` : " · Jamais connecté"}
                  </div>
                  {a.last_login_ip && (
                    <div style={{ fontFamily: "monospace", fontSize: 8, color: "#9AA0AC", marginTop: 2 }}>
                      {a.last_login_ip}{a.last_login_device ? ` · ${a.last_login_device.slice(0, 60)}` : ""}
                    </div>
                  )}
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
                    placeholder="Min. 8 car., 1 majuscule, 1 minuscule, 1 chiffre"
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

      {/* GDPR retention review */}
      <div style={{ marginTop: 36 }}>
        <button onClick={toggleRetention} style={{
          width: "100%", background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 6,
          padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center",
          cursor: "pointer", textAlign: "left",
        }}>
          <div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 4 }}>RGPD</div>
            <div style={{ fontSize: 15, fontWeight: 800 }}>Nettoyage des données ({retentionDays} jours)</div>
          </div>
          <div style={{ color: "#9AA0AC" }}>{showRetention ? "▾" : "▸"}</div>
        </button>

        {showRetention && (
          <div style={{ marginTop: 10 }}>
            {retentionCandidates === null ? (
              <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC", padding: "12px 0" }}>Chargement...</div>
            ) : retentionCandidates.length === 0 ? (
              <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC", padding: "12px 0" }}>Aucun lead perdu au-delà de la période de rétention.</div>
            ) : (
              <>
                <div style={{ fontSize: 12, color: "#374151", marginBottom: 10 }}>
                  {retentionCandidates.length} lead(s) marqué(s) "Perdu" depuis plus de {retentionDays} jours. Anonymiser supprime nom/téléphone/email/notes définitivement, sans affecter les statistiques du pipeline.
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 10, maxHeight: 200, overflowY: "auto" }}>
                  {retentionCandidates.map(c => (
                    <div key={c.lead_id} style={{ fontFamily: "monospace", fontSize: 10, color: "#6B7280", background: "#F5F6F8", borderRadius: 3, padding: "6px 10px" }}>
                      {c.name} · {c.created_at ? new Date(c.created_at).toLocaleDateString() : ""}
                    </div>
                  ))}
                </div>
                <button onClick={purgeRetention} disabled={purging} style={{ background: "#ef4444", color: "#fff", border: "none", borderRadius: 4, padding: "9px 16px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
                  {purging ? "..." : `ANONYMISER LES ${retentionCandidates.length} LEADS →`}
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Audit trail */}
      <div style={{ marginTop: 36 }}>
        <button onClick={toggleAudit} style={{
          width: "100%", background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 6,
          padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center",
          cursor: "pointer", textAlign: "left",
        }}>
          <div>
            <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 4 }}>ACCOUNTABILITÉ</div>
            <div style={{ fontSize: 15, fontWeight: 800 }}>Journal d'audit</div>
          </div>
          <div style={{ color: "#9AA0AC" }}>{showAudit ? "▾" : "▸"}</div>
        </button>

        {showAudit && (
          <div style={{ marginTop: 10 }}>
            {auditEntries.length === 0 && !auditLoading ? (
              <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC", padding: "12px 0" }}>Aucune activité enregistrée.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {auditEntries.map(e => (
                  <div key={e.id} style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderLeft: `3px solid ${auditColor(e.action)}`, borderRadius: 4, padding: "10px 12px" }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#121830" }}>{auditLabel(e.action)}</div>
                    <div style={{ fontFamily: "monospace", fontSize: 9, color: "#6B7280", marginTop: 2 }}>
                      {e.actor_name} · {e.timestamp ? new Date(e.timestamp).toLocaleString() : ""}{e.ip ? ` · ${e.ip}` : ""}
                    </div>
                    {e.details && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#9AA0AC", marginTop: 3 }}>{e.details}</div>}
                  </div>
                ))}
              </div>
            )}

            {auditHasMore && (
              <button onClick={() => loadAudit(false)} disabled={auditLoading} style={{
                width: "100%", marginTop: 10, background: "transparent", border: "1px solid #D7DAE1", color: "#6B7280",
                borderRadius: 4, padding: "8px", fontFamily: "monospace", fontSize: 10, cursor: "pointer",
              }}>
                {auditLoading ? "Chargement..." : "CHARGER PLUS"}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const AUDIT_LABELS = {
  USER_CREATED: "Compte créé",
  USER_DEACTIVATED: "Compte désactivé",
  USER_REACTIVATED: "Compte réactivé",
  PASSWORD_RESET: "Mot de passe réinitialisé",
  LOGIN_SUCCESS: "Connexion réussie",
  LOGIN_FAILED: "Échec de connexion",
  ACCOUNT_LOCKED: "Compte verrouillé (tentatives multiples)",
  MFA_LOGIN_FAILED: "Code 2FA invalide",
  MFA_ENABLED: "2FA activée",
  MFA_DISABLED: "2FA désactivée",
  LEAD_REASSIGNED: "Lead réassigné",
};

const AUDIT_COLORS = {
  USER_CREATED: "#22c55e",
  USER_DEACTIVATED: "#ef4444",
  USER_REACTIVATED: "#22c55e",
  PASSWORD_RESET: "#f5a623",
  LOGIN_SUCCESS: "#4a9eff",
  LOGIN_FAILED: "#ef4444",
  ACCOUNT_LOCKED: "#ef4444",
  MFA_LOGIN_FAILED: "#ef4444",
  MFA_ENABLED: "#22c55e",
  MFA_DISABLED: "#f5a623",
  LEAD_REASSIGNED: "#a855f7",
};

function auditLabel(action) { return AUDIT_LABELS[action] || action; }
function auditColor(action) { return AUDIT_COLORS[action] || "#9AA0AC"; }

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
