# Socratica

> **Grounded AI Teaching Assistant with Socratic Learning, RAG, and Human Escalation**  
> Developed for educational institutions to provide pedagogical guidance, grounded academic assistance, and continuous feedback.

---

## Overview

**Socratica** is an enterprise-grade AI academic assistant engineered to transform how universities and students interact with course materials. Unlike conventional generative chat applications that simply provide direct answers to assignments—undermining critical thinking—Socratica employs the **Socratic Method** to stimulate intellectual curiosity, guide problem-solving through scaffolded inquiry, and provide rubric-aligned formative feedback.

### Key Capabilities

1. **Course-Grounded RAG (Retrieval-Augmented Generation)**:
   All answers are anchored strictly in lecturer-uploaded syllabus documents, lecture notes, and reading materials using **Qdrant** vector search and **Google Gemini** embeddings.
2. **Pedagogical Socratic Tutoring**:
   Rather than handing over final solutions or code, Socratica challenges students with probing questions, conceptual hints, and guided checkpoints.
3. **Formative Assignment Evaluation**:
   Students can submit assignment drafts for rubric-aligned feedback without receiving an automated grade, highlighting areas of conceptual mastery and opportunities for refinement.
4. **Academic Guardrails & Safety**:
   Rebuffs non-academic prompts, prevents cheating attempts, and mitigates indirect prompt injection attacks hidden within uploaded documents.
5. **Seamless Human Escalation**:
   When an AI interaction reaches an impasse or addresses out-of-scope administrative queries, questions can be escalated directly to professors or Teaching Assistants (TAs) with full conversational context.

---

## System Architecture

The following diagram illustrates the end-to-end architecture and data flow across Socratica's services:

```mermaid
flowchart TD
    subgraph Client["Presentation Layer (Client)"]
        UI["Next.js 16 Web Application<br/>(React 19, TypeScript, Tailwind CSS)"]
    end

    subgraph BackendGateway["Application & API Layer"]
        API["FastAPI Backend<br/>(Async REST, Auth, Business Logic)"]
        DB[("PostgreSQL 16<br/>Users, Courses, Enrollments,<br/>Conversations, Escalations")]
    end

    subgraph RAGOrchestration["AI & Orchestration Layer"]
        LF["Langflow Orchestration Engine<br/>(Dockerized Execution Pipeline)"]
        
        subgraph Flows["Canonical Flows"]
            UnifiedFlow["Socratica — All-in-One AI Assistant<br/>(Guardrail, Grounded Q&A, Socratic, Evaluator)"]
            IngestionFlow["Socratica — Document Ingestion<br/>(Chunking, Embedding, Indexing)"]
        end
    end

    subgraph StorageVector["Knowledge & Inference Layer"]
        Qdrant[("Qdrant Vector Database<br/>(Collection: socratica, 768-dim)")]
        Gemini["Google Gemini Cloud API<br/>(LLM: gemini-flash-lite-latest<br/>Embeddings: gemini-embedding-001)"]
    end

    UI -->|"HTTP / REST API (Port 8000)"| API
    API -->|"Async SQLAlchemy / asyncpg"| DB
    API -->|"Langflow REST Client (Port 7860)"| LF
    LF --> UnifiedFlow
    LF --> IngestionFlow
    
    UnifiedFlow -->|"Vector Search & Metadata Filter"| Qdrant
    UnifiedFlow -->|"Inference Prompts & Responses"| Gemini
    
    IngestionFlow -->|"Vector Embeddings"| Gemini
    IngestionFlow -->|"Vector Upserts (course_id payload)"| Qdrant
```

---

## Data & Ingestion Pipeline

```mermaid
flowchart LR
    A["Course Document<br/>(PDF, DOCX, TXT)"] --> B["FastAPI Upload Endpoint<br/>(/api/v1/courses/:id/documents)"]
    B --> C["Langflow Ingestion Pipeline<br/>(socratica_ingestion.json)"]
    C --> D["Recursive Character Splitter<br/>(Chunk: 1000, Overlap: 200)"]
    D --> E["Google Gemini Embeddings<br/>(models/gemini-embedding-001)"]
    E --> F["Qdrant Vector Store<br/>(Payload: course_id, filename, chunk)"]
```

- **Tenant Isolation**: Documents are tagged with a verified `course_id` extracted from authenticated session credentials. Vector queries are strictly scoped to the active enrolled course to prevent data leakage across classes.
- **Deduplication & Hygiene**: Chunks retain original source metadata enabling precise citation attribution in chat responses.

---

## Technology Stack

