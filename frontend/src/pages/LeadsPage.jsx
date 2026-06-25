import { useState, useEffect } from "react";
import BusinessPopup from "../components/BusinessPopup";

const API = "https://barbechai-backend.onrender.com";

const scoreColor = (score) => score >= 71 ? "#ff4d00" : score >= 41 ? "#f5a623" : "#4a9eff";
const scoreLabel = (score) => score >= 71 ? "HIGH" : score >= 41 ? "MEDIUM" : "LOW";

export default function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [filterCity, setFilterCity] = useState("ALL");

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      const res = await fetch(`${API}/crm/pipeline`);
      const data = await res.json();
      setLeads(data.leads || []);
    } catch (e) {
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const statuses = ["ALL", "NEW", "ENRICHING", "ENRICHED", "CONTACTED", "INTERESTED", "NOT_INTERESTED", "APPOINTMENT_SET"];
  const cities = ["ALL", ...new Set(leads.map(l => l.city).filter(Boolean))];

  const filtered = leads.filter(l => {
    if (filterStatus !== "ALL" && l.status !== filterStatus) return false;
    if (filterCity !== "ALL" && l.city !== filterCity) return false;
    return true;
  });

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "32px 16px" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00", letterSpacing: 3, marginBottom: 8 }}>LEAD MANAGEMENT</div>
        <h1 style={{ fontSize: 28, fontWeight: 800 }}>Leads Pipeline</h1>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 20 }}>
        <div style={{ flex: 1, minWidth: 140 }}>
          <div style={labelStyle}>Status</div>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={selectStyle}>
            {statuses.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: 120 }}>
          <div style={labelStyle}>City</div>
          <select value={filterCity} onChange={e => setFilterCity(e.target.value)} style={selectStyle}>
            {cities.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <button onClick={fetchLeads} style={{ alignSelf: "flex-end", background: "#1e1e1e", border: "1px solid #2a2a2a", color: "#888", borderRadius: 5, padding: "9px 16px", fontFamily: "monospace", fontSize: 11, cursor: "pointer" }}>↻ REFRESH</button>
      </div>

      {/* Stats */}
      <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
        {[["TOTAL", leads.length, "#555"], ["ENRICHED", leads.filter(l => l.status === "ENRICHED").length, "#22c55e"], ["ENRICHING", leads.filter(l => l.status === "ENRICHING").length, "#f5a623"], ["CONTACTED", leads.filter(l => l.status === "CONTACTED").length, "#4a9eff"]].map(([l, v, c]) => (
          <div key={l} style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
            <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 800, color: c }}>{v}</div>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>{l}</div>
          </div>
        ))}
      </div>

      {/* Leads List */}
      {loading ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#444", textAlign: "center", padding: 40 }}>Loading leads...</div>
      ) : filtered.length === 0 ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#333", textAlign: "center", padding: 40 }}>No leads found. Run a search first.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {filtered.map((lead, i) => (
            <div key={lead.id || i} onClick={() => setSelected(lead)}
              style={{ background: "#0f0f0f", border: "1px solid #1e1e1e", borderLeft: `3px solid ${scoreColor(lead.score)}`, borderRadius: 6, padding: "14px 18px", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#f0f0f0", marginBottom: 3 }}>{lead.name}</div>
                <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555", letterSpacing: 1 }}>{lead.category?.toUpperCase()} · {lead.city}</div>
                <div style={{ fontFamily: "monospace", fontSize: 10, marginTop: 4 }}>
                  <span style={{ color: lead.status === "ENRICHED" ? "#22c55e" : lead.status === "ENRICHING" ? "#f5a623" : "#4a9eff" }}>{lead.status}</span>
                  {lead.created_at && <span style={{ color: "#333", marginLeft: 8 }}>{new Date(lead.created_at).toLocaleDateString()}</span>}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ background: scoreColor(lead.score), color: "#fff", fontFamily: "monospace", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3, marginBottom: 4 }}>{scoreLabel(lead.score)}</div>
                <div style={{ fontFamily: "monospace", fontSize: 20, fontWeight: 800, color: scoreColor(lead.score) }}>{lead.score}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selected && <BusinessPopup biz={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

const labelStyle = { fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2, textTransform: "uppercase", marginBottom: 6 };
const selectStyle = { width: "100%", background: "#080808", border: "1px solid #2a2a2a", borderRadius: 5, color: "#f0f0f0", padding: "9px 12px", fontSize: 13, fontFamily: "Inter, sans-serif", cursor: "pointer" };
