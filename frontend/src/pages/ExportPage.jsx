import { apiFetch } from "../api";
import { useState, useEffect } from "react";

import { API } from "../config";

export default function ExportPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [filterCity, setFilterCity] = useState("ALL");
  const [filterCategory, setFilterCategory] = useState("ALL");

  useEffect(() => { fetchLeads(); }, []);

  const fetchLeads = async () => {
    try {
      const res = await apiFetch(`${API}/crm/pipeline`);
      const data = await res.json();
      setLeads(data.leads || []);
    } catch (e) {
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const filtered = leads.filter(l => {
    if (filterStatus !== "ALL" && l.status !== filterStatus) return false;
    if (filterCity !== "ALL" && l.city !== filterCity) return false;
    if (filterCategory !== "ALL" && l.category !== filterCategory) return false;
    return true;
  });

  const exportCSV = () => {
    const headers = ["Name","Category","City","Score","Opportunity","Status","Phone","Website","Facebook","Instagram","Address","Date"];
    const rows = filtered.map(l => [
      l.name, l.category, l.city, l.score, l.opportunity_level,
      l.status, l.phone || "", l.website || "", l.facebook || "",
      l.instagram || "", l.address || "",
      l.created_at ? new Date(l.created_at).toLocaleDateString() : ""
    ]);
    const csv = [headers, ...rows].map(r => r.map(v => `"${v}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `barbechai_leads_${Date.now()}.csv`;
    a.click();
  };

  const cities = ["ALL", ...new Set(leads.map(l => l.city).filter(Boolean))];
  const categories = ["ALL", ...new Set(leads.map(l => l.category).filter(Boolean))];
  const statuses = ["ALL", "NEW", "ENRICHING", "ENRICHED", "CONTACTED", "INTERESTED", "NOT_INTERESTED", "APPOINTMENT_SET"];

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "32px 16px" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 8 }}>EXPORT CENTER</div>
        <h1 style={{ fontSize: 28, fontWeight: 800 }}>Export Leads</h1>
      </div>

      {/* Filters */}
      <div style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 8, padding: 20, marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
          <div style={{ flex: 1, minWidth: 130 }}>
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
          <div style={{ flex: 1, minWidth: 130 }}>
            <div style={labelStyle}>Category</div>
            <select value={filterCategory} onChange={e => setFilterCategory(e.target.value)} style={selectStyle}>
              {categories.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <div style={{ background: "#E5E7EB", border: "1px solid #D7DAE1", borderRadius: 6, padding: "12px 20px", fontFamily: "monospace", fontSize: 13, color: "#121830" }}>
            {filtered.length} leads selected
          </div>
          <button onClick={exportCSV} disabled={filtered.length === 0} style={{
            flex: 1, background: filtered.length === 0 ? "#E5E7EB" : "#121830",
            color: filtered.length === 0 ? "#6B7280" : "#fff",
            border: "none", borderRadius: 6, padding: "12px",
            fontFamily: "monospace", fontSize: 12, fontWeight: 700,
            cursor: filtered.length === 0 ? "not-allowed" : "pointer", letterSpacing: 1,
          }}>↓ EXPORT CSV</button>
        </div>
      </div>

      {/* Preview */}
      {loading ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#6B7280", textAlign: "center", padding: 40 }}>Loading...</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {filtered.slice(0, 20).map((lead, i) => (
            <div key={i} style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 5, padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#121830" }}>{lead.name}</div>
                <div style={{ fontFamily: "monospace", fontSize: 10, color: "#6B7280", marginTop: 2 }}>{lead.category} · {lead.city} · {lead.status}</div>
              </div>
              <div style={{ fontFamily: "monospace", fontSize: 13, fontWeight: 800, color: lead.score >= 71 ? "#121830" : lead.score >= 41 ? "#f5a623" : "#4a9eff" }}>{lead.score}</div>
            </div>
          ))}
          {filtered.length > 20 && (
            <div style={{ fontFamily: "monospace", fontSize: 11, color: "#6B7280", textAlign: "center", padding: 12 }}>
              +{filtered.length - 20} more in export
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const labelStyle = { fontFamily: "monospace", fontSize: 9, color: "#6B7280", letterSpacing: 2, textTransform: "uppercase", marginBottom: 6 };
const selectStyle = { width: "100%", background: "#F5F6F8", border: "1px solid #D7DAE1", borderRadius: 5, color: "#121830", padding: "9px 12px", fontSize: 13, fontFamily: "Inter, sans-serif", cursor: "pointer" };
