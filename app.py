import json, os
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

load_dotenv()
BASE = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

app = Flask(__name__, static_folder="static", static_url_path="/static")


def load_portfolio():
    with open(os.path.join(BASE, "portfolio.json"), encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt(p):
    return f"""You are {p['assistant_name']}, the AI assistant on {p['name']}'s portfolio website.
Answer visitors' questions about {p['name']} using ONLY the profile data below.
Be friendly, concise and professional. Speak about {p['name']} in the third person.
If something is not in the data, say you don't have that detail and suggest contacting {p['name']} at {p['email']}.
Never invent projects, employers, dates, skills, metrics or case studies.
Keep answers short (2-5 sentences) unless asked for detail. Plain text only, no markdown symbols.

PROFILE DATA:
{json.dumps(p, indent=2, ensure_ascii=False)}"""


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/profile")
def profile():
    p = load_portfolio()
    keys = ("assistant_name", "name", "title", "suggested_questions")
    return jsonify({k: p.get(k) for k in keys})


@app.post("/api/chat")
def chat():
    if not API_KEY:
        return jsonify(error="OPENROUTER_API_KEY is missing. Add it to your .env file."), 500
    history = (request.get_json(silent=True) or {}).get("messages", [])[-12:]
    history = [m for m in history if m.get("role") in ("user", "assistant") and m.get("content")]
    if not history:
        return jsonify(error="No message received."), 400
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": build_system_prompt(load_portfolio())}] + history,
    }
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        return jsonify(reply=r.json()["choices"][0]["message"]["content"])
    except requests.RequestException as e:
        return jsonify(error=f"OpenRouter request failed: {e}"), 502
    except (KeyError, IndexError):
        return jsonify(error="Unexpected response from OpenRouter."), 502


if __name__ == "__main__":
    app.run(debug=True, port=5000)
