from flask import Blueprint, request

debug_bp = Blueprint("debug", __name__, url_prefix="/debug")


@debug_bp.get("")
def index():
    """
    Simple HTML page that links to your endpoints.
    Uses the browser cookie automatically, so /auth/me etc work in-browser after login.
    """
    base = request.host_url.rstrip("/")
    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>IVEvents Debug</title>
        <style>
          body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; padding: 24px; }}
          code {{ background: #f3f3f3; padding: 2px 6px; border-radius: 6px; }}
          a {{ display: inline-block; margin: 6px 0; }}
        </style>
      </head>
      <body>
        <h1>IVEvents API Viewer</h1>

        <h2>Auth</h2>
        <div><a href="{base}/auth/me" target="_blank">GET /auth/me</a></div>

        <h2>Events</h2>
        <div><a href="{base}/events" target="_blank">GET /events</a> <code>(feed)</code></div>
        <div><a href="{base}/events/mine" target="_blank">GET /events/mine</a> <code>(requires login cookie)</code></div>

        <h2>Preferences</h2>
        <div><a href="{base}/preferences/me" target="_blank">GET /preferences/me</a> <code>(requires login cookie)</code></div>

        <h2>Create / Update (use curl)</h2>
        <p>Browser links are great for GETs. For POST/PUT, use curl from EC2 with <code>-b cookies.txt</code>.</p>
      </body>
    </html>
    """
    return html
