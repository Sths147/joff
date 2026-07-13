"""Flask JSON API for the joff pipeline (fetch latest JO, global/thematic summary).

Served in production by gunicorn (see backend/Dockerfile), not app.run().

CORS is enabled for all origins since this is a personal tool served on
localhost only (see ADR 0005) — there's no session/credential leakage risk
worth restricting origins over.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

import jobs
from errors import PipelineError
from pipeline import (
    get_profile,
    global_summary,
    personalized_summary,
    save_profile,
    thematic_summary,
)

app = Flask(__name__)
CORS(app)


@app.errorhandler(PipelineError)
def handle_pipeline_error(err):
    return jsonify({"error": str(err)}), err.status


@app.post("/jo/latest")
def post_latest_jo():
    """Start (or observe an already-running) fetch of the latest JO.

    Returns immediately with the job's current status — see ADR 0006. Poll
    GET /jo/latest/status for the result.
    """
    return jsonify(jobs.start_fetch_latest_jo()), 202


@app.get("/jo/latest/status")
def get_latest_jo_status():
    return jsonify(jobs.get_status())


@app.get("/jo/latest/summary")
def get_latest_summary():
    topic = request.args.get("topic")
    personalized = request.args.get("personalized")
    if topic:
        k = request.args.get("k", default=10, type=int)
        min_score = request.args.get("min_score", default=0.83, type=float)
        summary = thematic_summary(topic, k, min_score)
    elif personalized:
        summary = personalized_summary()
    else:
        summary = global_summary()
    return jsonify({"summary": summary})


@app.get("/profile")
def get_profile_endpoint():
    return jsonify({"bio": get_profile()})


@app.put("/profile")
def put_profile_endpoint():
    bio = (request.get_json(silent=True) or {}).get("bio", "")
    return jsonify({"bio": save_profile(bio)})
