import { apiFetch } from "../api";
import { useState, useEffect } from "react";
import LeadActivityModal from "../components/LeadActivityModal";

import { API } from "../config";

const CRM_STAGES = [
  { key: "NEW", label: "New", color: "#6B7280" },
  { key: "CONTACTED", label: "Contacted", color: "#4a9eff" },
  { key: "INTERESTED", label: "Interested", color: "#f5a623" },
  { key: "APPOINTMENT_SET", label: "Appointment", color: "#a855f7" },
  { key: "WON", label: "Won", color: "#22c55e" },
  { key: "LOST", label: "Lost", color: "#ef4444" },
];

const scoreColor = (score) => score >= 71 ? "#121830" : score >= 41 ? "#f5a623" : "#4a9eff";

export default function CRMPage({ user }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [movingId, setMovingId] = useState(null);
  const [agents, setAgents] = useState([]);
  const [assigningId, setAssigningId] = useState(null);
  // Stacked vertically for mobile (no more sideways swiping between
  // stages) — collapsed by default only once a stage has been reviewed,
  // everything starts open so nothing's hidden the first time you land here.
  const [collapsed, setCollapsed] = useState({});
  const [crmTotal, setCrmTotal] = useState(0);

  useEffect(() => { fetchCRMLeads(); fetchAgents(); }, []);

  const fetchAgents = async () => {
    try {
      const res = await apiFetch(`${API}/auth/agents`);
      const data = await res.json();
      setAgents((data.agents || []).filter(a => a.role === "field_agent" && a.is_active));
    } catch (e) {
      setAgents([]);
    }
  };

  const assignAgent = async (leadId, agentId, agentName) => {
    setAssigningId(leadId);
    try {
      await apiFetch(`${API}/crm/assign?lead_id=${encodeURIComponent(leadId)}&agent_id=${encodeURIComponent(agentId)}&agent_name=${encodeURIComponent(agentName)}`, { method: "POST" });
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, assigned_agent_name: agentName } : l));
    } catch (e) {} finally {
      setAssigningId(null);
    }
  };

  const fetchCRMLeads = async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${API}/crm/leads?limit=200&offset=0`);
      const data = await res.json();
      setLeads(data.leads || []);
      setCrmTotal(data.total ?? (data.leads || []).length);
    } catch (e) {
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const moveStage = async (leadId, newStatus) => {
    setMovingId(leadId);
    try {
      await apiFetch(`${API}/crm/status?lead_id=${encodeURIComponent(leadId)}&new_status=${newStatus}`, { method: "POST" });
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, crm_status: newStatus } : l));
    } catch (e) {} finally {
      setMovingId(null);
    }
  };

  const getStageLeads = (stageKey) => leads.filter(l => (l.crm_status || "NEW") === stageKey);

  const totalWon = leads.filter(l => l.crm_status === "WON").length;
  const totalLost = leads.filter(l => l.crm_status === "LOST").length;

  const toggleCollapsed = (key) => setCollapsed(prev => ({ ...prev, [key]: !prev[key] }));

  return (
    <div style={{ padding: "24px 16px", maxWidth: 720, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 8 }}>CRM PIPELINE</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800 }}>Sales Pipeline</h1>
          <div style={{ display: "flex", gap: 10 }}>
            <StatBadge label="TOTAL" value={leads.length} color="#6B7280" />
            <StatBadge label="WON" value={totalWon} color="#22c55e" />
            <StatBadge label="LOST" value={totalLost} color="#ef4444" />
            <button onClick={fetchCRMLeads} aria-label="Actualiser" style={{ background: "#E2E4E9", border: "1px solid #D7DAE1", color: "#6B7280", borderRadius: 5, padding: "6px 14px", fontFamily: "monospace", fontSize: 11, cursor: "pointer" }}>↻ REFRESH</button>
          </div>
        </div>
        {crmTotal > leads.length && (
          <div style={{ fontFamily: "monospace", fontSize: 10, color: "#f5a623", marginTop: 8 }}>
            ⚠ Affichage des {leads.length} premiers sur {crmTotal} leads CRM. Utilisez les filtres pour affiner.
          </div>
        )}
      </div>

      {loading ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#9AA0AC", textAlign: "center", padding: 60 }}>Loading CRM...</div>
      ) : leads.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60 }}>
          <div style={{ fontFamily: "monospace", fontSize: 13, color: "#9AA0AC", marginBottom: 8 }}>No leads in CRM yet.</div>
          <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC" }}>Search for businesses and click "ADD TO CRM →" in the popup.</div>
        </div>
      ) : (
        /* Vertical stack of stages — tap a stage header to expand/collapse
           it. Scrolls down the page instead of sideways across columns,
           which is much easier to use one-handed on a phone. */
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {CRM_STAGES.map(stage => {
            const stageLeads = getStageLeads(stage.key);
            const isCollapsed = !!collapsed[stage.key];
            return (
              <div key={stage.key}>
                {/* Stage header */}
                <button
                  onClick={() => toggleCollapsed(stage.key)}
                  style={{
                    width: "100%", background: "#FFFFFF", border: "1px solid #E2E4E9",
                    borderLeft: `4px solid ${stage.color}`, borderRadius: 6, padding: "12px 16px",
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    cursor: "pointer", textAlign: "left",
                  }}
                >
                  <div style={{ fontFamily: "monospace", fontSize: 12, fontWeight: 700, color: stage.color, letterSpacing: 1 }}>{stage.label.toUpperCase()}</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 800, color: stage.color }}>{stageLeads.length}</div>
                    <div style={{ color: "#9AA0AC", fontSize: 11 }}>{isCollapsed ? "▸" : "▾"}</div>
                  </div>
                </button>

                {/* Cards */}
                {!isCollapsed && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
                    {stageLeads.length === 0 ? (
                      <div style={{ border: "1px dashed #D7DAE1", borderRadius: 6, padding: "16px 12px", textAlign: "center", fontFamily: "monospace", fontSize: 10, color: "#9AA0AC" }}>Empty</div>
                    ) : stageLeads.map(lead => (
                      <div key={lead.id} style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderLeft: `3px solid ${scoreColor(lead.score)}`, borderRadius: 6, padding: 12 }}>
                        <div onClick={() => setSelected(lead)} style={{ cursor: "pointer", marginBottom: 10 }}>
                          <div style={{ fontSize: 13, fontWeight: 700, color: "#121830", marginBottom: 2 }}>{lead.name}</div>
                          <div style={{ fontFamily: "monospace", fontSize: 9, color: "#6B7280", letterSpacing: 1, marginBottom: 4 }}>{lead.category?.toUpperCase()} · {lead.city}</div>
                          {lead.phone && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#4a9eff" }}>📞 {lead.phone}</div>}
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6 }}>
                            <div style={{ fontFamily: "monospace", fontSize: 9, color: scoreColor(lead.score), border: `1px solid ${scoreColor(lead.score)}33`, padding: "2px 6px", borderRadius: 3 }}>
                              {lead.score >= 71 ? "HIGH" : lead.score >= 41 ? "MED" : "LOW"} {lead.score}
                            </div>
                            <div style={{ fontFamily: "monospace", fontSize: 9, color: lead.assigned_agent_name ? "#C4A264" : "#9AA0AC" }}>
                              👤 {lead.assigned_agent_name || "Non assigné"}
                            </div>
                          </div>
                        </div>

                        {/* Assign to Field Agent */}
                        <select
                          value=""
                          disabled={assigningId === lead.id}
                          onChange={(e) => {
                            const agent = agents.find(a => a.id === e.target.value);
                            if (agent) assignAgent(lead.id, agent.id, agent.name);
                          }}
                          style={{ width: "100%", marginBottom: 8, background: "#F5F6F8", border: "1px solid #D7DAE1", color: "#6B7280", borderRadius: 3, padding: "6px 8px", fontFamily: "monospace", fontSize: 10 }}
                        >
                          <option value="">{lead.assigned_agent_name ? `→ ${lead.assigned_agent_name}` : "Assign agent..."}</option>
                          {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                        </select>

                        {/* Move Buttons */}
                        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                          {CRM_STAGES.filter(s => s.key !== stage.key).map(s => (
                            <button key={s.key} onClick={() => moveStage(lead.id, s.key)}
                              disabled={movingId === lead.id}
                              style={{ background: "transparent", border: `1px solid ${s.color}44`, color: s.color, borderRadius: 3, padding: "3px 8px", fontFamily: "monospace", fontSize: 9, cursor: "pointer", letterSpacing: 0.5 }}>
                              → {s.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {selected && (
        <LeadActivityModal
          lead={selected}
          user={user}
          onClose={() => setSelected(null)}
          onNoteAdded={fetchCRMLeads}
          onAnonymized={() => { setSelected(null); fetchCRMLeads(); }}
        />
      )}
    </div>
  );
}

function StatBadge({ label, value, color }) {
  return (
    <div style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
      <div style={{ fontFamily: "monospace", fontSize: 16, fontWeight: 800, color }}>{value}</div>
      <div style={{ fontFamily: "monospace", fontSize: 9, color: "#9AA0AC", letterSpacing: 2 }}>{label}</div>
    </div>
  );
}
