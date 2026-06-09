"""
Mongolian TTS Local Server
Run this once before opening the quiz:
    python tts_server.py

Then open mongolian_quiz.html in your browser.
The quiz will automatically use the mn-MN-YesuiNeural voice.

Requirements: pip install edge-tts flask flask-cors
"""

import asyncio
import io
import edge_tts
from flask import Flask, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow the quiz HTML to call this server

VOICE = "mn-MN-YesuiNeural"  # Best Mongolian neural voice
RATE  = "-10%"                # Slightly slower for learning
VOLUME = "+0%"

@app.route("/tts")
def tts():
    text = request.args.get("text", "").strip()
    if not text:
        return Response("No text provided", status=400)

    # Run edge-tts async in sync context
    audio = asyncio.run(generate_audio(text))
    return Response(
        audio,
        mimetype="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )

async def generate_audio(text):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, volume=VOLUME)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()

@app.route("/voices")
def voices():
    """List available Mongolian voices"""
    async def get_voices():
        return await edge_tts.list_voices()
    all_voices = asyncio.run(get_voices())
    mn_voices = [v for v in all_voices if v["Locale"].startswith("mn")]
    return {"voices": mn_voices}

@app.route("/health")
def health():
    return {"status": "ok", "voice": VOICE}

if __name__ == "__main__":
    print("\n🐻 Gobi TTS Server starting...")
    print(f"   Voice: {VOICE}")
    print(f"   URL:   http://localhost:5050")
    print(f"\n   Keep this running while using the quiz.")
    print(f"   Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=5050, debug=False)
