"""
Gobi TTS Server — works locally and on Render
Local: python tts_server.py
Render: automatically uses PORT env variable
"""

import asyncio
import io
import os
import requests
import edge_tts
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

VOICE  = "mn-MN-YesuiNeural"
RATE   = "-10%"
VOLUME = "+0%"

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
            headers={"Content-Type": "application/json",
                     "x-api-key": api_key,
                     "anthropic-version": "2023-06-01"},
            json=body, timeout=30)
        return Response(res.content, status=res.status_code,
                        content_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok", "voice": VOICE})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    host = "0.0.0.0" if os.environ.get("RENDER") else "127.0.0.1"
    print(f"\n🐻 Gobi Server starting on {host}:{port}")
    app.run(host=host, port=port, debug=False)
