import { apiFetch } from "../api";
import { useState, useEffect } from "react";
import BusinessPopup from "../components/BusinessPopup";
import { API } from "../config";

const STAGE_LABEL = {
  NEW: "New",
  CONTACTED: "Contacted",
  CALLBACK: "Callback",
  INTERESTED: "Interested",
  APPOINTMENT_SET: "Appointment Set",
  MEETING_DONE: "Meeting Done",
  PROPOSAL_SENT: "Proposal Sent",
  DEAL_CLOSED: "Deal Closed",
  NOT_INTERESTED: "Not Interested",
  DECLINED: "Declined",
};

const STAGE_COLOR = {
  NEW: "#555", CONTACTED: "#4a9eff", CALLBACK: "#f5a623", INTERESTED: "#22c55e",
  APPOINTMENT_SET: "#ff4d00", MEETING_DONE: "#a855f7", PROPOSAL_SENT: "#f5a623",
  DEAL_CLOSED: "#22c55e", NOT_INTERESTED: "#666", DECLINED: "#ef4444",
};

export default function AgentPage({ user }) {
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [busyLeadId, setBusyLeadId] = useState(null);
  const [dealModal, setDealModal] = useState(null); // lead being closed with a deal value
  const [declineModal, setDeclineModal] = useState(null); // lead being declined with a reason
  const [callbackModal, setCallbackModal] = useState(null); // lead being scheduled for a callback

  const [viewMode, setViewMode] = useState("queue"); // "queue" | "list"
  const [locations, setLocations] = useState({});
  const [governorate, setGovernorate] = useState("");
  const [delegation, setDelegation] = useState("");
  const [skippedIds, setSkippedIds] = useState(new Set()); // session-only "come back later" for the queue

  // tel: links only open a real dialer on a device that has one (phone/APK).
  // On a PC there's nothing to hand off to, so don't pretend there is —
  // show a copy-the-number action there instead.
  const isNativeOrMobile = typeof window !== "undefined" &&
    (window.Capacitor?.isNativePlatform?.() || /Android|iPhone/i.test(navigator.userAgent));

  useEffect(() => {
    load();
    apiFetch(`${API}/agent/locations`).then(r => r.json()).then(d => setLocations(d.locations || {})).catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [governorate, delegation]);

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (governorate) params.set("governorate", governorate);
      if (delegation) params.set("delegation", delegation);
      const [leadsRes, statsRes] = await Promise.all([
        apiFetch(`${API}/agent/my-leads?${params.toString()}`),
        apiFetch(`${API}/agent/stats`),
      ]);
      const leadsData = await leadsRes.json();
      const statsData = await statsRes.json();
      setLeads(leadsData.leads || []);
      setStats(statsData);
    } catch (e) {
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const updateLead = async (leadId, body, action) => {
    setBusyLeadId(leadId);
    try {
      await apiFetch(`${API}/agent/lead/${leadId}/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (action) {
        await apiFetch(`${API}/agent/log?lead_id=${leadId}&action=${action}`, { method: "POST" });
      }
      await load();
    } catch (e) {
      // keep it simple on a phone screen — a failed action just doesn't advance the card
    } finally {
      setBusyLeadId(null);
    }
  };

  const markContacted = (lead) => updateLead(lead.id, { status: "CONTACTED" }, "CONTACTED");
  const markInterested = (lead) => updateLead(lead.id, { status: "INTERESTED" }, "INTERESTED");
  const markNoAnswer = (lead) => updateLead(lead.id, {}, "NO_ANSWER");
  const confirmCallback = async () => {
    if (!callbackModal || !callbackModal.when) return;
    await updateLead(callbackModal.lead.id, { status: "CALLBACK", appointment_date: callbackModal.when }, "CALLBACK");
    setSkippedIds(prev => new Set(prev).add(callbackModal.lead.id));
    setCallbackModal(null);
  };
  const setAppointment = (lead) => {
    const when = window.prompt("Appointment date/time (e.g. 2026-07-20T14:00)");
    if (!when) return;
    updateLead(lead.id, { status: "APPOINTMENT_SET", appointment_date: when }, "APPOINTMENT_SET");
  };

  // Queue-mode wrappers: same underlying calls, plus session-scoped skip so a
  // "no answer" doesn't just re-show the same top-priority lead forever.
  const qCall = (lead) => {
    if (isNativeOrMobile) {
      window.location.href = `tel:${lead.phone}`;
    } else {
      navigator.clipboard?.writeText(lead.phone).catch(() => {});
    }
  };
  const qNoAnswer = (lead) => {
    markNoAnswer(lead);
    setSkippedIds(prev => new Set(prev).add(lead.id));
  };
  const qInterested = (lead) => {
    markInterested(lead);
    setSkippedIds(prev => new Set(prev).add(lead.id));
  };
  const qDecline = (lead) => setDeclineModal({ lead, reason: "" }); // skip added in confirmDecline
  const qCallback = (lead) => setCallbackModal({ lead, when: "" });
  const resetSkipped = () => setSkippedIds(new Set());
  const markMeetingDone = (lead) =>
    updateLead(lead.id, { status: "MEETING_DONE", meeting_completed_at: new Date().toISOString() }, "MEETING_DONE");
  const markProposalSent = (lead) =>
    updateLead(lead.id, { status: "PROPOSAL_SENT", proposal_sent_at: new Date().toISOString() }, "PROPOSAL_SENT");

  const confirmDeal = async () => {
    if (!dealModal) return;
    const value = parseFloat(dealModal.value);
    if (isNaN(value) || value <= 0) return;
    await updateLead(dealModal.lead.id, {
      status: "DEAL_CLOSED",
      contract_sent_at: new Date().toISOString(),
      deal_value: value,
    }, "DEAL_CLOSED");
    setDealModal(null);
  };

  const confirmDecline = async () => {
    if (!declineModal) return;
    await updateLead(declineModal.lead.id, {
      status: "NOT_INTERESTED",
      decline_reason: declineModal.reason || "No reason given",
    }, "NOT_INTERESTED");
    setSkippedIds(prev => new Set(prev).add(declineModal.lead.id));
    setDeclineModal(null);
  };

  const scoreColor = (score) => score >= 71 ? "#ff4d00" : score >= 41 ? "#f5a623" : "#4a9eff";

  const queueList = leads
    .filter(l => ["NEW", "CONTACTED", "CALLBACK"].includes(l.status) && !skippedIds.has(l.id))
    .sort((a, b) => (b.score || 0) - (a.score || 0));
  const currentQueueLead = queueList[0] || null;

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "32px 16px" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: "monospace", fontSize: 10, color: "#ff4d00", letterSpacing: 3, marginBottom: 8 }}>AGENT PANEL</div>
        <h1 style={{ fontSize: 28, fontWeight: 800 }}>My Assigned Leads</h1>
        {user?.name && <div style={{ fontFamily: "monospace", fontSize: 11, color: "#555", marginTop: 4 }}>{user.name}</div>}
      </div>

      {stats && (
        <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
          {[
            ["APPELS AUJOURD'HUI", stats.calls_today || 0, "#ff4d00"],
            ["ASSIGNED", stats.total_assigned || 0, "#555"],
            ["CONTACTED", stats.contacted || 0, "#4a9eff"],
            ["INTERESTED", stats.interested || 0, "#22c55e"],
            ["APPOINTMENTS", stats.appointments || 0, "#ff4d00"],
            ["DEALS", stats.deals_closed || 0, "#22c55e"],
          ].map(([l, v, c]) => (
            <div key={l} style={{ background: "#1c1c1c", border: "1px solid #333333", borderRadius: 4, padding: "6px 14px", textAlign: "center" }}>
              <div style={{ fontFamily: "monospace", fontSize: 18, fontWeight: 800, color: c }}>{v}</div>
              <div style={{ fontFamily: "monospace", fontSize: 9, color: "#444", letterSpacing: 2 }}>{l}</div>
            </div>
          ))}
        </div>
      )}

      {/* Mode toggle + area filter */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16, alignItems: "center" }}>
        <ActionBtn onClick={() => setViewMode("queue")} disabled={false} highlight={viewMode === "queue"}>📞 File d'appel</ActionBtn>
        <ActionBtn onClick={() => setViewMode("list")} disabled={false} highlight={viewMode === "list"}>☰ Liste</ActionBtn>

        <div style={{ width: 1, height: 20, background: "#333", margin: "0 4px" }} />

        <select value={governorate} onChange={(e) => { setGovernorate(e.target.value); setDelegation(""); }}
          style={{ background: "#161616", border: "1px solid #3a3a3a", color: "#ccc", borderRadius: 3, padding: "5px 8px", fontFamily: "monospace", fontSize: 10 }}>
          <option value="">Tous les gouvernorats</option>
          {Object.keys(locations).map(g => <option key={g} value={g}>{g}</option>)}
        </select>

        {governorate && (
          <select value={delegation} onChange={(e) => setDelegation(e.target.value)}
            style={{ background: "#161616", border: "1px solid #3a3a3a", color: "#ccc", borderRadius: 3, padding: "5px 8px", fontFamily: "monospace", fontSize: 10 }}>
            <option value="">Toutes les délégations</option>
            {(locations[governorate] || []).map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        )}

        {viewMode === "queue" && skippedIds.size > 0 && (
          <ActionBtn onClick={resetSkipped} disabled={false}>↺ Revoir les {skippedIds.size} passés</ActionBtn>
        )}
      </div>

      {viewMode === "queue" ? (
        loading ? (
          <div style={{ fontFamily: "monospace", fontSize: 13, color: "#444", textAlign: "center", padding: 40 }}>Loading...</div>
        ) : !currentQueueLead ? (
          <div style={{ fontFamily: "monospace", fontSize: 13, color: "#333", textAlign: "center", padding: 40 }}>
            File d'appel vide. {skippedIds.size > 0 ? "Tout a été traité ou passé pour l'instant." : "Aucun lead à appeler."}
          </div>
        ) : (
          <div style={{ background: "#1c1c1c", border: "1px solid #333333", borderLeft: `4px solid ${scoreColor(currentQueueLead.score)}`, borderRadius: 8, padding: 24, maxWidth: 480, margin: "0 auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
              <div style={{ background: scoreColor(currentQueueLead.score), color: "#fff", fontFamily: "monospace", fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 3 }}>
                SCORE {currentQueueLead.score}
              </div>
              <div style={{ fontFamily: "monospace", fontSize: 10, color: STAGE_COLOR[currentQueueLead.status] || "#555" }}>
                {STAGE_LABEL[currentQueueLead.status] || currentQueueLead.status}
              </div>
            </div>

            <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 6 }}>{currentQueueLead.name}</div>
            <div style={{ fontFamily: "monospace", fontSize: 11, color: "#555", marginBottom: 12 }}>
              {currentQueueLead.category?.toUpperCase()} · {currentQueueLead.city}{currentQueueLead.governorate ? ` (${currentQueueLead.governorate})` : ""}
            </div>
            {currentQueueLead.address && <div style={{ fontSize: 12, color: "#888", marginBottom: 12 }}>{currentQueueLead.address}</div>}

            {currentQueueLead.phone ? (
              <button onClick={() => qCall(currentQueueLead)} style={{
                width: "100%", background: "#ff4d00", color: "#fff", border: "none", borderRadius: 6,
                padding: "16px", fontSize: 16, fontWeight: 800, marginBottom: 16, cursor: "pointer",
              }}>
                {isNativeOrMobile ? `📞 Appeler ${currentQueueLead.phone}` : `📋 Copier ${currentQueueLead.phone}`}
              </button>
            ) : (
              <div style={{ fontFamily: "monospace", fontSize: 11, color: "#666", marginBottom: 16 }}>Pas de numéro de téléphone</div>
            )}

            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <ActionBtn onClick={() => qNoAnswer(currentQueueLead)}>Pas de réponse</ActionBtn>
              <ActionBtn onClick={() => qCallback(currentQueueLead)}>Rappeler plus tard</ActionBtn>
              <ActionBtn onClick={() => qInterested(currentQueueLead)}>Intéressé</ActionBtn>
              <ActionBtn danger onClick={() => qDecline(currentQueueLead)}>Pas intéressé</ActionBtn>
            </div>

            <div style={{ fontFamily: "monospace", fontSize: 9, color: "#333", marginTop: 16, textAlign: "center" }}>
              {queueList.length} restant{queueList.length > 1 ? "s" : ""} dans la file
            </div>
          </div>
        )
      ) : loading ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#444", textAlign: "center", padding: 40 }}>Loading...</div>
      ) : leads.length === 0 ? (
        <div style={{ fontFamily: "monospace", fontSize: 13, color: "#333", textAlign: "center", padding: 40 }}>
          No leads assigned yet. Ask back office to assign you leads from the CRM page.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {leads.map((lead) => {
            const busy = busyLeadId === lead.id;
            return (
              <div key={lead.id} style={{ background: "#1c1c1c", border: "1px solid #333333", borderLeft: `3px solid ${scoreColor(lead.score)}`, borderRadius: 6, padding: "14px 18px", opacity: busy ? 0.6 : 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                  <div onClick={() => setSelected(lead)} style={{ cursor: "pointer" }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: "#f0f0f0", marginBottom: 3 }}>{lead.name}</div>
                    <div style={{ fontFamily: "monospace", fontSize: 10, color: "#555" }}>{lead.category?.toUpperCase()} · {lead.city}</div>
                    {lead.phone && <div style={{ fontFamily: "monospace", fontSize: 11, color: "#4a9eff", marginTop: 4 }}>📞 {lead.phone}</div>}
                    {lead.appointment_date && <div style={{ fontFamily: "monospace", fontSize: 11, color: "#ff4d00", marginTop: 2 }}>📅 {new Date(lead.appointment_date).toLocaleString()}</div>}
                    {lead.deal_value && <div style={{ fontFamily: "monospace", fontSize: 11, color: "#22c55e", marginTop: 2 }}>💰 {lead.deal_value} TND</div>}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                    <div style={{ background: scoreColor(lead.score), color: "#fff", fontFamily: "monospace", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 3 }}>
                      {lead.score}
                    </div>
                    <div style={{ fontFamily: "monospace", fontSize: 9, color: STAGE_COLOR[lead.status] || "#555" }}>
                      {STAGE_LABEL[lead.status] || lead.status}
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {lead.status === "NEW" && (
                    <ActionBtn onClick={() => markContacted(lead)} disabled={busy}>Mark Contacted</ActionBtn>
                  )}
                  {lead.status === "CONTACTED" && (
                    <>
                      <ActionBtn onClick={() => markInterested(lead)} disabled={busy}>Interested</ActionBtn>
                      <ActionBtn danger onClick={() => setDeclineModal({ lead, reason: "" })} disabled={busy}>Not Interested</ActionBtn>
                    </>
                  )}
                  {lead.status === "INTERESTED" && (
                    <ActionBtn onClick={() => setAppointment(lead)} disabled={busy}>Set Appointment</ActionBtn>
                  )}
                  {lead.status === "APPOINTMENT_SET" && (
                    <ActionBtn onClick={() => markMeetingDone(lead)} disabled={busy}>Meeting Completed</ActionBtn>
                  )}
                  {lead.status === "MEETING_DONE" && (
                    <ActionBtn onClick={() => markProposalSent(lead)} disabled={busy}>Proposal Sent</ActionBtn>
                  )}
                  {lead.status === "PROPOSAL_SENT" && (
                    <>
                      <ActionBtn onClick={() => setDealModal({ lead, value: "" })} disabled={busy}>Close Deal</ActionBtn>
                      <ActionBtn danger onClick={() => setDeclineModal({ lead, reason: "" })} disabled={busy}>Declined</ActionBtn>
                    </>
                  )}
                  {(lead.status === "DEAL_CLOSED" || lead.status === "NOT_INTERESTED") && (
                    <div style={{ fontFamily: "monospace", fontSize: 10, color: "#444" }}>
                      {lead.status === "DEAL_CLOSED" ? "✓ Closed" : `✕ ${lead.decline_reason || "Declined"}`}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selected && <BusinessPopup biz={selected} onClose={() => setSelected(null)} />}

      {dealModal && (
        <Modal onClose={() => setDealModal(null)} title={`Close deal — ${dealModal.lead.name}`}>
          <input
            type="number"
            placeholder="Deal value (TND)"
            value={dealModal.value}
            onChange={(e) => setDealModal({ ...dealModal, value: e.target.value })}
            style={{ width: "100%", background: "#161616", border: "1px solid #3a3a3a", borderRadius: 4, color: "#f0f0f0", padding: "8px 12px", fontSize: 13, marginBottom: 12 }}
            autoFocus
          />
          <ActionBtn onClick={confirmDeal} disabled={!dealModal.value}>Confirm</ActionBtn>
        </Modal>
      )}

      {declineModal && (
        <Modal onClose={() => setDeclineModal(null)} title={`Decline — ${declineModal.lead.name}`}>
          <input
            type="text"
            placeholder="Reason (e.g. not interested, budget, timing)"
            value={declineModal.reason}
            onChange={(e) => setDeclineModal({ ...declineModal, reason: e.target.value })}
            style={{ width: "100%", background: "#161616", border: "1px solid #3a3a3a", borderRadius: 4, color: "#f0f0f0", padding: "8px 12px", fontSize: 13, marginBottom: 12 }}
            autoFocus
          />
          <ActionBtn danger onClick={confirmDecline}>Confirm</ActionBtn>
        </Modal>
      )}

      {callbackModal && (
        <Modal onClose={() => setCallbackModal(null)} title={`Rappeler — ${callbackModal.lead.name}`}>
          <input
            type="datetime-local"
            value={callbackModal.when}
            onChange={(e) => setCallbackModal({ ...callbackModal, when: e.target.value })}
            style={{ width: "100%", background: "#161616", border: "1px solid #3a3a3a", borderRadius: 4, color: "#f0f0f0", padding: "8px 12px", fontSize: 13, marginBottom: 12 }}
            autoFocus
          />
          <ActionBtn onClick={confirmCallback} disabled={!callbackModal.when}>Confirm</ActionBtn>
        </Modal>
      )}
    </div>
  );
}

function ActionBtn({ children, onClick, disabled, danger, highlight }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      background: highlight ? "#ff4d00" : "transparent",
      border: `1px solid ${danger ? "#ef444466" : highlight ? "#ff4d00" : "#3a3a3a"}`,
      color: highlight ? "#fff" : danger ? "#ef4444" : "#ccc",
      borderRadius: 3, padding: "5px 12px", fontFamily: "monospace", fontSize: 10,
      cursor: disabled ? "default" : "pointer", letterSpacing: 1,
    }}>{children}</button>
  );
}

function Modal({ children, onClose, title }) {
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: 16 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: "#1c1c1c", border: "1px solid #333", borderRadius: 8, padding: 20, width: "100%", maxWidth: 360 }}>
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 14 }}>{title}</div>
        {children}
      </div>
    </div>
  );
}
