import { useState, useEffect } from "react";
import BusinessPopup from "../components/BusinessPopup";

import { API } from "../config";

export default function AgentPage() {
  const [agentId, setAgentId] = useState("agent_1");
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchAgentLeads();
  }, [agentId]);

  const fetchAgentLeads = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/agent/stats?agent_id=${agentId}`);
      const data = await res.json();
      setStats(data);
      setLeads(data.leads || []);
    } catch (e) {
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const logAction = async (leadId, action) => {
    try {
      await fetch(`${API}/agent/log?agent_id=${agentId}&lead_id=${leadId}&action=${action}`, { method: "POST" });
      fetchAgentLeads();
    } catch (e) {}
  };

  const scoreColor = (score) => score >= 71 ? "#ff4d00" : score >= 41 ? "#f5a623" : "#4a9eff";

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "32px 16px" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00", letterSpacing: 3, marginBottom: 8 }}>AGENT PANEL</div>
        <h1 style={{ fontSize: 28, fontWeight: 800 }}>My Assigned Leads</h1>
      </div>

      {/* Agent Selector */}
      <div style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 8, padding: 16, marginBottom: 20 }}>
        <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, marginBottom: 6 }}>AGENT ID</div>
        <input value={agentId} onChange={e => setAgentId(e.target.value)}
          style={{ background: "#080808", border: "1px solid #2a2a2a", borderRadius: 4, color: "#f0f0f0", padding: "8px 12px", fontSize: 13, fontFamily: "Inter, sans-serif", width: "100%" }} />
      </div>

      {/* Stats */}
      {stats && (
        <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
          {[
            ["ASSIGNED", stats.total_assigned || 0, "#555"],
            ["CONTACTED", stats.contacted || 0, "#4a9eff"],
            ["INTERESTED", stats.interested || 0, "#22c55e"],
            ["APPOINTMENTS", stats.appointments || 0, "#ff4d00"],
          ].map(([l, v, c]) => (
            <div key={l} style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
              <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 800, color: c }}>{v}</div>
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>{l}</div>
            </div>
          ))}
        </div>
      )}

      {/* Leads */}
      {loading ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#444", textAlign: "center", padding: 40 }}>Loading...</div>
      ) : leads.length === 0 ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#333", textAlign: "center", padding: 40 }}>No leads assigned yet.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {leads.map((lead, i) => (
            <div key={lead.id || i} style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderLeft: `3px solid ${scoreColor(lead.score)}`, borderRadius: 6, padding: "14px 18px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                <div onClick={() => setSelected(lead)} style={{ cursor: "pointer" }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: "#f0f0f0", marginBottom: 3 }}>{lead.name}</div>
                  <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555" }}>{lead.category?.toUpperCase()} · {lead.city}</div>
                  {lead.phone && <div style={{ fontFamily: "monospace", fontSize: 11, color: "#4a9eff", marginTop: 4 }}>📞 {lead.phone}</div>}
                </div>
                <div style={{ background: scoreColor(lead.score), color: "#fff", fontFamily: "monospace", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3 }}>
                  {lead.score}
                </div>
              </div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {["CALLED", "INTERESTED", "NOT_INTERESTED", "APPOINTMENT_SET"].map(action => (
                  <button key={action} onClick={() => logAction(lead.id, action)} style={{
                    background: "transparent", border: "1px solid #2a2a2a", color: "#666",
                    borderRadius: 3, padding: "4px 10px", fontFamily: "monospace", fontSize: 10,
                    cursor: "pointer", letterSpacing: 1,
                  }}>{action}</button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {selected && <BusinessPopup biz={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
