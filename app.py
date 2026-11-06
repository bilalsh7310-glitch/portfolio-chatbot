
import json
import os
import requests

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

# Load environment variables
load_dotenv()

BASE = os.path.dirname(os.path.abspath(__file__))

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
PORT = int(os.getenv("PORT", 10000))

# Flask configuration
app = Flask(
    __name__,
    static_folder=os.path.join(BASE, "static"),
    static_url_path="/static"
)


# Load portfolio information
def load_portfolio():
    portfolio_path = os.path.join(BASE, "portfolio.json")

    with open(portfolio_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Create AI system prompt
def build_system_prompt(p):
    return f"""
You are {p['assistant_name']}, the AI assistant on {p['name']}'s portfolio website.

Answer visitors' questions using ONLY the profile data below.

Rules:
1. Be friendly, concise and professional.
2. Speak about {p['name']} in the third person.
3. Never invent projects, employers, dates, skills or achievements.
4. If information is unavailable, suggest contacting {p['name']} at {p['email']}.
5. Keep answers short, usually 2 to 5 sentences.
6. Use plain text.

PROFILE DATA:
{json.dumps(p, indent=2, ensure_ascii=False)}
"""


# Homepage
@app.get("/")
def index():
    return send_from_directory(BASE + "/static", "index.html")


# Health check
@app.get("/health")
def health():
    return jsonify(status="healthy"), 200


# Profile API
@app.get("/api/profile")
def profile():
    try:
        p = load_portfolio()

        keys = (
            "assistant_name",
            "name",
            "title",
            "suggested_questions"
        )

        return jsonify({k: p.get(k) for k in keys})

    except (FileNotFoundError, json.JSONDecodeError):
        app.logger.exception("Portfolio loading failed")
        return jsonify(error="Portfolio data is unavailable."), 500


# AI Chat API
@app.post("/api/chat")
def chat():

    if not API_KEY:
        return jsonify(
            error="Server configuration error. API key is missing."
        ), 500

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])

    if not isinstance(messages, list):
        return jsonify(error="Invalid messages format."), 400

    # Keep only the latest 12 valid messages
    history = [
        m for m in messages
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
        and m.get("content").strip()
    ][-12:]

    if not history or not any(m["role"] == "user" for m in history):
        return jsonify(error="No valid user message received."), 400

    try:

        portfolio = load_portfolio()

        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": build_system_prompt(portfolio)
                }
            ] + history
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        result = response.json()

        reply = result["choices"][0]["message"]["content"]

        if not isinstance(reply, str) or not reply.strip():
            return jsonify(error="AI returned an empty response."), 502

        return jsonify(reply=reply)

    except requests.Timeout:
        app.logger.exception("OpenRouter request timed out")
        return jsonify(error="AI response timed out. Please try again."), 504

    except requests.RequestException:
        app.logger.exception("OpenRouter API request failed")
        return jsonify(error="Unable to connect to the AI service."), 502

    except (KeyError, IndexError, ValueError):
        app.logger.exception("Invalid OpenRouter response")
        return jsonify(error="Unexpected response from AI service."), 502

    except (FileNotFoundError, json.JSONDecodeError):
        app.logger.exception("Portfolio data error")
        return jsonify(error="Portfolio data could not be loaded."), 500


# Local development
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )
