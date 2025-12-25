import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { apiGet, apiPost } from "../api";

export default function EventDetailPage() {
  const { eventId } = useParams();

  const [event, setEvent] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [myParticipation, setMyParticipation] = useState(null);

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setErr("");
    try {
      const data = await apiGet(`/events/${eventId}`);
      setEvent(data.event);
      setParticipants(data.participants || []);
      setMyParticipation(data.my_participation || null);
    } catch (e) {
      setErr(e.message || "Failed to load event");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId]);

  async function rsvp(status) {
    try {
      setSaving(true);
      setErr("");
      await apiPost(`/events/${eventId}/rsvp`, { status });
      await load();
    } catch (e) {
      setErr(e.message || "Failed to RSVP");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <Link to="/">← Back to Events</Link>
      </div>

      {loading && <p>Loading…</p>}
      {err && <p style={{ color: "crimson" }}>Error: {err}</p>}

      {!loading && event && (
        <div>
          <h2 style={{ marginTop: 0 }}>{event.title}</h2>

          <div style={{ fontSize: 14, opacity: 0.85, marginBottom: 10 }}>
            <div>Starts: {event.starts_at}</div>
            {event.ends_at && <div>Ends: {event.ends_at}</div>}
            <div>Participants: {event.participant_count}</div>
          </div>

          {event.description && <p style={{ marginTop: 0 }}>{event.description}</p>}

          <div style={{ marginTop: 16, marginBottom: 10 }}>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>My RSVP</div>
            <div style={{ fontSize: 14, marginBottom: 10 }}>
              {myParticipation
                ? `${myParticipation.role} • ${myParticipation.rsvp_status}`
                : "Not participating (or not logged in)."}
            </div>

            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button disabled={saving} onClick={() => rsvp("going")}>Going</button>
              <button disabled={saving} onClick={() => rsvp("maybe")}>Maybe</button>
              <button disabled={saving} onClick={() => rsvp("no")}>Not going</button>
            </div>
          </div>

          <div style={{ marginTop: 18 }}>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>Participants</div>
            {participants.length === 0 ? (
              <p style={{ marginTop: 0 }}>No participants yet.</p>
            ) : (
              <ul style={{ paddingLeft: 18, marginTop: 0 }}>
                {participants.map((p) => (
                  <li key={`${p.user_id}-${p.role}`}>
                    <span style={{ fontFamily: "monospace" }}>{p.user_id.slice(0, 8)}</span>
                    {" — "}
                    {p.role} • {p.rsvp_status}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}