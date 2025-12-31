from datetime import datetime, timezone
from uuid import  UUID
from flask import Blueprint, request, jsonify

from extensions import db
from auth_routes import get_current_user
from models import Event, EventParticipant


events_bp = Blueprint("events", __name__, url_prefix="/events")


def parse_iso_datetime(s: str):
    # Accepts ISO 8601 strings like: "2025-12-24T23:00:00Z"
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


@events_bp.post("")
def create_event():
    """
    Create an event as the current logged-in user.
    JSON:
      {
        "title": "...",
        "description": "...",
        "starts_at": "2025-12-24T23:00:00Z",
        "ends_at": "2025-12-25T00:00:00Z"
      }
    """
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip() or None

    if not title:
        return jsonify({"ok": False, "error": "title_required"}), 400

    starts_at_raw = data.get("starts_at")
    if not starts_at_raw:
        return jsonify({"ok": False, "error": "starts_at_required"}), 400

    starts_at = parse_iso_datetime(starts_at_raw)
    ends_at_raw = data.get("ends_at")
    ends_at = parse_iso_datetime(ends_at_raw) if ends_at_raw else None

    ev = Event(
        title=title,
        description=description,
        starts_at=starts_at,
        ends_at=ends_at,
        created_by_user_id=user.id,
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(ev)
    db.session.commit()

    # Add creator as host automatically
    link = EventParticipant(event_id=ev.id, user_id=user.id, role="host", rsvp_status="going")
    db.session.add(link)
    db.session.commit()

    return jsonify({"ok": True, "event_id": str(ev.id)}), 201


@events_bp.post("/<event_id>/rsvp")
def rsvp(event_id):
    """
    RSVP the current user to an event.
    JSON: {"status":"going" | "maybe" | "no"}
    """
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(force=True) or {}
    status = (data.get("status") or "").strip().lower()
    if status not in {"going", "maybe", "no"}:
        return jsonify({"ok": False, "error": "invalid_status"}), 400

    link = EventParticipant.query.filter_by(event_id=event_id, user_id=user.id).first()
    if link is None:
        link = EventParticipant(event_id=event_id, user_id=user.id, role="attendee", rsvp_status=status)
        db.session.add(link)
    else:
        link.rsvp_status = status

    db.session.commit()
    return jsonify({"ok": True, "event_id": event_id, "status": status})

@events_bp.get("")
def list_events():
    """
    List upcoming events (simple feed).
    Query params (optional):
      - limit (default 25, max 100)
      - mine=true  -> only events the current user is participating in
    """
    user = get_current_user()  # can be None for public feed (optional)
    limit = min(int(request.args.get("limit", 25)), 100)
    mine = (request.args.get("mine") or "").lower() == "true"

    now = datetime.now(timezone.utc)

    q = Event.query.filter(Event.starts_at >= now).order_by(Event.starts_at.asc())

    if mine:
        if not user:
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        q = (
            q.join(EventParticipant, EventParticipant.event_id == Event.id)
             .filter(EventParticipant.user_id == user.id)
        )

    events = q.limit(limit).all()

    # For each event, include participant count and (if logged in) my RSVP
    results = []
    for ev in events:
        count = EventParticipant.query.filter_by(event_id=ev.id).count()

        my_rsvp = None
        if user:
            link = EventParticipant.query.filter_by(event_id=ev.id, user_id=user.id).first()
            if link:
                my_rsvp = link.rsvp_status

        results.append(
            {
                "id": str(ev.id),
                "title": ev.title,
                "description": ev.description,
                "starts_at": ev.starts_at.isoformat(),
                "ends_at": ev.ends_at.isoformat() if ev.ends_at else None,
                "created_by_user_id": str(ev.created_by_user_id) if ev.created_by_user_id else None,
                "participant_count": count,
                "my_rsvp": my_rsvp,  # null if not logged in or not participating
            }
        )

    return jsonify({"ok": True, "events": results})


@events_bp.get("/mine")
def my_events():
    """
    Return:
      - events I created
      - events I'm participating in
    """
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    created = (
        Event.query.filter_by(created_by_user_id=user.id)
        .order_by(Event.starts_at.desc())
        .limit(100)
        .all()
    )

    participating = (
        Event.query.join(EventParticipant, EventParticipant.event_id == Event.id)
        .filter(EventParticipant.user_id == user.id)
        .order_by(Event.starts_at.desc())
        .limit(100)
        .all()
    )

    def serialize(ev: Event):
        return {
            "id": str(ev.id),
            "title": ev.title,
            "starts_at": ev.starts_at.isoformat(),
            "ends_at": ev.ends_at.isoformat() if ev.ends_at else None,
        }

    return jsonify(
        {
            "ok": True,
            "created": [serialize(e) for e in created],
            "participating": [serialize(e) for e in participating],
        }
    )


@events_bp.get("/<event_id>")
def event_detail(event_id):
    """
    Event details + participant list + (if logged in) my participation.
    """
    # Validate UUID format early (clean 400 vs 500)
    try:
        UUID(event_id)
    except ValueError:
        return jsonify({"ok": False, "error": "invalid_event_id"}), 400

    user = get_current_user()  # may be None
    ev = Event.query.filter_by(id=event_id).first()
    if not ev:
        return jsonify({"ok": False, "error": "not_found"}), 404

    links = EventParticipant.query.filter_by(event_id=ev.id).all()

    participants = []
    my_participation = None

    for link in links:
        participants.append(
            {
                "user_id": str(link.user_id),
                "role": link.role,
                "rsvp_status": link.rsvp_status,
            }
        )
        if user and str(link.user_id) == str(user.id):
            my_participation = {"role": link.role, "rsvp_status": link.rsvp_status}

    return jsonify(
        {
            "ok": True,
            "event": {
                "id": str(ev.id),
                "title": ev.title,
                "description": ev.description,
                "starts_at": ev.starts_at.isoformat(),
                "ends_at": ev.ends_at.isoformat() if ev.ends_at else None,
                "created_by_user_id": str(ev.created_by_user_id) if ev.created_by_user_id else None,
                "participant_count": len(participants),
            },
            "participants": participants,
            "my_participation": my_participation,  # null if not logged in / not participating
        }
    )
