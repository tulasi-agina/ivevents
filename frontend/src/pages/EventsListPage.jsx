import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api";

export default function EventsListPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setErr("");
        const data = await apiGet("/events");
        if (mounted) setEvents(data.events || []);
      } catch (e) {
        if (mounted) setErr(e.message || "Failed to load events");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div>
      {loading && <p>Loading events…</p>}
      {err && <p style={{ color: "crimson" }}>Error: {err}</p>}

      {!loading && !err && events.length === 0 && <p>No upcoming events yet.</p>}

      <ul style={{ paddingLeft: 18 }}>
        {events.map((e) => (
          <li key={e.id} style={{ marginBottom: 12 }}>
            <div style={{ fontWeight: 700 }}>
              <Link to={`/events/${e.id}`}>{e.title}</Link>
            </div>

            <div style={{ fontSize: 14, opacity: 0.8 }}>
              Starts: {e.starts_at}
              {typeof e.participant_count === "number" ? ` • Participants: ${e.participant_count}` : ""}
              {e.my_rsvp ? ` • My RSVP: ${e.my_rsvp}` : ""}
            </div>

            {e.description && <div style={{ fontSize: 14 }}>{e.description}</div>}
          </li>
        ))}
      </ul>
    </div>
  );
}
