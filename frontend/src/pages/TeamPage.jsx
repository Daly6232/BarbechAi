import { apiFetch } from "../api";
import { useState, useEffect } from "react";
import { API } from "../config";
import AgentTimelineModal from "../components/AgentTimelineModal";

const ROLE_LABEL = {
  field_agent: "Agent Terrain",
  back_office: "Back Office",
  admin: "Admin",
};

const SORT_OPTIONS = [
  { key: "deals_closed", label: "Deals conclus" },
  { key: "calls_today", label: "Appels aujourd'hui" },
  { key: "total_actions", label: "Total actions" },
  { key: "contacted", label: "Contactés" },
];

export default function TeamPage() {
  const [agents, setAgents] = useState([]);
  const [stats, setStats] = useState({}); // agent_id -> stats
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState("deals_closed");
  const [viewingTimeline, setViewingTimeline] = useState(null);
  const [overdueFollowups, setOverdueFollowups] = useState([]);

  const loadOverdue = async () => {
    try {
      const res = await apiFetch(`${API}/crm/followups?overdue_only=true`);
      const data = await res.json();
      setOverdueFollowups(data.followups || []);
    } catch {}
  };

  const load = async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${API}/auth/agents`);
      const data = await res.json();
      const list = data.agents || [];
      setAgents(list);

      const statPairs = await Promise.all(
        list.map(async (a) => {
          try {
            const r = await apiFetch(`${API}/agent/stats/${encodeURIComponent(a.id)}`);
            const d = await r.json();
            return [a.id, d];
          } catch {
            return [a.id, null];
          }
        })
      );
      const statsMap = {};
      statPairs.forEach(([id, d]) => { statsMap[id] = d; });
      setStats(statsMap);
    } catch {
      setAgents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); loadOverdue(); }, []);

  const sorted = [...agents].sort((a, b) => {
    const sa = stats[a.id]?.[sortKey] || 0;
    const sb = stats[b.id]?.[sortKey] || 0;
    return sb - sa;
  });

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "24px 16px" }}>
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 8 }}>SUPERVISION</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
          <h1 style={{ fontSize: 24, fontWeight: 800 }}>Contrôle Qualité — Équipe</h1>
          <button onClick={load} aria-label="Actualiser" style={{ background: "#E2E4E9", border: "1px solid #D7DAE1", color: "#6B7280", borderRadius: 5, padding: "6px 14px", fontFamily: "monospace", fontSize: 11, cursor: "pointer" }}>↻ REFRESH</button>
        </div>
      </div>

      {/* Overdue follow-ups — CEO-level visibility into leads nobody is
          following up on, across the whole team */}
      {overdueFollowups.length > 0 && (
        <div style={{ background: "#FDEDED", border: "1px solid #ef444444", borderRadius: 8, padding: 14, marginBottom: 20 }}>
          <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ef4444", letterSpacing: 2, marginBottom: 8 }}>
            ⚠ {overdueFollowups.length} SUIVI(S) EN RETARD
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 160, overflowY: "auto" }}>
            {overdueFollowups.slice(0, 20).map(f => (
              <div key={f.id} style={{ fontFamily: "monospace", fontSize: 10, color: "#374151" }}>
                <span style={{ fontWeight: 700 }}>{f.name}</span> — {f.next_action || "action non précisée"} · {f.assigned_agent_name || "non assigné"} · {f.callback_date ? new Date(f.callback_date).toLocaleDateString() : ""}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sort control */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 18 }}>
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "#9AA0AC", alignSelf: "center", marginRight: 4 }}>TRIER PAR:</div>
        {SORT_OPTIONS.map(opt => (
          <button
            key={opt.key}
            onClick={() => setSortKey(opt.key)}
            style={{
              background: sortKey === opt.key ? "#121830" : "transparent",
              color: sortKey === opt.key ? "#fff" : "#6B7280",
              border: `1px solid ${sortKey === opt.key ? "#121830" : "#D7DAE1"}`,
              borderRadius: 4, padding: "5px 10px", fontFamily: "monospace", fontSize: 9, cursor: "pointer",
            }}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ fontFamily: "monospace", fontSize: 12, color: "#9AA0AC", padding: "20px 0" }}>Chargement...</div>
      ) : sorted.length === 0 ? (
        <div style={{ fontFamily: "monospace", fontSize: 12, color: "#9AA0AC", padding: "20px 0" }}>Aucun agent pour le moment.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {sorted.map((a, i) => {
            const s = stats[a.id] || {};
            return (
              <div key={a.id} style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 8, padding: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {i === 0 && (s[sortKey] || 0) > 0 && <span style={{ fontSize: 13 }}>🏆</span>}
                      <div style={{ fontSize: 14, fontWeight: 700, color: "#121830" }}>{a.name}</div>
                    </div>
                    <div style={{ fontFamily: "monospace", fontSize: 9, color: "#C4A264", letterSpacing: 1, marginTop: 2 }}>
                      {(ROLE_LABEL[a.role] || a.role).toUpperCase()} · {a.is_active ? "ACTIF" : "DÉSACTIVÉ"}
                    </div>
                  </div>
                  <button
                    onClick={() => setViewingTimeline(a)}
                    style={{ background: "transparent", border: "1px solid #D7DAE1", color: "#6B7280", borderRadius: 4, padding: "5px 10px", fontFamily: "monospace", fontSize: 9, cursor: "pointer" }}
                  >
                    HISTORIQUE →
                  </button>
                </div>

                {/* KPI grid */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(88px, 1fr))", gap: 8, marginTop: 12 }}>
                  <Stat label="Assignés" value={s.total_assigned} />
                  <Stat label="Contactés" value={s.contacted} color="#4a9eff" />
                  <Stat label="Intéressés" value={s.interested} color="#f5a623" />
                  <Stat label="RDV" value={s.appointments} color="#a855f7" />
                  <Stat label="Deals" value={s.deals_closed} color="#22c55e" />
                  <Stat label="Appels/jour" value={s.calls_today} />
                </div>
                {s.total_deal_value > 0 && (
                  <div style={{ marginTop: 8, fontFamily: "monospace", fontSize: 10, color: "#22c55e" }}>
                    💰 {s.total_deal_value.toLocaleString()} TND en deals conclus
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {viewingTimeline && (
        <AgentTimelineModal agent={viewingTimeline} onClose={() => setViewingTimeline(null)} />
      )}
    </div>
  );
}

function Stat({ label, value, color = "#121830" }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: 16, fontWeight: 800, color }}>{value ?? 0}</div>
      <div style={{ fontFamily: "monospace", fontSize: 8, color: "#9AA0AC", letterSpacing: 0.5 }}>{label.toUpperCase()}</div>
    </div>
  );
}
