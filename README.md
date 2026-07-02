# Laptop Recommender

Flask app for laptop search, recommendations, and laptop buying questions.

## App Job

- Shows an intro video, then opens the laptop recommender dashboard.
- Recommends laptops by use case, budget, and brand.
- Searches a local CSV dataset when live TechSpecs data is unavailable.
- Answers laptop questions with Groq.
- Keeps recent chat messages for follow-up questions.

## Student-Friendly Project Map

Start here:

- `run.py` - starts the Flask app.
- `backend/app.py` - connects browser routes to the backend modules.
- `frontend/intro/mainpage.html` - first page users see.
- `frontend/dashboard/index.html` - main laptop recommender UI.

Backend code:

- `backend/config.py` - reads `.env` values and points to project folders.
- `backend/laptop_catalog.py` - searches TechSpecs first, then the CSV dataset.
- `backend/chat_intent.py` - understands what the user is asking the chatbot.
- `backend/groq_client.py` - sends prompts to Groq.
- `backend/ai_training_system.py` - builds laptop expert prompts.
- `backend/conversation_memory.py` - stores recent chat messages.

Frontend files:

- `frontend/intro/` - intro video page.
- `frontend/dashboard/` - dashboard HTML, CSS, and JavaScript.
- `frontend/login/` - saved login page files.
- `frontend/assets/` - video and media assets.

Data files:

- `data/laptop_specs_enhanced.csv` - main fallback laptop dataset.
- `data/laptop_specs.csv` - older/alternate laptop dataset.

## Runtime Flow

1. `run.py` starts Flask from `backend/app.py`.
2. `/` serves `frontend/intro/mainpage.html`.
3. The intro page reveals `/dashboard`.
4. Dashboard JavaScript calls `/recommend`, `/search`, `/api-status`, and `/chat`.
5. `backend/laptop_catalog.py` returns laptop results.
6. `backend/chat_intent.py` and `backend/groq_client.py` handle chat replies.

## Requirements

- Python 3.10+
- Python packages listed in `requirements.txt`
- Groq API key for chatbot replies
- TechSpecs credentials for live product search

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` into `.env`, then fill in any keys you want to use.

```text
GROQ_API_KEY=
TECHSPECS_API_KEY=
TECHSPECS_API_ID=
TECHSPECS_BASE_URL=https://api.techspecs.io/v5
LAPTOP_CSV_PATH=
```

4. Start the app:

```bash
python run.py
```

5. Open:

```text
http://127.0.0.1:8080
```

## API Endpoints

- `GET /` - intro page
- `GET /dashboard` - recommender dashboard
- `POST /recommend` - recommendations by usage, budget, and brand
- `POST /search` - laptop search by keyword
- `GET /api-status` - current TechSpecs/CSV fallback status
- `POST /reset-api` - retry TechSpecs mode when credentials exist
- `GET /memory-stats` - chat memory stats
- `POST /clear-memory` - clear chat memory
- `POST /chat` - chatbot message endpoint

## Notes

- The app works without TechSpecs credentials by using `data/laptop_specs_enhanced.csv`.
- The chatbot needs `GROQ_API_KEY`.
- Keep secrets in `.env`; do not commit real API keys.
- If you want to learn the backend first, read `backend/app.py`, then `backend/laptop_catalog.py`.
