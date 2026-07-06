"""
Secure Artifact Signing - Aplicação alvo para demonstração.
API REST simples em Flask com dois endpoints.
"""

import os
from flask import Flask, jsonify

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
BUILD_SHA   = os.getenv("BUILD_SHA", "local")


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/version")
def version():
    return jsonify({
        "version":   APP_VERSION,
        "build_sha": BUILD_SHA,
        "signed":    True,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
