import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import EventsListPage from "./pages/EventsListPage";
import EventDetailPage from "./pages/EventDetailPage";

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ padding: 24, fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial" }}>
        <header style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
          <h1 style={{ margin: 0 }}>
            <Link to="/" style={{ textDecoration: "none", color: "inherit" }}>
              IVEvents
            </Link>
          </h1>
        </header>

        <div style={{ marginTop: 18 }}>
          <Routes>
            <Route path="/" element={<EventsListPage />} />
            <Route path="/events/:eventId" element={<EventDetailPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}