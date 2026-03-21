# 🤖 AI Resume Analyzer

A production-ready AI-powered resume screening and candidate ranking system.

## 🏗 Architecture

```
resume_analyzer/
├── backend/
│   ├── config.py              # Pydantic settings (env vars)
│   ├── logger.py              # Structured logging
│   ├── main.py                # FastAPI app entry point
│   ├── models/
│   │   ├── db_models.py       # SQLAlchemy ORM models
│   │   └── schemas.py         # Pydantic request/response schemas
│   ├── routes/
│   │   ├── resume_routes.py   # POST /upload_resume
│   │   ├── job_routes.py      # POST /analyze_job
│   │   ├── ranking_routes.py  # POST /rank_candidates, GET /candidate/:id
│   │   └── export_routes.py   # GET /export_shortlist
│   ├── services/
│   │   ├── ai_service.py      # AI micro-task orchestration
│   │   ├── ranking_service.py # Full ranking pipeline
│   │   └── export_service.py  # CSV/JSON export
│   └── utils/
│       ├── ai_client.py       # Multi-provider LLM client
│       ├── database.py        # Async SQLAlchemy session
│       └── file_parser.py     # PDF + DOCX text extraction
├── frontend/
│   ├── app.py                 # Streamlit UI
│   └── .streamlit/config.toml
├── prompts/
│   └── templates.py           # All AI prompt templates
├── data/uploads/              # Temporary resume storage
├── logs/                      # Application logs
├── .env.example               # Environment variable template
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repo>
cd resume_analyzer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env — add your AI provider API key
```

**Get a free API key:**
- **OpenRouter** (recommended): https://openrouter.ai → free models available
- **Groq**: https://console.groq.com → very fast, generous free tier
- **Gemini**: https://aistudio.google.com → free tier available

### 3. Run the Backend (FastAPI)

```bash
# From project root
python -m uvicorn backend.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 4. Run the Frontend (Streamlit)

```bash
# In a second terminal
streamlit run frontend/app.py --server.port 8501
```

Open: http://localhost:8501

## 📡 API Endpoints

| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| POST   | /api/upload_resume    | Upload 1–20 PDF/DOCX resumes             |
| POST   | /api/analyze_job      | Extract requirements from job description|
| POST   | /api/rank_candidates  | Run full AI pipeline + ranking           |
| GET    | /api/candidate/:id    | Get full details for one candidate       |
| GET    | /api/export_shortlist | Download CSV or JSON export              |
| GET    | /health               | Health check                             |

## 🧠 AI Pipeline

For each resume, the system runs 6 parallel/sequential AI tasks:

1. **Resume Parser** → Extract name, email, skills, experience, education
2. **Job Analyzer** → Extract required skills, keywords, experience level
3. **Scoring Engine** → Score 1–10 with detailed reasoning
4. **ATS Gap Analyzer** → Missing keywords + improvement suggestions
5. **Weakness Detector** → Quality issues (metrics, descriptions, formatting)
6. **Report Generator** → Full markdown recruiter report

## ⚙️ Configuration

Key `.env` variables:

```env
AI_PROVIDER=openrouter          # openrouter | groq | gemini
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
SHORTLIST_SCORE_THRESHOLD=7    # Candidates with score >= 7 are shortlisted
MAX_FILE_SIZE_MB=10
DATABASE_URL=sqlite+aiosqlite:///./resume_analyzer.db
```

## 🔧 Changing AI Models

Edit `.env`:
```env
# Free OpenRouter models:
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
OPENROUTER_MODEL=meta-llama/llama-3-8b-instruct:free
OPENROUTER_MODEL=google/gemma-7b-it:free

# Groq (fast & free):
AI_PROVIDER=groq
GROQ_MODEL=llama3-8b-8192
GROQ_MODEL=mixtral-8x7b-32768
```

## 📊 Scoring Logic

- **Score 7–10** → Shortlisted ✅
- **Score 4–6.9** → Review candidate
- **Score 1–3.9** → Not recommended

Sub-scores: skill match + experience match + keyword match (weighted average)

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 📦 Production Deployment

```bash
# Backend
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend (behind nginx)
streamlit run frontend/app.py --server.headless true --server.port 8501
```
