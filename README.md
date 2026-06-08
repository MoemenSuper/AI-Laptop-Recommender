# AI Laptop Recommender

Flask-based laptop recommendation app that combines:

- a web UI for laptop search and recommendations
- TechSpecs API lookups for live product data
- a CSV fallback dataset when the API is unavailable or rate-limited
- a Groq-powered chat assistant for conversational laptop advice
- lightweight conversation memory for context-aware replies

## What It Does

The app helps users find laptops by:

- use case, such as gaming, business, or student work
- direct keyword search
- brand preference
- budget filtering

If the TechSpecs API fails or hits its limit, the app falls back to the local dataset in `laptop_specs_enhanced.csv` so the interface still returns results.

## Features

- Laptop recommendation form
- Search endpoint for specific laptop queries
- Chat assistant for natural-language questions
- API status indicator in the frontend
- CSV fallback mode with fuzzy search
- Conversation memory with session cleanup and limits
- Prompt-tuned AI responses for laptop buying guidance

## Project Structure

- `app.py` - main Flask application, API integration, CSV fallback, and chat endpoints
- `ai_training_system.py` - laptop-specific system prompts and prompt-building helpers
- `conversation_memory.py` - session memory and context utilities for the chatbot
- `templates/index.html` - browser UI and frontend JavaScript
- `laptop_specs_enhanced.csv` - primary fallback dataset used by the app
- `laptop_specs.csv` - alternate/older laptop dataset
- `laptop_code.py` - earlier prototype/alternate implementation

## Requirements

- Python 3.10+ recommended
- Internet access for the TechSpecs and Groq API integrations
- Python packages:
  - `flask`
  - `requests`
  - `pandas`
  - `fuzzywuzzy`

Optional but useful:

- `python-Levenshtein` for faster fuzzy matching

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install flask requests pandas fuzzywuzzy
```

3. Update API credentials in `app.py` if needed.

   The current code reads the TechSpecs and Groq credentials directly from constants in `app.py`, so make sure they are valid before running the app.

4. Start the Flask app:

```bash
python app.py
```

5. Open the app in your browser:

```text
http://127.0.0.1:8080
```

## How It Works

1. The frontend sends requests to the Flask backend.
2. For search and recommendations, the backend tries TechSpecs first.
3. If TechSpecs returns no data or the API limit is reached, the app falls back to `laptop_specs_enhanced.csv`.
4. For chat, the app builds a laptop-focused prompt and sends it to Groq.
5. Conversation memory keeps recent user and assistant messages so follow-up questions stay in context.

## API Endpoints

- `GET /` - main web UI
- `POST /recommend` - get recommendations by usage, budget, and brand
- `POST /search` - search laptops by keyword
- `GET /api-status` - check whether the app is using API mode or CSV fallback
- `POST /reset-api` - reset the API fallback flag
- `GET /memory-stats` - view conversation memory statistics
- `POST /clear-memory` - clear stored conversation sessions
- `POST /chat` - send a message to the chatbot

## Usage Notes

- Keep `laptop_specs_enhanced.csv` in the project root so the fallback loader can find it.
- The chatbot depends on a valid Groq API key.
- The recommendation and search routes can still function in CSV fallback mode even if the TechSpecs API is unavailable.
- For production use, move API keys out of source code and into environment variables.

## Troubleshooting

- If the app starts but returns no laptop results, check that the CSV files are present in the repository root.
- If chat requests fail, verify the Groq API key and network access.
- If the API mode keeps switching to CSV fallback, the TechSpecs quota may have been reached or the API may be unavailable.

## License

No license file is currently included. Add one if you want to publish or share the project publicly.
