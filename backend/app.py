import os
from flask import Flask
from extensions import db, migrate
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    from models import User, Event, UserPreference  # noqa: F401

    from auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from events_routes import events_bp
    app.register_blueprint(events_bp)

    from preferences_routes import prefs_bp
    app.register_blueprint(prefs_bp)

    from debug_routes import debug_bp
    app.register_blueprint(debug_bp)

    @app.get("/health")
    def health():
        return {"ok": True}


    @app.get("/db-check")
    def db_check():
        # Create or fetch a deterministic test user
        test_email = "db-check@ivevents.local"
        user = User.query.filter_by(email=test_email).first()
        if user is None:
            user = User(email=test_email, full_name="DB Check User")
            db.session.add(user)
            db.session.commit()

        # Create or fetch a deterministic test event
        existing_event = Event.query.filter_by(title="DB Check Event").first()
        if existing_event is None:
            from datetime import datetime, timedelta, timezone
            starts = datetime.now(timezone.utc) + timedelta(minutes=5)
            ends = starts + timedelta(hours=1)

            existing_event = Event(
                title="DB Check Event",
                description="Created by /db-check",
                starts_at=starts,
                ends_at=ends,
                created_by_user_id=user.id,
            )
            db.session.add(existing_event)
            db.session.commit()

        return {
            "ok": True,
            "user_id": str(user.id),
            "event_id": str(existing_event.id),
        }


    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
