import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB

from extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=True)

    # Google OAuth stable subject identifier (recommended)
    google_sub = db.Column(db.String(255), unique=True, nullable=True, index=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)

    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)

    user = db.relationship("User", backref=db.backref("sessions", lazy=True, cascade="all, delete-orphan"))


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    starts_at = db.Column(db.DateTime(timezone=True), nullable=False)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_by_user_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    created_by = db.relationship("User", backref=db.backref("events_created", lazy=True))


class EventParticipant(db.Model):
    __tablename__ = "event_participants"

    event_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role = db.Column(db.String(32), nullable=False, default="attendee")  # attendee | host
    rsvp_status = db.Column(db.String(32), nullable=False, default="going")  # going | maybe | no

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    event = db.relationship("Event", backref=db.backref("participants", lazy=True, cascade="all, delete-orphan"))
    user = db.relationship("User", backref=db.backref("event_memberships", lazy=True, cascade="all, delete-orphan"))

class UserPreference(db.Model):
    __tablename__ = "user_preferences"

    # One-to-one: user_id is both primary key and foreign key
    user_id = db.Column(
        db.Uuid(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Store arrays/objects efficiently in Postgres
    preferred_tags = db.Column(JSONB, nullable=False, default=list)        # e.g. ["music","sports"]
    preferred_days = db.Column(JSONB, nullable=False, default=list)        # e.g. ["fri","sat"]
    preferred_time_window = db.Column(db.String(32), nullable=True)        # e.g. "morning"|"afternoon"|"evening"

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    user = db.relationship("User", backref=db.backref("preferences", uselist=False, cascade="all, delete-orphan"))
