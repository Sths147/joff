"""Flask JSON API for the joff pipeline (fetch latest JO, global/thematic summary).

Served in production by gunicorn (see backend/Dockerfile), not app.run().

Every route requires a logged-in session (see auth.require_auth) — the app sits
behind an nginx reverse proxy that also terminates TLS, so the frontend and
backend are always same-origin (through that proxy in the containerized stack,
through the Vite dev-server proxy locally) and the session cookie is always
first-party. No CORS handling is needed as a result.
"""

from flask import Flask, g, jsonify, request

import jobs
import users_db
from auth import (
    clear_session_cookie,
    issue_token,
    require_auth,
    require_auth_or_cron,
    set_session_cookie,
)
from errors import PipelineError
from pipeline import (
    get_profile,
    global_summary,
    login_user,
    personalized_summary,
    register_user,
    save_profile,
    thematic_summary,
)

app = Flask(__name__)
users_db.init_schema()


@app.errorhandler(PipelineError)
def handle_pipeline_error(err):
    return jsonify({"error": str(err)}), err.status


@app.post("/auth/register")
def post_register():
    body = request.get_json(silent=True) or {}
    user_id, email = register_user(body.get("email"), body.get("password"))
    resp = jsonify({"email": email})
    set_session_cookie(resp, issue_token(user_id))
    return resp, 201


@app.post("/auth/login")
def post_login():
    body = request.get_json(silent=True) or {}
    user_id, email = login_user(body.get("email"), body.get("password"))
    resp = jsonify({"email": email})
    set_session_cookie(resp, issue_token(user_id))
    return resp


@app.post("/auth/logout")
@require_auth
def post_logout():
    resp = jsonify({"ok": True})
    clear_session_cookie(resp)
    return resp


@app.get("/auth/me")
@require_auth
def get_me():
    user = users_db.find_user_by_id(g.user_id)
    return jsonify({"email": user["email"]})


@app.post("/jo/latest")
@require_auth_or_cron
def post_latest_jo():
    """Start (or observe an already-running) fetch of the latest JO.

    Returns immediately with the job's current status — see ADR 0006. Poll
    GET /jo/latest/status for the result.
    """
    return jsonify(jobs.start_fetch_latest_jo()), 202


@app.get("/jo/latest/status")
@require_auth
def get_latest_jo_status():
    return jsonify(jobs.get_status())


@app.get("/jo/latest/summary")
@require_auth
def get_latest_summary():
    topic = request.args.get("topic")
    personalized = request.args.get("personalized")
    if topic:
        k = request.args.get("k", default=10, type=int)
        min_score = request.args.get("min_score", default=0.83, type=float)
        summary = thematic_summary(topic, k, min_score)
    elif personalized:
        summary = personalized_summary(g.user_id)
    else:
        summary = global_summary()
    return jsonify({"summary": summary})


@app.get("/profile")
@require_auth
def get_profile_endpoint():
    return jsonify({"bio": get_profile(g.user_id)})


@app.put("/profile")
@require_auth
def put_profile_endpoint():
    bio = (request.get_json(silent=True) or {}).get("bio", "")
    return jsonify({"bio": save_profile(g.user_id, bio)})
