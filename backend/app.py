from flask import Flask, jsonify, render_template, request, send_from_directory

from .ai_training_system import create_enhanced_prompt
from .chat_intent import analyze_user_intent_and_get_data, get_fallback_response
from .config import (
    ASSETS_FOLDER,
    CSV_FILE_PATH,
    DASHBOARD_FOLDER,
    GROQ_API_KEY,
    GROQ_BASE_URL,
    INTRO_FOLDER,
    TECHSPECS_CONFIG,
)
from .conversation_memory import ConversationMemory
from .groq_client import GroqClient
from .laptop_catalog import LaptopCatalog


app = Flask(__name__, template_folder=str(DASHBOARD_FOLDER))

catalog = LaptopCatalog(CSV_FILE_PATH, TECHSPECS_CONFIG)
groq_client = GroqClient(GROQ_API_KEY, GROQ_BASE_URL)
conversation_memory = ConversationMemory(
    max_messages=10,
    session_timeout_minutes=30,
    max_sessions=25,
    max_memory_mb=50,
)

if groq_client.configured:
    print("Groq AI configured.")
else:
    print("Groq API key not configured.")


def parse_optional_int(value):
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def query_for_usage(usage):
    return {
        "gaming": "gaming laptop",
        "business": "business laptop",
        "student": "budget laptop",
    }.get(usage, "laptop")


@app.route("/")
def home():
    return send_from_directory(INTRO_FOLDER, "mainpage.html")


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


@app.route("/mainpage.css")
def mainpage_styles():
    return send_from_directory(INTRO_FOLDER, "mainpage.css")


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(ASSETS_FOLDER, filename)


@app.route("/style.css")
def dashboard_styles():
    return send_from_directory(DASHBOARD_FOLDER, "style.css")


@app.route("/controle-et-animation.js")
def dashboard_script():
    return send_from_directory(DASHBOARD_FOLDER, "controle-et-animation.js")


@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json() or {}
        usage = data.get("usage", "general")
        budget = parse_optional_int(data.get("budget"))
        brand = data.get("brand")

        print(f"Recommendation request: usage={usage}, budget={budget}, brand={brand}")
        recommendations = catalog.search(query_for_usage(usage), limit=6, budget=budget, brand=brand)

        return jsonify({"success": True, "recommendations": recommendations})
    except Exception as error:
        print(f"Recommendation error: {error}")
        return jsonify({"success": False, "error": "Recommendation request failed"})


@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.get_json() or {}
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"success": False, "error": "No search query provided"})

        print(f"Search request: query={query}")
        results = catalog.search(query, limit=8)

        return jsonify({"success": True, "results": results})
    except Exception as error:
        print(f"Search error: {error}")
        return jsonify({"success": False, "error": "Search failed"})


@app.route("/api-status")
def api_status():
    return jsonify(catalog.status())


@app.route("/reset-api", methods=["POST"])
def reset_api():
    catalog.reset_api_limit()
    print("API limit flag reset.")
    status = catalog.status()

    return jsonify({
        "success": True,
        "message": "API limit flag reset",
        "current_mode": status["current_mode"],
    })


@app.route("/memory-stats")
def memory_stats():
    try:
        return jsonify({"success": True, "memory_stats": conversation_memory.get_memory_stats()})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)})


@app.route("/clear-memory", methods=["POST"])
def clear_memory():
    try:
        conversation_memory.clear_all_sessions()
        return jsonify({"success": True, "message": "Conversation memory cleared"})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"success": False, "error": "No message provided"})

        if not groq_client.configured:
            return jsonify({
                "success": False,
                "error": "Groq key missing. Add GROQ_API_KEY to .env.",
            })

        session_id = conversation_memory.get_session_id(request)
        had_previous_messages = conversation_memory.has_messages(session_id)
        print(f"Chat request [{session_id[:8]}]: {user_message}")

        response_data = analyze_user_intent_and_get_data(user_message, catalog)
        conversation_memory.add_message(session_id, "user", user_message)

        try:
            if had_previous_messages:
                history = conversation_memory.get_conversation_history(
                    session_id,
                    include_system_prompt=True,
                )
                ai_response = groq_client.complete_messages(history)
            else:
                prompt = create_enhanced_prompt(user_message, response_data["data"])
                ai_response = groq_client.complete_prompt(prompt)

            if not ai_response:
                ai_response = get_fallback_response(user_message, response_data)

            conversation_memory.add_message(session_id, "assistant", ai_response)
            return jsonify({"success": True, "response": ai_response})
        except Exception as error:
            print(f"AI response error: {error}")
            fallback_response = get_fallback_response(user_message, response_data)
            conversation_memory.add_message(session_id, "assistant", fallback_response)
            return jsonify({"success": True, "response": fallback_response})

    except Exception as error:
        print(f"Chat error: {error}")
        return jsonify({
            "success": False,
            "error": "I could not process that message. Rephrase it.",
        })


if __name__ == "__main__":
    print("Starting Laptop AI Recommender...")
    print("Open your browser and go to: http://localhost:8080")
    app.run(debug=True, port=8080, host="127.0.0.1")
