import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GEMINI_BASE = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key="
)


def call_gemini(prompt: str) -> str:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    url = GEMINI_BASE + api_key
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    return result["candidates"][0]["content"]["parts"][0]["text"]


def parse_json_response(text: str):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        inner = []
        in_block = False
        for line in lines:
            if line.startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                inner.append(line)
        text = "\n".join(inner).strip()
    return json.loads(text)


def gemini_error_response(e: Exception):
    msg = str(e)
    if "429" in msg:
        return jsonify({"error": "Rate limit exceeded. Please try again shortly."}), 429
    if "401" in msg or "403" in msg:
        return jsonify({"error": "Invalid or unauthorized API key."}), 401
    return jsonify({"error": f"Gemini API error: {msg}"}), 502


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    message = data.get("message", "")
    if not message:
        return jsonify({"error": "Missing 'message' field"}), 400

    if not os.environ.get("GOOGLE_API_KEY"):
        return jsonify({"error": "GOOGLE_API_KEY not configured"}), 500

    prompt = (
        "You are Hyeko, a friendly AI learning mentor. Be warm and concise 3-5 sentences. Student: "
        + message
    )
    try:
        text = call_gemini(prompt)
    except Exception as e:
        return gemini_error_response(e)
    return jsonify({"status": "ok", "reply": text})


@app.route("/api/generate-mindmap", methods=["POST"])
def generate_mindmap():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    topic = data.get("topic", "")
    if not topic:
        return jsonify({"error": "Missing 'topic' field"}), 400

    if not os.environ.get("GOOGLE_API_KEY"):
        return jsonify({"error": "GOOGLE_API_KEY not configured"}), 500

    prompt = (
        f"Create a mind map about {topic}. "
        "Return ONLY valid JSON: {\"central\": topic, \"branches\": [{\"name\": ..., \"sub_branches\": [...]}]} "
        "with 5 branches. No markdown, no explanation, just raw JSON."
    )
    try:
        text = call_gemini(prompt)
        mindmap = parse_json_response(text)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse mind map JSON from AI response", "raw": text}), 502
    except Exception as e:
        return gemini_error_response(e)
    return jsonify({"status": "ok", "mindmap": mindmap})


@app.route("/api/generate-timetable", methods=["POST"])
def generate_timetable():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    topics = data.get("topics", "")
    hours_per_day = data.get("hours_per_day", data.get("hours", 2))
    if not topics:
        return jsonify({"error": "Missing 'topics' field"}), 400

    if not os.environ.get("GOOGLE_API_KEY"):
        return jsonify({"error": "GOOGLE_API_KEY not configured"}), 500

    prompt = (
        f"Create 7 day study timetable for topics:{topics} hours:{hours_per_day}. "
        "Return ONLY valid JSON: {\"weekly_plan\": [{\"day\": ..., \"sessions\": [{\"time\": ..., \"topic\": ..., \"activity\": ...}]}], "
        "\"recommendations\": [...]}. No markdown, no explanation, just raw JSON."
    )
    try:
        text = call_gemini(prompt)
        timetable = parse_json_response(text)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse timetable JSON from AI response", "raw": text}), 502
    except Exception as e:
        return gemini_error_response(e)
    return jsonify({"status": "ok", "timetable": timetable})


@app.route("/api/quiz/generate", methods=["POST"])
def quiz_generate():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    topic = data.get("topic", "")
    if not topic:
        return jsonify({"error": "Missing 'topic' field"}), 400

    if not os.environ.get("GOOGLE_API_KEY"):
        return jsonify({"error": "GOOGLE_API_KEY not configured"}), 500

    prompt = (
        f"Create 3 quiz questions about {topic}. "
        "Return ONLY valid JSON: {\"questions\": [{\"question\": ..., \"options\": [4 options], \"correct\": 0-3, \"xp\": 15}]}. "
        "No markdown, no explanation, just raw JSON."
    )
    try:
        text = call_gemini(prompt)
        quiz = parse_json_response(text)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse quiz JSON from AI response", "raw": text}), 502
    except Exception as e:
        return gemini_error_response(e)
    return jsonify({"status": "ok", "quiz": quiz})


@app.route("/api/visual-notes", methods=["POST"])
def visual_notes():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    topic = data.get("topic", "")
    if not topic:
        return jsonify({"error": "Missing 'topic' field"}), 400

    if not os.environ.get("GOOGLE_API_KEY"):
        return jsonify({"error": "GOOGLE_API_KEY not configured"}), 500

    prompt = (
        f"Create structured visual study notes for {topic}. "
        "Include key concepts, how it works, why it matters, memory tips. "
        "Use emojis and bullet points."
    )
    try:
        text = call_gemini(prompt)
    except Exception as e:
        return gemini_error_response(e)
    return jsonify({"status": "ok", "notes": text})


@app.route("/api/visual-animation", methods=["POST"])
def visual_animation():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    topic = data.get("topic", "")
    if not topic:
        return jsonify({"error": "Missing 'topic' field"}), 400

    if not os.environ.get("GOOGLE_API_KEY"):
        return jsonify({"error": "GOOGLE_API_KEY not configured"}), 500

    prompt = (
        f"Create a step by step visual explanation of {topic} with 5 steps. "
        "Return ONLY valid JSON: {\"steps\": [{\"step_number\": 1, \"title\": ..., \"description\": ..., \"emoji\": ...}]}. "
        "No markdown, no explanation, just raw JSON."
    )
    try:
        text = call_gemini(prompt)
        animation = parse_json_response(text)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse animation JSON from AI response", "raw": text}), 502
    except Exception as e:
        return gemini_error_response(e)
    return jsonify({"status": "ok", "animation": animation})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
