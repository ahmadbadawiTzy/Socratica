# Socratica

> Web Chatbot AI Teaching Assistant based on RAG — Grounded Knowledge + Socratic Learning + Human Escalation.

## Quick Start

```bash
# 1. Clone & configure
cp .env.example .env       # edit .env with your values
cp frontend/.env.local.example frontend/.env.local

# 2. Start infrastructure
cd ibm-hacktiv8-langflow && docker compose up -d && cd ..
docker compose up db qdrant -d

# 3. Run backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn asgi:app --reload

# 4. Import Langflow flows (see flows/README.md)
# Open http://localhost:7860 → import flows/exports/*.json
# Configure Gemini API key and Qdrant URL in each flow
# Copy flow IDs to .env

# 5. Run frontend
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## Architecture

```
┌──────────────────────────┐
│   Next.js + React        │
│   Web Chatbot UI         │  http://localhost:3000
└────────────┬─────────────┘
             │ REST API
             ▼
┌──────────────────────────┐
│   FastAPI Backend        │  http://localhost:8000
│   Auth / API / DB        │
└────────────┬─────────────┘
             │ Langflow API
             ▼
┌──────────────────────────┐
│   Langflow (Docker)      │  http://localhost:7860
│   RAG Orchestration      │
└──────────┬───────────────┘
           ├──────────────────┐
           ▼                  ▼
    Qdrant :6333        PostgreSQL :5432
    Vector DB           Application DB
```

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 + React + TypeScript + Tailwind CSS |
| Backend | FastAPI + SQLAlchemy + Alembic |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant |
| RAG Orchestration | Langflow (Docker) |
| LLM + Embeddings | Google Gemini (configured in Langflow) |
| Auth | JWT (HS256) + Argon2id password hashing |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- Google Gemini API key (set in Langflow, not in `.env`)
- Langflow running via `ibm-hacktiv8-langflow/compose.yaml`

---

## Step-by-Step Setup

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` — required values:
```env
DATABASE_URL=postgresql+asyncpg://socratica:changeme@localhost:5432/socratica
LANGFLOW_BASE_URL=http://localhost:7860
JWT_SECRET=<generate: python -c "import secrets; print(secrets.token_hex(32))">
FRONTEND_ORIGIN=http://localhost:3000
```

After importing flows (step 5), also set:
```env
LANGFLOW_RETRIEVAL_FLOW_ID=<uuid>
LANGFLOW_INGESTION_FLOW_ID=<uuid>
LANGFLOW_SOCRATIC_FLOW_ID=<uuid>
LANGFLOW_EVALUATOR_FLOW_ID=<uuid>
```

### 2. Start Services

```bash
# PostgreSQL + Qdrant (from repo root)
docker compose up db qdrant -d

# Langflow (from ibm-hacktiv8-langflow directory)
cd ibm-hacktiv8-langflow
docker compose up -d
# → Langflow UI: http://localhost:7860
```

### 3. Setup & Run Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start backend
uvicorn asgi:app --reload --host 0.0.0.0 --port 8000
# → API: http://localhost:8000
# → API docs (dev): http://localhost:8000/docs
```

### 4. Setup & Run Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
# → UI: http://localhost:3000
```

### 5. Import Langflow Flows

See [`flows/README.md`](flows/README.md) for step-by-step instructions.

**Summary:**
1. Open `http://localhost:7860`
2. Import each file from `flows/exports/`
3. Set Gemini API key in each Gemini component
4. Set Qdrant URL: `http://localhost:6333`
5. Copy flow IDs to `.env`
6. Restart FastAPI: `uvicorn asgi:app --reload`

---

## API Endpoints

