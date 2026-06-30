import { useState, useEffect } from "react";
import BusinessPopup from "../components/BusinessPopup";

import { API } from "../config";

const CRM_STAGES = [
  { key: "NEW", label: "New", color: "#555" },
  { key: "CONTACTED", label: "Contacted", color: "#4a9eff" },
  { key: "INTERESTED", label: "Interested", color: "#f5a623" },
  { key: "APPOINTMENT_SET", label: "Appointment", color: "#a855f7" },
  { key: "WON", label: "Won", color: "#22c55e" },
  { key: "LOST", label: "Lost", color: "#ef4444" },
];

const scoreColor = (score) => score >= 71 ? "#ff4d00" : score >= 41 ? "#f5a623" : "#4a9eff";

export default function CRMPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [movingId, setMovingId] = useState(null);

  useEffect(() => { fetchCRMLeads(); }, []);

  const fetchCRMLeads = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/crm/leads`);
      const data = await res.json();
      setLeads(data.leads || []);
    } catch (e) {
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const moveStage = async (leadId, newStatus) => {
    setMovingId(leadId);
    try {
      await fetch(`${API}/crm/status?lead_id=${encodeURIComponent(leadId)}&new_status=${newStatus}`, { method: "POST" });
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, crm_status: newStatus } : l));
    } catch (e) {} finally {
      setMovingId(null);
    }
  };

  const getStageLeads = (stageKey) => leads.filter(l => (l.crm_status || "NEW") === stageKey);

  const totalWon = leads.filter(l => l.crm_status === "WON").length;
  const totalLost = leads.filter(l => l.crm_status === "LOST").length;

  return (
    <div style={{ padding: "24px 16px", maxWidth: 1200, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00", letterSpacing: 3, marginBottom: 8 }}>CRM PIPELINE</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800 }}>Sales Pipeline</h1>
          <div style={{ display: "flex", gap: 10 }}>
            <StatBadge label="TOTAL" value={leads.length} color="#555" />
            <StatBadge label="WON" value={totalWon} color="#22c55e" />
            <StatBadge label="LOST" value={totalLost} color="#ef4444" />
            <button onClick={fetchCRMLeads} style={{ background: "#1e1e1e", border: "1px solid #2a2a2a", color: "#888", borderRadius: 5, padding: "6px 14px", fontFamily: "monospace", fontSize: 11, cursor: "pointer" }}>↻ REFRESH</button>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#444", textAlign: "center", padding: 60 }}>Loading CRM...</div>
      ) : leads.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60 }}>
          <div style={{ fontFamily: "monospace", fontSize: 13, color: "#333", marginBottom: 8 }}>No leads in CRM yet.</div>
          <div style={{ fontFamily: "monospace", fontSize: 11, color: "#222" }}>Search for businesses and click "ADD TO CRM →" in the popup.</div>
        </div>
      ) : (
        /* Kanban Board */
        <div style={{ display: "flex", gap: 12, overflowX: "auto", paddingBottom: 16 }}>
          {CRM_STAGES.map(stage => (
            <div key={stage.key} style={{ minWidth: 220, flex: "0 0 220px" }}>
              {/* Column Header */}
              <div style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderTop: `3px solid ${stage.color}`, borderRadius: 6, padding: "10px 14px", marginBottom: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontFamily: "monospace", fontSize: 11, fontWeight: 700, color: stage.color, letterSpacing: 1 }}>{stage.label.toUpperCase()}</div>
                <div style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 800, color: stage.color }}>{getStageLeads(stage.key).length}</div>
              </div>

              {/* Cards */}
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {getStageLeads(stage.key).map(lead => (
                  <div key={lead.id} style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderLeft: `3px solid ${scoreColor(lead.score)}`, borderRadius: 6, padding: 12 }}>
                    <div onClick={() => setSelected(lead)} style={{ cursor: "pointer", marginBottom: 10 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: "#f0f0f0", marginBottom: 2 }}>{lead.name}</div>
                      <div style={{ fontFamily: "monospace", fontSize: 9, color: "#555", letterSpacing: 1, marginBottom: 4 }}>{lead.category?.toUpperCase()} · {lead.city}</div>
                      {lead.phone && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#4a9eff" }}>📞 {lead.phone}</div>}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6 }}>
                        <div style={{ fontFamily: "monospace", fontSize: 9, color: scoreColor(lead.score), border: `1px solid ${scoreColor(lead.score)}33`, padding: "2px 6px", borderRadius: 3 }}>
                          {lead.score >= 71 ? "HIGH" : lead.score >= 41 ? "MED" : "LOW"} {lead.score}
                        </div>
                        {lead.assigned_agent_name && (
                          <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444" }}>👤 {lead.assigned_agent_name}</div>
                        )}
                      </div>
                    </div>

                    {/* Move Buttons */}
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                      {CRM_STAGES.filter(s => s.key !== stage.key).map(s => (
                        <button key={s.key} onClick={() => moveStage(lead.id, s.key)}
                          disabled={movingId === lead.id}
                          style={{ background: "transparent", border: `1px solid ${s.color}44`, color: s.color, borderRadius: 3, padding: "2px 6px", fontFamily: "monospace", fontSize: 8, cursor: "pointer", letterSpacing: 0.5 }}>
                          → {s.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                {getStageLeads(stage.key).length === 0 && (
                  <div style={{ border: "1px dashed #1e1e1e", borderRadius: 6, padding: "20px 12px", textAlign: "center", fontFamily: "monospace", fontSize: 10, color: "#2a2a2a" }}>Empty</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {selected && <BusinessPopup biz={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function StatBadge({ label, value, color }) {
  return (
    <div style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
      <div style={{ fontFamily: "monospace", fontSize: 16, fontWeight: 800, color }}>{value}</div>
      <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>{label}</div>
    </div>
  );
}
