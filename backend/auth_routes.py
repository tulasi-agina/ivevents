import os
import uuid
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, make_response

# We import db from app.py because that's where SQLAlchemy() is created.
# This keeps one shared DB instance across the whole app.
from extensions import db

# Import the ORM models (tables)
from models import User, Session


def utcnow():
    """Return timezone-aware UTC timestamp (good practice for DB storage)."""
    return datetime.now(timezone.utc)


# Blueprint groups routes under /auth so app.py stays clean.
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _cookie_settings():
    """
    Central place for cookie security settings.

    - httponly: JS cannot read the cookie (protects against XSS stealing it)
    - samesite=Lax: helps reduce CSRF on most requests
    - secure: cookie only sent over HTTPS (should be True in production)
    - path=/ : cookie applies to the whole site
    """
    # In production you'll be behind HTTPS, so secure should be True.
    # In local dev (HTTP) secure cookies won't work, so we set it False.
    secure = os.getenv("FLASK_ENV") != "development"

    return {
        "httponly": True,
        "secure": secure,
        "samesite": "Lax",
        "path": "/",
    }


def get_current_user():
    """
    Read the session_id cookie, validate it, load session row, enforce:
    - session exists
    - not revoked
    - not expired
    Then return the corresponding User row (or None).
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    # session_id is stored as a UUID string in the cookie.
    # Convert to UUID to avoid invalid input / injection attempts.
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return None

    # Load the session record from DB
    sess = Session.query.filter_by(id=sid).first()
    if not sess:
        return None

    # If we revoked it, treat as logged out
    if sess.revoked_at is not None:
        return None

    # If expired, treat as logged out
    if sess.expires_at <= utcnow():
        return None

    # Load and return the user for this session
    return User.query.filter_by(id=sess.user_id).first()


@auth_bp.post("/login")
def login():
    """
    TEMPORARY DEV LOGIN (replace later with Google OAuth callback)

    Accepts JSON:
      {"email": "user@example.com", "full_name": "User Name"}

    Behavior:
    - Finds or creates the user row
    - Creates a session row (server-side session)
    - Sets a cookie 'session_id' on the client
    """
    data = request.get_json(force=True) or {}

    # Normalize email for consistent uniqueness
    email = (data.get("email") or "").strip().lower()
    full_name = (data.get("full_name") or "").strip() or None

    if not email:
        return jsonify({"ok": False, "error": "email_required"}), 400

    # Find existing user or create new
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, full_name=full_name)
        db.session.add(user)
        db.session.commit()
    else:
        # Optional: keep name updated if provided
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            db.session.commit()

    # Record last login time
    user.last_login_at = utcnow()
    db.session.commit()

    # Create a server-side session row (expires in 7 days)
    sess = Session(
        user_id=user.id,
        created_at=utcnow(),
        expires_at=utcnow() + timedelta(days=7),
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
    )
    db.session.add(sess)
    db.session.commit()

    # Return response and set cookie on client
    resp = make_response(jsonify({"ok": True, "user_id": str(user.id)}))

    # Cookie stores ONLY the session UUID (not the user info).
    # The server uses the cookie to look up the session row.
    resp.set_cookie(
        "session_id",
        str(sess.id),
        max_age=7 * 24 * 3600,  # 7 days in seconds
        **_cookie_settings(),
    )

    return resp


@auth_bp.post("/logout")
def logout():
    """
    Log out by revoking the session in DB and deleting the cookie.

    This is better than "just deleting the cookie" because:
    - you can invalidate sessions server-side
    - you can audit and control sessions
    """
    session_id = request.cookies.get("session_id")

    if session_id:
        try:
            sid = uuid.UUID(session_id)
            sess = Session.query.filter_by(id=sid).first()
            if sess and sess.revoked_at is None:
                sess.revoked_at = utcnow()
                db.session.commit()
        except ValueError:
            # If cookie is malformed, just ignore and delete it anyway
            pass

    resp = make_response(jsonify({"ok": True}))
    resp.delete_cookie("session_id", path="/")
    return resp


@auth_bp.get("/me")
def me():
    """
    Return current logged-in user info if session cookie is valid.
    Useful for frontend to check if user is logged in.
    """
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    return jsonify(
        {
            "ok": True,
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
        }
    )


@auth_bp.get("/login-dev")
def login_dev_get():
    # Browser-friendly: address bar uses GET
    return login_dev()


@auth_bp.post("/login-dev")
def login_dev():
    """
    DEV ONLY: creates a session for a test user and sets session_id cookie.

    Call from browser:
      POST /auth/login-dev
    """
    # Create (or reuse) a predictable dev user
    email = "dev@ivevents.local"
    full_name = "Dev User"

    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, full_name=full_name)
        db.session.add(user)
        db.session.commit()

    # Create a new session row
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session = Session(user_id=user.id, expires_at=expires_at)

    db.session.add(session)
    db.session.commit()

    resp = jsonify({"ok": True, "user_id": str(user.id), "session_id": str(session.id)})

    # Set cookie so the browser will send it automatically next requests
    resp.set_cookie(
        "session_id",
        str(session.id),
        httponly=True,
        samesite="Lax",
        secure=False,  # dev via localhost tunnel
        path="/",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    return resp
