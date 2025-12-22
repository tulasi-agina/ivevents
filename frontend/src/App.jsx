import { useEffect, useMemo, useState } from "react";

// Backend base URL (you can override with VITE_BACKEND_URL later)
const BACKEND = import.meta.env.VITE_BACKEND_URL || "http://localhost:5000";

export default function App() {
  // Events state + loading/error so you don't show "No events" while loading
  const [events, setEvents] = useState([]);
  const [eventsLoading, setEventsLoading] = useState(true);
  const [eventsError, setEventsError] = useState("");
  const [profileImgOk, setProfileImgOk] = useState(false);

  // Auth state + loading
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  // Build login URL once (stable)
  const loginUrl = useMemo(() => `${BACKEND}/api/auth/google/login?next=/`, []);

  // Fetch current user + events on initial page load
  useEffect(() => {
    // 1) Check logged-in user (session cookie)
    fetch(`${BACKEND}/api/auth/me`, { credentials: "include" })
      .then((r) => r.json())
      .then((data) => setUser(data.user || null))
      .catch(() => setUser(null))
      .finally(() => setAuthChecked(true));

    // 2) Fetch events list
    setEventsLoading(true);
    setEventsError("");

    fetch(`${BACKEND}/api/events`, { credentials: "include" })
      .then(async (r) => {
        // Handle non-200 responses cleanly
        if (!r.ok) {
          const text = await r.text();
          throw new Error(text || `Request failed (${r.status})`);
        }
        return r.json();
      })
      .then((data) => setEvents(Array.isArray(data.events) ? data.events : []))
      .catch(() => {
        setEvents([]);
        setEventsError("Could not load events. Try refreshing.");
      })
      .finally(() => setEventsLoading(false));
  }, []);

  // Logout handler (clears server session + updates UI immediately)
  async function handleLogout() {
    try {
      await fetch(`${BACKEND}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } finally {
      setUser(null);
      setAuthChecked(true);
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: "72px auto", fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 44, marginBottom: 8 }}>IVEvents</h1>

      <p style={{ fontSize: 18, lineHeight: 1.5 }}>
        Discover local events and track what you’re interested in.
      </p>

      {/* Auth status */}
      <div
        style={{
          marginTop: 18,
          padding: 12,
          border: "1px solid #eee",
          borderRadius: 10,
        }}
      >
        {!authChecked ? (
          <div>Checking login…</div>
        ) : user ? (
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 12,
              flexWrap: "wrap",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              {/* Show profile image if available */}
              {user?.picture && profileImgOk ? (
                <img
                  src={user.picture}
                  alt="profile"
                  width="32"
                  height="32"
                  style={{ borderRadius: 16 }}
                />
              ) : null}

              {/* Hidden preloader: tries to load the image once; if it fails, we never show it */}
              {user?.picture ? (
                <img
                  src={user.picture}
                  alt=""
                  style={{ display: "none" }}
                  onLoad={() => setProfileImgOk(true)}
                  onError={() => setProfileImgOk(false)}
                />
              ) : null}


              <div>
                Logged in as <b>{user.name}</b> ({user.email})
              </div>
            </div>

            <button
              onClick={handleLogout}
              style={{
                padding: "8px 12px",
                borderRadius: 10,
                border: "1px solid #ddd",
                cursor: "pointer",
              }}
            >
              Logout
            </button>
          </div>
        ) : (
          <div>Not logged in.</div>
        )}
      </div>

      {/* Auth buttons */}
      <div style={{ display: "flex", gap: 12, marginTop: 28 }}>
        <a href={loginUrl}>
          <button
            style={{
              padding: "12px 16px",
              borderRadius: 10,
              border: "1px solid #ddd",
              cursor: "pointer",
              fontSize: 16,
            }}
          >
            Login with Google
          </button>
        </a>

        <a href={loginUrl}>
          <button
            style={{
              padding: "12px 16px",
              borderRadius: 10,
              border: "1px solid #ddd",
              cursor: "pointer",
              fontSize: 16,
            }}
          >
            Create Account
          </button>
        </a>
      </div>

      {/* Events list */}
      <div style={{ marginTop: 28 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
          <h2 style={{ marginBottom: 10 }}>Upcoming Events</h2>

          {/* Lightweight refresh button */}
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "8px 12px",
              borderRadius: 10,
              border: "1px solid #ddd",
              cursor: "pointer",
            }}
            title="Refresh events"
          >
            Refresh
          </button>
        </div>

        {eventsLoading ? (
          <div>Loading events…</div>
        ) : eventsError ? (
          <div style={{ border: "1px solid #f0f0f0", padding: 12, borderRadius: 10 }}>
            {eventsError}
          </div>
        ) : events.length === 0 ? (
          <div>No events yet.</div>
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {events.map((e) => (
              <div
                key={e.id}
                style={{
                  padding: 14,
                  border: "1px solid #eee",
                  borderRadius: 12,
                }}
              >
                <div style={{ fontSize: 18, fontWeight: 600 }}>{e.title}</div>
                <div style={{ marginTop: 6 }}>{e.date}</div>
                <div style={{ marginTop: 2, color: "#555" }}>{e.location}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}