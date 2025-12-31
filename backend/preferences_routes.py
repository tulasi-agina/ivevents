"""
preferences_routes.py

Purpose:
- Store and retrieve each user's event preferences from the database (RDS Postgres).
- Provides two endpoints:
    GET  /preferences/me  -> read current user's preferences (creates default row if missing)
    PUT  /preferences/me  -> update current user's preferences

Notes:
- Uses server-side sessions via get_current_user() (reads session_id cookie -> sessions table -> users table).
- Preferences are stored in the user_preferences table (UserPreference model).
"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from extensions import db
from auth_routes import get_current_user
from models import UserPreference

# Create a Blueprint so these routes can be registered cleanly in app.py.
# All routes in this file will be under /preferences/...
prefs_bp = Blueprint("preferences", __name__, url_prefix="/preferences")


def utcnow():
    """Timezone-aware UTC timestamp for updated_at."""
    return datetime.now(timezone.utc)


@prefs_bp.get("/me")
def get_my_preferences():
    """
    GET /preferences/me

    What it does:
    - Requires the user to be logged in (valid session cookie).
    - Looks up the user's preferences row in user_preferences.
    - If none exists yet, it creates a default preferences row so the frontend
      always receives a consistent JSON shape.

    Response example:
    {
      "ok": true,
      "preferences": {
        "preferred_tags": ["music", "sports"],
        "preferred_days": ["fri", "sat"],
        "preferred_time_window": "evening"
      }
    }
    """
    # Identify current user using the session_id cookie (server-side session table).
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    # Fetch preferences for this user (1-to-1 via user_id primary key).
    pref = UserPreference.query.filter_by(user_id=user.id).first()

    # If this is the user's first time, create a default row.
    if pref is None:
        pref = UserPreference(
            user_id=user.id,
            preferred_tags=[],
            preferred_days=[],
            preferred_time_window=None,
        )
        db.session.add(pref)
        db.session.commit()

    # Return preferences (guarantee lists even if null-ish somehow).
    return jsonify(
        {
            "ok": True,
            "preferences": {
                "preferred_tags": pref.preferred_tags or [],
                "preferred_days": pref.preferred_days or [],
                "preferred_time_window": pref.preferred_time_window,
            },
        }
    )


@prefs_bp.put("/me")
def update_my_preferences():
    """
    PUT /preferences/me

    What it does:
    - Requires login.
    - Accepts a JSON body with any subset of the supported fields.
    - Validates types and allowed values.
    - Updates only what was provided.
    - Saves to Postgres.

    JSON body example:
    {
      "preferred_tags": ["music", "sports"],
      "preferred_days": ["fri", "sat"],
      "preferred_time_window": "evening"
    }

    Rules:
    - preferred_tags: list of strings
    - preferred_days: list of strings
    - preferred_time_window: one of {"morning","afternoon","evening","night"} or null
    """
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    # Parse request JSON (force=True means it will attempt JSON parsing even if headers are imperfect)
    data = request.get_json(force=True) or {}

    # Load row (or create if missing)
    pref = UserPreference.query.filter_by(user_id=user.id).first()
    if pref is None:
        pref = UserPreference(
            user_id=user.id,
            preferred_tags=[],
            preferred_days=[],
            preferred_time_window=None,
        )
        db.session.add(pref)

    # -------- preferred_tags --------
    if "preferred_tags" in data:
        tags = data["preferred_tags"]

        # Validate: must be list[str]
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            return jsonify({"ok": False, "error": "preferred_tags_must_be_list_of_strings"}), 400

        # Normalize: trim + lowercase + drop empty
        pref.preferred_tags = [t.strip().lower() for t in tags if t.strip()]

    # -------- preferred_days --------
    if "preferred_days" in data:
        days = data["preferred_days"]

        # Validate: must be list[str]
        if not isinstance(days, list) or not all(isinstance(d, str) for d in days):
            return jsonify({"ok": False, "error": "preferred_days_must_be_list_of_strings"}), 400

        # Normalize: trim + lowercase + drop empty
        pref.preferred_days = [d.strip().lower() for d in days if d.strip()]

    # -------- preferred_time_window --------
    if "preferred_time_window" in data:
        tw = data["preferred_time_window"]

        # Allow null to "clear" the setting
        allowed = {"morning", "afternoon", "evening", "night"}
        if tw is not None and tw not in allowed:
            return jsonify({"ok": False, "error": "invalid_preferred_time_window"}), 400

        pref.preferred_time_window = tw

    # Update timestamp and commit
    pref.updated_at = utcnow()
    db.session.commit()

    return jsonify({"ok": True})
