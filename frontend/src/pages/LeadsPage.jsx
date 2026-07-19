import { apiFetch } from "../api";
import { useState, useEffect, useRef } from "react";
import BusinessPopup from "../components/BusinessPopup";

import { API } from "../config";

const scoreColor = (s) => s >= 71 ? "#121830" : s >= 41 ? "#f5a623" : "#4a9eff";
const scoreLabel = (s) => s >= 71 ? "HIGH" : s >= 41 ? "MEDIUM" : "LOW";

const labelStyle = { fontFamily: "monospace", fontSize: 9, color: "#6B7280", letterSpacing: 2, textTransform: "uppercase", marginBottom: 6 };
const selectStyle = { width: "100%", background: "#F5F6F8", border: "1px solid #D7DAE1", borderRadius: 5, color: "#121830", padding: "8px 12px", fontSize: 13, fontFamily: "Inter, sans-serif", cursor: "pointer" };

export default function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [filterCity, setFilterCity] = useState("ALL");
  const [filterCategory, setFilterCategory] = useState("ALL");
  const [filterOpportunity, setFilterOpportunity] = useState("ALL");
  const [sortBy, setSortBy] = useState("date");

  const [pendingCount, setPendingCount] = useState(0);
  const [enriching, setEnriching] = useState(false);
  const [enrichProgress, setEnrichProgress] = useState({ done: 0, total: 0 });
  const [leadsOffset, setLeadsOffset] = useState(0);
  const [leadsTotal, setLeadsTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [pipelineStats, setPipelineStats] = useState({ total: 0, high: 0, medium: 0, low: 0, enriched: 0 });
  const stopFlag = useRef(false);

  useEffect(() => { fetchLeads(); fetchPendingCount(); fetchStats(); }, []);

  const fetchStats = async () => {
    try {
      const res = await apiFetch(`${API}/crm/pipeline/stats`);
      const data = await res.json();
      setPipelineStats(data);
    } catch (e) {}
  };

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`${API}/crm/pipeline?limit=200&offset=0`);
      const data = await res.json();
      const initial = data.leads || [];
      setLeads(initial);
      setLeadsTotal(data.total ?? initial.length);
      setLeadsOffset(initial.length);
    } catch (e) {
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const loadMoreLeads = async () => {
    setLoadingMore(true);
    try {
      const res = await apiFetch(`${API}/crm/pipeline?limit=200&offset=${leadsOffset}`);
      const data = await res.json();
      const more = data.leads || [];
      setLeads(prev => [...prev, ...more]);
      setLeadsOffset(prev => prev + more.length);
    } catch (e) {} finally {
      setLoadingMore(false);
    }
  };

  const fetchPendingCount = async () => {
    try {
      const res = await apiFetch(`${API}/leads/pending-count`);
      const data = await res.json();
      setPendingCount(data.pending || 0);
    } catch (e) {
      // ignore
    }
  };

  const enrichAllPending = async () => {
    setEnriching(true);
    stopFlag.current = false;
    const startRes = await apiFetch(`${API}/leads/pending-count`);
    const startData = await startRes.json();
    const total = startData.pending || 0;
    setEnrichProgress({ done: 0, total });

    let remaining = total;
    let done = 0;

    while (remaining > 0 && !stopFlag.current) {
      try {
        const res = await apiFetch(`${API}/leads/enrich-pending?batch_size=10`, { method: "POST" });
        const data = await res.json();
        if (data.error) break;
        done += data.queued || 0;
        remaining = data.remaining ?? 0;
        setEnrichProgress({ done, total });
        await fetchLeads();
        await fetchPendingCount();
        // give background threads time to finish before queuing next batch
        await new Promise(r => setTimeout(r, 8000));
      } catch (e) {
        break;
      }
    }
    setEnriching(false);
    fetchLeads();
    fetchPendingCount();
  };

  // Keep the open popup in sync with the latest fetched data
  useEffect(() => {
    if (selected) {
      const fresh = leads.find(l => l.id === selected.id);
      if (fresh) setSelected(fresh);
    }
  }, [leads]);

  const statuses = ["ALL", "NEW", "ENRICHING", "ENRICHED", "ENRICHED_PARTIAL", "ENRICHMENT_FAILED", "CONTACTED", "INTERESTED", "NOT_INTERESTED", "APPOINTMENT_SET"];
  const cities = ["ALL", ...new Set(leads.map(l => l.city).filter(Boolean))];
  const categories = ["ALL", ...new Set(leads.map(l => l.category).filter(Boolean))];
  const opportunities = ["ALL", "HIGH", "MEDIUM", "LOW"];

  const filtered = leads
    .filter(l => {
      if (search && !l.name?.toLowerCase().includes(search.toLowerCase()) && !l.city?.toLowerCase().includes(search.toLowerCase())) return false;
      if (filterStatus !== "ALL" && l.status !== filterStatus) return false;
      if (filterCity !== "ALL" && l.city !== filterCity) return false;
      if (filterCategory !== "ALL" && l.category !== filterCategory) return false;
      if (filterOpportunity !== "ALL" && l.opportunity_level !== filterOpportunity) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "score") return b.score - a.score;
      if (sortBy === "name") return a.name?.localeCompare(b.name);
      return new Date(b.created_at) - new Date(a.created_at);
    });

  // Stat badges now come from pipelineStats (fetched via /crm/pipeline/stats),
  // not from filtering `leads`, since `leads` only holds the current page.

  const resetFilters = () => {
    setSearch("");
    setFilterStatus("ALL");
    setFilterCity("ALL");
    setFilterCategory("ALL");
    setFilterOpportunity("ALL");
    setSortBy("date");
  };

  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "24px 16px" }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 8 }}>LEAD MANAGEMENT</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800 }}>Leads Pipeline</h1>
          <button onClick={fetchLeads} style={{ background: "#E2E4E9", border: "1px solid #D7DAE1", color: "#888", borderRadius: 5, padding: "6px 14px", fontFamily: "monospace", fontSize: 11, cursor: "pointer" }}>↻ REFRESH</button>
        </div>
      </div>

      {/* Enrich pending banner */}
      {pendingCount > 0 && (
        <div style={{ background: "#FBF3E7", border: "1px solid #C4A26455", borderRadius: 6, padding: "12px 16px", marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
          <div style={{ fontFamily: "monospace", fontSize: 12, color: "#8A6D2F" }}>
            {enriching
              ? `⟳ ENRICHING ${enrichProgress.done}/${enrichProgress.total}...`
              : `${pendingCount} leads not yet enriched`}
          </div>
          {enriching ? (
            <button onClick={() => { stopFlag.current = true; }} style={{ background: "transparent", border: "1px solid #12183066", color: "#121830", borderRadius: 5, padding: "6px 14px", fontFamily: "monospace", fontSize: 11, cursor: "pointer" }}>
              STOP
            </button>
          ) : (
            <button onClick={enrichAllPending} style={{ background: "#121830", border: "none", color: "#fff", borderRadius: 5, padding: "6px 14px", fontFamily: "monospace", fontSize: 11, fontWeight: 700, cursor: "pointer" }}>
              ⚡ ENRICH PENDING
            </button>
          )}
        </div>
      )}

      {/* Stats */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        {[["TOTAL", pipelineStats.total, "#6B7280"], ["HIGH", pipelineStats.high, "#121830"], ["MED", pipelineStats.medium, "#f5a623"], ["LOW", pipelineStats.low, "#4a9eff"], ["ENRICHED", pipelineStats.enriched, "#22c55e"]].map(([l, v, c]) => (
          <div key={l} style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
            <div style={{ fontFamily: "monospace", fontSize: 16, fontWeight: 800, color: c }}>{v}</div>
            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#6B7280", letterSpacing: 2 }}>{l}</div>
          </div>
        ))}
      </div>

      {/* Search */}
      <div style={{ marginBottom: 12 }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by name or city..."
          style={{ width: "100%", background: "#FFFFFF", border: "1px solid #D7DAE1", borderRadius: 5, color: "#121830", padding: "10px 14px", fontSize: 13, fontFamily: "Inter, sans-serif" }}
        />
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        <div style={{ flex: 1, minWidth: 110 }}>
          <div style={labelStyle}>Status</div>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={selectStyle}>
            {statuses.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: 110 }}>
          <div style={labelStyle}>City</div>
          <select value={filterCity} onChange={e => setFilterCity(e.target.value)} style={selectStyle}>
            {cities.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: 120 }}>
          <div style={labelStyle}>Category</div>
          <select value={filterCategory} onChange={e => setFilterCategory(e.target.value)} style={selectStyle}>
            {categories.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: 100 }}>
          <div style={labelStyle}>Opportunity</div>
          <select value={filterOpportunity} onChange={e => setFilterOpportunity(e.target.value)} style={selectStyle}>
            {opportunities.map(o => <option key={o}>{o}</option>)}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: 100 }}>
          <div style={labelStyle}>Sort By</div>
          <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={selectStyle}>
            <option value="date">Date</option>
            <option value="score">Score</option>
            <option value="name">Name</option>
          </select>
        </div>
      </div>

      {/* Filter info + reset */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{ fontFamily: "monospace", fontSize: 11, color: "#6B7280" }}>
          {filtered.length} / {leads.length} leads
        </div>
        {(search || filterStatus !== "ALL" || filterCity !== "ALL" || filterCategory !== "ALL" || filterOpportunity !== "ALL") && (
          <button onClick={resetFilters} style={{ background: "transparent", border: "1px solid #9AA0AC", color: "#888", borderRadius: 4, padding: "4px 10px", fontFamily: "monospace", fontSize: 10, cursor: "pointer" }}>
            ✕ RESET
          </button>
        )}
      </div>

      {/* List */}
      {loading ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#6B7280", textAlign: "center", padding: 40 }}>Loading...</div>
      ) : filtered.length === 0 ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#9AA0AC", textAlign: "center", padding: 40 }}>No leads found.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {filtered.map((lead, i) => (
            <div key={lead.id || i} onClick={() => setSelected(lead)}
              style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderLeft: `3px solid ${scoreColor(lead.score)}`, borderRadius: 6, padding: "14px 18px", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#121830", marginBottom: 2 }}>{lead.name}</div>
                <div style={{ fontFamily: "monospace", fontSize: 10, color: "#6B7280", letterSpacing: 1, marginBottom: 3 }}>{lead.category?.toUpperCase()} · {lead.city}</div>
                {lead.phone && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#4a9eff", marginBottom: 2 }}>📞 {lead.phone}</div>}
                {lead.address && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#6B7280", marginBottom: 2 }}>📍 {lead.address}</div>}
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
                  {lead.website && <span style={{ fontFamily: "monospace", fontSize: 9, color: "#4a9eff", border: "1px solid #4a9eff33", padding: "2px 6px", borderRadius: 3 }}>🌐 WEB</span>}
                  {lead.facebook && <span style={{ fontFamily: "monospace", fontSize: 9, color: "#1877f2", border: "1px solid #1877f233", padding: "2px 6px", borderRadius: 3 }}>📘 FB</span>}
                  {lead.instagram && <span style={{ fontFamily: "monospace", fontSize: 9, color: "#e1306c", border: "1px solid #e1306c33", padding: "2px 6px", borderRadius: 3 }}>📸 IG</span>}
                  {lead.in_crm === "true" && <span style={{ fontFamily: "monospace", fontSize: 9, color: "#22c55e", border: "1px solid #22c55e33", padding: "2px 6px", borderRadius: 3 }}>✓ CRM</span>}
                </div>
                <div style={{ fontFamily: "monospace", fontSize: 9, marginTop: 6, color: lead.status === "ENRICHED" ? "#22c55e" : lead.status === "ENRICHING" ? "#f5a623" : lead.status === "ENRICHED_PARTIAL" ? "#4a9eff" : lead.status === "ENRICHMENT_FAILED" ? "#ef4444" : "#6B7280" }}>
                  {lead.status} {lead.created_at ? `· ${new Date(lead.created_at).toLocaleDateString("fr-TN")}` : ""}
                </div>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 12 }}>
                <div style={{ background: scoreColor(lead.score), color: "#fff", fontFamily: "monospace", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3, marginBottom: 4 }}>{scoreLabel(lead.score)}</div>
                <div style={{ fontFamily: "monospace", fontSize: 20, fontWeight: 800, color: scoreColor(lead.score) }}>{lead.score}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && leadsOffset < leadsTotal && (
        <button onClick={loadMoreLeads} disabled={loadingMore} style={{
          width: "100%", marginTop: 12, background: "#FFFFFF", border: "1px solid #D7DAE1", color: "#6B7280",
          borderRadius: 6, padding: "12px", fontFamily: "monospace", fontSize: 11, cursor: "pointer",
        }}>
          {loadingMore ? "Chargement..." : `CHARGER PLUS (${leadsTotal - leadsOffset} restants)`}
        </button>
      )}

      {selected && <BusinessPopup biz={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