### Public
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/health/langflow` | Langflow connectivity |
| `POST` | `/api/v1/auth/register` | Register account |
| `POST` | `/api/v1/auth/login` | Login → JWT |
| `POST` | `/api/v1/auth/refresh` | Refresh token |

### Authenticated
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/auth/me` | Current user profile |
| `GET` | `/api/v1/courses` | List enrolled courses |
| `POST` | `/api/v1/courses` | Create course (lecturer) |
| `GET` | `/api/v1/courses/{id}` | Course detail |
| `POST` | `/api/v1/courses/{id}/enroll` | Enroll user |
| `GET` | `/api/v1/courses/{id}/documents` | List documents |
| `POST` | `/api/v1/courses/{id}/documents` | Upload document |
| `DELETE` | `/api/v1/courses/{id}/documents/{doc_id}` | Delete document |
| `GET` | `/api/v1/conversations` | List conversations |
| `POST` | `/api/v1/conversations` | Create conversation |
| `GET` | `/api/v1/conversations/{id}` | Get conversation + messages |
| `DELETE` | `/api/v1/conversations/{id}` | Soft-delete |
| `POST` | `/api/v1/conversations/{id}/messages` | Send message → RAG |
| `GET` | `/api/v1/escalations` | My escalations |
| `GET` | `/api/v1/escalations/course/{id}` | Course escalations (lecturer/TA) |
| `PATCH` | `/api/v1/escalations/{id}` | Update escalation status |

---

## Running Tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

---

## Langflow Flows

| File | Purpose | Flow ID Env Var |
|---|---|---|
| `socratica_ingestion.json` | Ingest documents to Qdrant | `LANGFLOW_INGESTION_FLOW_ID` |
| `socratica_retrieval_qa.json` | Q&A with RAG + citations | `LANGFLOW_RETRIEVAL_FLOW_ID` |
| `socratica_socratic.json` | Socratic learning mode | `LANGFLOW_SOCRATIC_FLOW_ID` |
| `socratica_assignment_evaluator.json` | Evaluate student drafts | `LANGFLOW_EVALUATOR_FLOW_ID` |
| `socratica_guardrail.json` | Input safety classifier (optional) | `LANGFLOW_GUARDRAIL_FLOW_ID` |

---

## Docker Networking

Two options for FastAPI ↔ Langflow communication:

**Option A (recommended for dev — FastAPI on host):**
```env
LANGFLOW_BASE_URL=http://localhost:7860
```

**Option B (FastAPI in Docker, same network):**
```bash
docker network create socratica-net
# Add network to ibm-hacktiv8-langflow/compose.yaml
```
```env
LANGFLOW_BASE_URL=http://langflow:7860
```

---

## Security Notes

- JWT tokens expire in 60 minutes (configurable via `JWT_EXPIRE_MINUTES`)
- Passwords hashed with Argon2id
- `course_id` for retrieval always derived from server-side auth — never from user input
- Retrieved document content treated as DATA in all prompts (indirect injection protection)
- Student drafts treated as untrusted DATA in evaluator prompt
- CORS restricted to `FRONTEND_ORIGIN` — no wildcards
- No Gemini API key in source code or `.env` — configured in Langflow credential store

---

## Current Implementation Status

| Component | Status |
|---|---|
| FastAPI backend | ✅ Complete |
| Auth (JWT + Argon2id) | ✅ Complete |
| PostgreSQL models + migrations | ✅ Complete |
| Course + enrollment management | ✅ Complete |
| Document upload + ingestion trigger | ✅ Complete |
| Chat API + Langflow integration | ✅ Complete |
| Escalation system | ✅ Complete |
| Langflow flows (5 flows) | ✅ Ready to import |
| Qdrant (via docker-compose) | ✅ Configured |
| Next.js chatbot UI | ✅ Complete |
| Login / Register | ✅ Complete |
| Conversation history | ✅ Complete |
| Citation display | ✅ Complete |
| Document manager (lecturer/TA) | ✅ Complete |
| Socratic Mode | ✅ (via Langflow flow) |
| Assignment Evaluator | ✅ (via Langflow flow) |
| Escalation notifications | ✅ In-app status |
| End-to-end RAG | ⏳ Requires Gemini key + flow import |

---

## Remaining Setup Steps

1. **Get Gemini API key**: [Google AI Studio](https://aistudio.google.com)
2. **Import flows** into Langflow (`flows/README.md`)
3. **Set flow IDs** in `.env`
4. **Upload test document** to a course
5. **Test chat**: ask a question about the document

---

## Documentation

- [`docs/prd.md`](docs/prd.md) — Product Requirements (source of truth)
- [`docs/ai.md`](docs/ai.md) — Engineering Instructions
- [`flows/README.md`](flows/README.md) — Langflow flow import guide