| Layer | Technology | Details / Version |
|---|---|---|
| **Frontend** | Next.js, React, TypeScript | Next.js 16 (Turbopack, App Router), React 19, Tailwind CSS 4 |
| **Backend API** | FastAPI, Python | Python 3.11+, Pydantic v2, ASGI (`uvicorn`) |
| **Relational Database** | PostgreSQL, SQLAlchemy | PostgreSQL 16 Alpine, SQLAlchemy 2.0 (asyncio), Alembic migrations |
| **Vector Database** | Qdrant | Qdrant latest, HNSW Cosine Index, 768 dimensions |
| **RAG Orchestrator** | Langflow | Langflow 1.x running in isolated Docker environment |
| **Foundation Models** | Google Gemini | **LLM:** `gemini-flash-lite-latest`<br/>**Embeddings:** `models/gemini-embedding-001` (768-dim) |
| **Authentication** | JWT & Argon2id | Access & Refresh tokens, Argon2id password hashing |
| **Containerization** | Docker, Docker Compose | Multi-container setup for PostgreSQL, Qdrant, and Langflow |

---

## Project Structure

```text
socratica/
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── api/v1/           # Versioned API routes (auth, courses, chat, escalations)
│   │   ├── core/             # App configuration, security, database session
│   │   ├── models/           # SQLAlchemy database models
│   │   ├── schemas/          # Pydantic validation schemas
│   │   └── services/         # Langflow client, RAG orchestrator, sanitizers
│   ├── migrations/           # Alembic database migrations
│   ├── tests/                # Automated pytest test suite (63+ tests)
│   └── asgi.py               # ASGI application entrypoint
├── frontend/                 # Next.js 16 web application
│   ├── src/
│   │   ├── app/              # Next.js App Router (pages & layouts)
│   │   ├── components/       # UI components (chat, navigation, modals)
│   │   └── lib/              # API clients and utilities
│   ├── package.json          # Frontend dependencies and scripts
│   └── tsconfig.json         # TypeScript configuration
├── flows/                    # Canonical Langflow definitions
│   ├── exports/
│   │   ├── socratica_unified.json    # All-in-One pedagogical & RAG assistant
│   │   └── socratica_ingestion.json  # File chunking & Qdrant ingestion
│   └── README.md             # Flow documentation and setup guide
├── docs/                     # Architecture specifications & PRD
│   ├── prd.md                # Product Requirements Document
│   └── ai.md                 # Engineering guidelines and architectural decisions
├── scripts/                  # Utility and verification scripts
│   └── verify_e2e_complete.py# Automated End-to-End validation test suite
├── docker-compose.yml        # Docker Compose configuration (db, qdrant, backend)
├── .env.example              # Sample environment configuration template
└── README.md                 # Project documentation
```

---

## Prerequisites

Before setting up Socratica locally, ensure the following tools are installed:

