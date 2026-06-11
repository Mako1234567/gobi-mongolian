"""
Gobi Local Server — TTS + Claude API proxy
Run this once before opening the quiz:
    python tts_server.py

Requirements: pip install edge-tts flask flask-cors requests
"""

import asyncio
import io
import json
import requests
import edge_tts
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

VOICE  = "mn-MN-YesuiNeural"
RATE   = "-10%"
VOLUME = "+0%"

# ── TTS ───────────────────────────────────────────────────────────────────
@app.route("/tts")
def tts():
    text = request.args.get("text", "").strip()
    if not text:
        return Response("No text provided", status=400)
    audio = asyncio.run(generate_audio(text))
    return Response(audio, mimetype="audio/mpeg",
                    headers={"Cache-Control": "public, max-age=3600",
                             "Access-Control-Allow-Origin": "*"})

async def generate_audio(text):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, volume=VOLUME)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()

# ── Claude API proxy ──────────────────────────────────────────────────────
@app.route("/claude", methods=["POST", "OPTIONS"])
def claude_proxy():
    if request.method == "OPTIONS":
        return Response("", status=200,
                        headers={"Access-Control-Allow-Origin": "*",
                                 "Access-Control-Allow-Headers": "Content-Type, x-api-key",
                                 "Access-Control-Allow-Methods": "POST"})
    api_key = request.headers.get("x-api-key", "")
    if not api_key:
        return jsonify({"error": "No API key provided"}), 400

    try:
        body = request.get_json()
        res = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json=body,
            timeout=30
        )
        return Response(res.content, status=res.status_code,
                        content_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Health ────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return {"status": "ok", "voice": VOICE, "claude_proxy": True}

if __name__ == "__main__":
    print("\n🐻 Gobi Server starting...")
    print(f"   TTS:   http://localhost:5050/tts")
    print(f"   Claude proxy: http://localhost:5050/claude")
    print(f"\n   Keep this running while using the quiz.")
    print(f"   Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=5050, debug=False)
