import { apiFetch } from "../api";
import { useState, useEffect } from "react";
import { API } from "../config";

export default function ReportsPage() {
  const [trends, setTrends] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [trendsRes, boardRes] = await Promise.all([
          apiFetch(`${API}/reports/trends?months=6`),
          apiFetch(`${API}/reports/leaderboard`),
        ]);
        const trendsData = await trendsRes.json();
        const boardData = await boardRes.json();
        setTrends(trendsData.months || []);
        setLeaderboard(boardData.agents || []);
      } catch (e) {
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const maxRevenue = Math.max(1, ...trends.map(t => t.revenue));
  const maxConversion = Math.max(1, ...trends.map(t => t.conversion_rate));

  if (loading) {
    return <div style={{ fontFamily: "monospace", fontSize: 13, color: "#9AA0AC", textAlign: "center", padding: 60 }}>Chargement des rapports...</div>;
  }

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "24px 16px" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#121830", letterSpacing: 3, marginBottom: 8 }}>RAPPORTS</div>
        <h1 style={{ fontSize: 24, fontWeight: 800 }}>Tendances & Performance</h1>
      </div>

      {/* Conversion rate trend */}
      <Section title="Taux de conversion (6 derniers mois)">
        <BarRow items={trends} valueKey="conversion_rate" max={maxConversion} color="#4a9eff" suffix="%" />
      </Section>

      {/* Revenue trend */}
      <Section title="Revenu par mois de clôture (TND)">
        <BarRow items={trends} valueKey="revenue" max={maxRevenue} color="#22c55e" suffix=" TND" />
      </Section>

      {/* Agent leaderboard */}
      <Section title="Classement des agents">
        {leaderboard.length === 0 ? (
          <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC" }}>Aucune donnée pour le moment.</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {leaderboard.map((a, i) => (
              <div key={a.agent_id} style={{ background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 6, padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  {i === 0 && a.deals_closed > 0 && <span>🏆</span>}
                  <span style={{ fontSize: 13, fontWeight: 700, color: "#121830" }}>{a.name}</span>
                </div>
                <div style={{ display: "flex", gap: 14, fontFamily: "monospace", fontSize: 10, color: "#6B7280" }}>
                  <span>{a.total_assigned} assignés</span>
                  <span style={{ color: "#22c55e" }}>{a.deals_closed} deals</span>
                  <span>{Math.round(a.total_deal_value).toLocaleString()} TND</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: "#121830", marginBottom: 10 }}>{title}</div>
      {children}
    </div>
  );
}

function BarRow({ items, valueKey, max, color, suffix }) {
  if (!items.length) {
    return <div style={{ fontFamily: "monospace", fontSize: 11, color: "#9AA0AC" }}>Aucune donnée pour le moment.</div>;
  }
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 8, height: 120, background: "#FFFFFF", border: "1px solid #E2E4E9", borderRadius: 6, padding: "12px 14px" }}>
      {items.map(item => {
        const value = item[valueKey] || 0;
        const heightPct = Math.max(4, (value / max) * 100);
        return (
          <div key={item.month} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", height: "100%" }}>
            <div style={{ fontFamily: "monospace", fontSize: 8, color: "#6B7280", marginBottom: 3 }}>
              {value % 1 === 0 ? value : value.toFixed(1)}{suffix}
            </div>
            <div style={{ width: "70%", height: `${heightPct}%`, background: color, borderRadius: "3px 3px 0 0", minHeight: 3 }} />
            <div style={{ fontFamily: "monospace", fontSize: 8, color: "#9AA0AC", marginTop: 4 }}>{item.month.slice(5)}</div>
          </div>
        );
      })}
    </div>
  );
}