- **Docker** (version 24.0+) & **Docker Compose** (v2.0+)
- **Python** (version 3.11 or higher)
- **Node.js** (version 18.x or higher) & **npm** (v9.x or higher)
- **Google Gemini API Key** (obtained via [Google AI Studio](https://aistudio.google.com/))

---

## Quickstart & Local Setup

### 1. Clone the Repository & Configure Environment

```bash
# Clone repository
git clone https://github.com/your-username/socratica.git
cd socratica

# Copy environment template
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

Edit `.env` to configure application secrets:
```env
# Application & Database
DATABASE_URL=postgresql+asyncpg://socratica:changeme@localhost:5432/socratica
POSTGRES_PASSWORD=changeme

# Authentication (Generate via: python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET=your_generated_64_character_secret_here

# Langflow & Vector Store
LANGFLOW_BASE_URL=http://localhost:7860
LANGFLOW_UNIFIED_FLOW_ID=fe99317c-abcc-4e05-85fd-e2d897fcbdf1
LANGFLOW_INGESTION_FLOW_ID=a080844a-76c6-4841-98ea-9e23b817ecb5
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=socratica

# CORS
FRONTEND_ORIGIN=http://localhost:3000
```

> [!IMPORTANT]
> **Gemini API Key Security**: The `GEMINI_API_KEY` is **never** committed to `.env` or the codebase. It is configured centrally within Langflow's credential store or runtime environment.

---

### 2. Launch Core Infrastructure

Start the PostgreSQL database and Qdrant vector database:

```bash
docker compose up db qdrant -d
```

Start the Langflow container:
```bash
# From the peer or dedicated Langflow directory:
cd ../ibm-hacktiv8-langflow
docker compose up -d
cd ../socratica
```

Verify that services are up:
- PostgreSQL: `localhost:5432`
- Qdrant Dashboard: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
- Langflow Studio: [http://localhost:7860](http://localhost:7860)

---

### 3. Setup and Run the Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn asgi:app --host 0.0.0.0 --port 8000 --reload
```

- API Base URL: [http://localhost:8000](http://localhost:8000)
- Interactive OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 4. Setup and Run the Frontend

```bash
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

- Web Application: [http://localhost:3000](http://localhost:3000)

---

### 5. Configure Langflow Flows

1. Open **Langflow Studio** at [http://localhost:7860](http://localhost:7860).
2. Click **Import** and select the two canonical flow exports:
   - `flows/exports/socratica_unified.json`
   - `flows/exports/socratica_ingestion.json`
3. Configure your **Google Gemini API Key** in Langflow:
   - Navigate to **Settings** $\rightarrow$ **Global Variables**.
   - Add variable `GEMINI_API_KEY` with your Google AI Studio API key.
   - Alternatively, enter the key directly into the `Google Generative AI` components in both flows.
4. Verify that the Qdrant component in both flows points to host `qdrant:6333` (Docker bridge) or `localhost:6333` and collection `socratica`.
5. Note the generated flow IDs and update `LANGFLOW_UNIFIED_FLOW_ID` and `LANGFLOW_INGESTION_FLOW_ID` in your `.env` file if they differ from the defaults.

---

## API Endpoints Reference

### Public Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Comprehensive system health check with live probe support (`?probe=true`) |
| `GET` | `/api/v1/health/langflow` | Langflow and Gemini connectivity verification |
| `POST` | `/api/v1/auth/register` | Register a new student or lecturer account |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT access & refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh expired access token |

### Authenticated Endpoints

| Method | Endpoint | Access Role | Description |
|---|---|---|---|
| `GET` | `/api/v1/auth/me` | All | Get profile of currently authenticated user |
| `GET` | `/api/v1/courses` | All | List courses enrolled or instructed |
| `POST` | `/api/v1/courses` | Lecturer | Create a new academic course |
| `GET` | `/api/v1/courses/{id}` | Enrolled | Get detailed course syllabus and stats |
| `POST` | `/api/v1/courses/{id}/enroll` | Student | Enroll current user in a course |
| `GET` | `/api/v1/courses/{id}/documents` | Enrolled | List ingested course materials |
| `POST` | `/api/v1/courses/{id}/documents` | Lecturer / TA | Upload course document and trigger ingestion pipeline |
| `DELETE` | `/api/v1/courses/{id}/documents/{doc_id}` | Lecturer | Remove document and vector representations |
| `GET` | `/api/v1/conversations` | All | List user's active and past conversation threads |
| `POST` | `/api/v1/conversations` | All | Start a new conversation thread within a course |
| `GET` | `/api/v1/conversations/{id}` | Owner | Retrieve conversation history and message stream |
| `POST` | `/api/v1/conversations/{id}/messages` | Owner | Send prompt to AI assistant (triggers Langflow RAG) |
| `GET` | `/api/v1/escalations` | Student | List escalated questions and lecturer responses |
| `GET` | `/api/v1/escalations/course/{id}` | Lecturer / TA | View pending questions requiring instructor review |
| `PATCH` | `/api/v1/escalations/{id}` | Lecturer / TA | Resolve or respond to escalated student questions |

---

## Testing & Quality Assurance

### 1. Backend Test Suite

The backend includes a comprehensive suite of unit and integration tests covering authentication, RBAC, RAG orchestrators, and fault handling:

```bash
cd backend
source .venv/bin/activate
pytest -v
```

*Status: 63/63 passing tests.*

### 2. Frontend Production Build

Validate TypeScript compilation, Tailwind CSS compilation, and Next.js Turbopack build:

```bash
cd frontend
npm run build
```

*Status: 0 compilation errors.*

### 3. Automated End-to-End Verification

Socratica includes an automated E2E test suite that runs against live local infrastructure to validate the entire user journey:

```bash
python3 scripts/verify_e2e_complete.py
```

The script systematically tests:
1. **Infrastructure Health**: PostgreSQL, Qdrant, and Langflow responsiveness.
2. **Authentication Flow**: User registration, login, and JWT credential validation.
3. **Course Management**: Course creation and student enrollment.
4. **Document Ingestion**: Document upload, chunking, and embedding generation.
5. **Vector Retrieval & RAG**: Semantic query matching in Qdrant.
6. **Pedagogical Assistant**: Direct Q&A mode, Socratic hints, and assignment evaluation.
7. **Human Escalation**: Question flagging and lecturer resolution workflow.

---

## Security & Privacy Highlights

- **Centralized Credential Management**: Google Gemini API keys are never stored in client code, backend source code, or application `.env` files. Keys are managed exclusively within Langflow's credential store.
- **Tenant Data Isolation**: Database-level and vector-payload-level isolation ensures students can only retrieve documents associated with courses they are explicitly enrolled in.
- **Indirect Prompt Injection Defense**: Course documents are treated strictly as untrusted data chunks during prompt templating, preventing hidden adversarial instructions from hijacking the LLM.
- **Cryptographic Security**: Passwords are protected using `Argon2id` hashing with unique salts, and API tokens utilize `HS256` signed JWTs with strict expiration windows.
- **CORS Protection**: Access to backend endpoints is restricted to explicitly whitelisted origin domains (`FRONTEND_ORIGIN`).

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
