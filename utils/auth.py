import os
from flask import request, abort

def require_admin():
    """Require admin authentication for protected routes"""
    admin_token = os.environ.get("ADMIN_TOKEN", "")
    token = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ","").strip()
    if not admin_token or token != admin_token:
        abort(401)
