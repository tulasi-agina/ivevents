# backend/auth.py
# Handles Google OAuth login and callback using Authlib (OpenID Connect).

import secrets
import os
from flask import Blueprint, redirect, url_for, session, request, jsonify
from authlib.integrations.flask_client import OAuth

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

oauth = OAuth()
google = None  # will be registered in init_oauth()


def init_oauth(app):
    """
    Registers the Google OAuth/OpenID Connect client with Flask.
    Reads GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from environment variables.
    """
    global google
    oauth.init_app(app)

    google = oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        # Google OIDC metadata endpoint (gives auth/token/userinfo endpoints)
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        # Request basic identity info
        client_kwargs={"scope": "openid email profile"},
    )


@auth_bp.get("/google/login")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)

    next_url = request.args.get("next", "/")
    session["post_login_redirect"] = next_url

    # Generate a nonce and store it in the session (required for OIDC id_token validation)
    nonce = secrets.token_urlsafe(16)
    session["oidc_nonce"] = nonce

    # Pass nonce to Google
    return google.authorize_redirect(redirect_uri, nonce=nonce)


@auth_bp.get("/google/callback")
def google_callback():
    """
    Handles Google redirect back to us.
    Exchanges code for tokens, reads the user identity (id_token),
    stores the user in the Flask session, then redirects to React.
    """
    token = google.authorize_access_token()
    nonce = session.pop("oidc_nonce", None)
    userinfo = google.parse_id_token(token, nonce)

    # Store minimum info in session (MVP)
    session["user"] = {
        "google_sub": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    }

    frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    next_url = session.pop("post_login_redirect", "/")
    return redirect(f"{frontend_base}{next_url}")


@auth_bp.get("/me")
def me():
    """
    Returns the logged-in user (if any).
    React will call this to see if the user is signed in.
    """
    return jsonify({"user": session.get("user")})


@auth_bp.post("/logout")
def logout():
    """
    Clears the session.
    """
    session.pop("user", None)
    return jsonify({"ok": True})