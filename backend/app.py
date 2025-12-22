# backend/app.py
# Flask API server + Google OAuth routes.

import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from auth import auth_bp, init_oauth

# Load environment variables from .env (repo root or backend/.env)
load_dotenv()

app = Flask(__name__)

# Needed for Flask sessions (cookies). Use a long random string in real use.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Cookie settings: Lax is good for OAuth redirects in most cases
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Allow your React dev server to call Flask and include cookies
frontend_origin = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
CORS(app, origins=[frontend_origin], supports_credentials=True)

# Initialize OAuth + register auth blueprint
init_oauth(app)
app.register_blueprint(auth_bp)


@app.get("/api/health")
def health():
    return jsonify({"ok": True})

# Temporary events endpoint for MVP
@app.get("/api/events")
def get_events():
    # Temporary in-memory events for MVP.
    # Later, these will come from PostgreSQL.
    events = [
        {
            "id": 1,
            "title": "Sunset Beach Volleyball",
            "date": "2025-12-28",
            "location": "East Beach, Santa Barbara",
        },
        {
            "id": 2,
            "title": "Local Art Walk",
            "date": "2026-01-03",
            "location": "Downtown SB",
        },
        {
            "id": 3,
            "title": "Coffee & Code Meetup",
            "date": "2026-01-05",
            "location": "Isla Vista",
        },
    ]
    return jsonify({"events": events})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)