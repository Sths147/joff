"""Flask JSON API for the joff pipeline (fetch latest JO, global/thematic summary).

Served in production by gunicorn (see backend/Dockerfile), not app.run().

CORS is enabled for all origins since this is a personal tool served on
localhost only (see ADR 0005) — there's no session/credential leakage risk
worth restricting origins over.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

from errors import PipelineError
from pipeline import fetch_latest_jo, global_summary, thematic_summary

app = Flask(__name__)
CORS(app)


@app.errorhandler(PipelineError)
def handle_pipeline_error(err):
    return jsonify({"error": str(err)}), err.status


@app.post("/jo/latest")
def post_latest_jo():
    return jsonify(fetch_latest_jo())


@app.get("/jo/latest/summary")
def get_latest_summary():
    topic = request.args.get("topic")
    if topic:
        k = request.args.get("k", default=10, type=int)
        min_score = request.args.get("min_score", default=0.83, type=float)
        summary = thematic_summary(topic, k, min_score)
    else:
        summary = global_summary()
    return jsonify({"summary": summary})
