# Socratica

> **Grounded AI Teaching Assistant with Socratic Learning, RAG, and Human Escalation**  
> Prepared for the **IBM SkillsBuild × Hacktiv8 National Hackathon**

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Problem Statement](#the-problem-statement)
3. [The Socratica Solution](#the-socratica-solution)
4. [Core Features & Current MVP Scope](#core-features--current-mvp-scope)
5. [Value Proposition & Differentiation](#value-proposition--differentiation)
6. [IBM Bob & Langflow: Roles in Socratica](#ibm-bob--langflow-roles-in-socratica)
7. [System Architecture](#system-architecture)
8. [Technology Stack](#technology-stack)
9. [Application Workflow & Data Flow](#application-workflow--data-flow)
10. [Repository Structure](#repository-structure)
11. [Prerequisites & System Requirements](#prerequisites--system-requirements)
12. [Environment Configuration](#environment-configuration)
13. [Installation & Local Setup](#installation--local-setup)
14. [Langflow Flow Configuration](#langflow-flow-configuration)
15. [API Documentation](#api-documentation)
16. [Knowledge Ingestion & RAG Pipeline](#knowledge-ingestion--rag-pipeline)
17. [Testing & Quality Assurance](#testing--quality-assurance)
18. [Security & Known Limitations](#security--known-limitations)
19. [Future Roadmap](#future-roadmap)
20. [Hackathon Submission & Project Impact](#hackathon-submission--project-impact)
21. [License](#license)

---

## Executive Summary

**Socratica** is an enterprise-grade AI academic assistant engineered to transform how higher education institutions and students engage with course materials. Unlike conventional generative chat applications that simply output direct answers to student homework—short-circuiting the cognitive effort essential for deep learning—Socratica embeds the **Socratic Method** into an institutional Retrieval-Augmented Generation (RAG) framework.

By combining course-grounded semantic retrieval, pedagogical scaffolding, automated academic guardrails, and human-in-the-loop escalation to course instructors, Socratica bridges the divide between instant information retrieval and authentic conceptual mastery.

---

## The Problem Statement

> **"Information is increasingly accessible. Understanding is still a challenge."**

The widespread adoption of foundation models and conversational AI in education has democratized access to instant answers. However, rapid answer retrieval does not equate to learning. In university environments, unguided generative AI tools introduce serious educational challenges:

- **Answer Dependency**: Ready-made solutions bypass the struggle required to form neural connections and intuitive problem-solving skills.
- **Superficial Understanding**: Receiving a correct answer or functioning code block often creates a false illusion of competence without genuine conceptual comprehension.
- **Limited Adaptive Guidance**: Standard educational materials and unspecialized chatbots lack structured, step-by-step scaffolding tailored to identify individual student misconceptions.
- **Unexamined Assumptions**: Learners frequently fail to question premise validity, critique flawed steps, or articulate *why* a particular method produces a valid result.
- **Fragmented Learning Resources**: Siloed lecture slides, textbooks, and assignment briefs are rarely integrated into an interactive dialogue that enforces academic honesty.

Rather than acting as a homework generator, learning technology must facilitate the reasoning and intellectual inquiry necessary to build lasting understanding.

---

## The Socratica Solution

**Socratica is designed not merely to deliver answers, but to help learners understand the reasoning behind them.**

Rooted in classical Socratic dialogue and modern pedagogical scaffolding, Socratica acts as a grounded 24/7 teaching assistant. It guides learners to:

1. **Deconstruct Problems**: Break down multi-step algorithms, mathematical proofs, and analytical questions into manageable cognitive steps.
2. **Examine Assumptions**: Prompt students to reflect on edge cases, initial premises, and underlying principles before accepting conclusions.
3. **Formulate Independent Solutions**: Offer progressive hints and reflective inquiries rather than handing out finished solutions.
4. **Anchor in Authoritative Course Materials**: Ground dialogue strictly within instructor-curated syllabi, lecture slides, and reading materials.
5. **Seamlessly Escalate to Human Educators**: Route unanswered or out-of-scope inquiries directly to university professors and Teaching Assistants (TAs) with full conversational context.

---

## Core Features & Current MVP Scope

| Feature Category | Implementation Status | Description |
|---|---|---|
| **Multi-Role Authentication & RBAC** | **Implemented (MVP)** | JWT & Argon2id authentication separating `student`, `lecturer`, and `ta` access tiers with strict server-side course enrollment enforcement. |
| **Course & Document Management** | **Implemented (MVP)** | Course creation, student enrollment, and multi-format document ingestion (PDF, DOCX, PPTX, TXT, MD) with validation. |
| **Course-Grounded RAG (Q&A Mode)** | **Implemented (MVP)** | Strict semantic retrieval from Qdrant scoped by `course_id`. Direct factual questions receive grounded responses with document and page citations. |
| **Socratic Tutoring Mode** | **Implemented (MVP)** | Pedagogical scaffolding prompt dynamically active for problem-solving inquiries. Provides progressive hints without leaking final code or direct solutions. |
| **Formative Assignment Evaluation** | **Implemented (MVP)** | Evaluates draft submissions against course expectations. Provides structured feedback (Strengths, Areas for Improvement, Actionable Next Steps) without grading numbers. |
| **Prompt Injection & Safety Guardrails** | **Implemented (MVP)** | Intercepts direct prompt injection ("ignore instructions"), system prompt leaks, and academic dishonesty requests before model generation. |
| **Human Escalation Workflow** | **Implemented (MVP)** | Automatic or manual routing of unresolved/low-confidence queries to instructors, complete with conversation snapshots and lecturer resolution endpoints. |
| **Automated LMS Grade Sync** | *Planned (Post-MVP)* | Two-way synchronization with Canvas, Blackboard, or Moodle gradebooks. |
| **Voice & Multimodal Audio Interaction** | *Planned (Post-MVP)* | Real-time speech-to-text and audio tutoring interactions. |

---

## Value Proposition & Differentiation

> **Socratica doesn't just help you find the answer. It helps you understand why the answer makes sense.**

| Dimension | Standard Generic AI Chatbot | Socratica AI Academic Assistant |
|---|---|---|
| **Primary Interaction Model** | Direct answer generation and code completion | Socratic inquiry, progressive hints, and guided reflection |
| **Knowledge Grounding** | General public training data with hallucination risk | Strictly bounded to instructor-uploaded course documents |
| **Citation Attribution** | Unverified or missing references | Strict citation extraction tied to retrieved vector chunks |
| **Data & Tenant Isolation** | Single shared context window | Strict course-level isolation (`course_id`) enforced at database and vector levels |
| **Handling Ambiguity** | Fallback to ungrounded guesses | Transparent "Insufficient Context" notification + Human Escalation to Lecturer |
| **Educational Integrity** | Solves student assignments directly | Evaluates draft submissions formatively and refuses academic dishonesty |

---

## IBM Bob & Langflow: Roles in Socratica

Understanding the technical distinction between **development tooling**, **orchestration layer**, and **runtime inference** is vital to evaluating Socratica's architecture.

```mermaid
flowchart LR
    subgraph DevTime["Development & Engineering Phase"]
        Bob["IBM Bob<br/>(AI-Assisted Development Partner)"]
        Eng["Software Engineers<br/>& AI Specialists"]
        Bob -.->|"Scaffolding, Refinement,<br/>FastAPI & React Development"| Eng
    end

    subgraph RunTime["Runtime Orchestration & Execution"]
        Client["Web Client"] --> Backend["FastAPI Backend"]
        Backend -->|"REST API / Webhooks"| LF["Langflow Engine<br/>(Visual AI Orchestrator)"]
        LF -->|"Embeddings & LLM Inference"| CloudLLM["Google Gemini API<br/>(Cloud Foundation Model)"]
        LF -->|"Vector Search & Retrieval"| VDB[("Qdrant Vector DB")]
    end
```

### IBM Bob (AI-Assisted Development Tool)
- **Role**: AI-assisted software development and engineering acceleration.
- **Contribution**: IBM Bob served as the developer's pair-programming agent during the hackathon lifecycle. It facilitated the rapid implementation of clean FastAPI REST endpoints, Pydantic v2 validation models, complex SQLAlchemy async queries, Next.js frontend components, and robust test suites.
- **Architectural Boundary**: IBM Bob operates during the **development workflow**. It is **not** part of the production inference pipeline and does not serve runtime LLM requests.

### Langflow (AI Workflow Orchestration Platform)
- **Role**: Visual and declarative orchestration engine for runtime AI pipelines.
- **Contribution**: Langflow standardizes Socratica's multi-step RAG pipelines into modular, version-controlled directed acyclic graphs (DAGs). It unifies document loaders, recursive text splitters, embedding generators, Qdrant vector store sinks, pedagogical prompt builders, and LLM interfaces into executable flows.
- **Integration**: The FastAPI backend communicates with Langflow via its REST client (`/api/v1/run/{flow_id}` and `/api/v1/upload/{flow_id}`) located in `backend/app/services/langflow/client.py`.

### Runtime AI Model Distinction
- **Runtime Foundation Model**: Socratica currently utilizes **Google Gemini** (`gemini-flash-lite-latest` for LLM inference and `models/gemini-embedding-001` for 768-dimensional vector embeddings) configured directly inside Langflow.
- **Vector Database**: **Qdrant** persists and queries 768-dimensional embeddings filtered by `course_id`.
- *Note*: Socratica does not currently execute IBM watsonx or IBM Granite at runtime; all external inference credentials remain isolated within Langflow global variables.

---

## System Architecture

The following diagram represents Socratica's production runtime architecture:

```mermaid
flowchart TD
    subgraph PresentationLayer["Presentation Layer (Client)"]
        UI["Next.js 16 Web Application<br/>(React 19, TypeScript, Tailwind CSS 4)"]
    end

    subgraph ApplicationLayer["Application & Security Layer"]
        API["FastAPI Backend (Python 3.11+ / 3.12)<br/>(AuthN/AuthZ, Tenant Isolation, Course Logic)"]
        DB[("PostgreSQL 16 Database<br/>Users, Courses, Enrollments, Messages, Escalations")]
    end

    subgraph OrchestrationLayer["AI Orchestration Layer (Langflow)"]
        LF["Langflow Docker Service (Port 7860)"]
        
        subgraph CanonicalFlows["Canonical Flows"]
            UnifiedFlow["Socratica — All-in-One AI Assistant<br/>(Guardrail, Ingestion Branch, RAG, Socratic, Evaluator)"]
            IngestionFlow["Socratica — Document Ingestion<br/>(Splitter, Gemini Embeddings, Qdrant Indexer)"]
        end
    end

    subgraph KnowledgeLayer["Knowledge & Foundation Model Layer"]
        Qdrant[("Qdrant Vector Database (Port 6333)<br/>Collection: socratica (768-dim, Cosine)")]
        Gemini["Google Gemini Cloud API<br/>(LLM: gemini-flash-lite-latest<br/>Embeddings: models/gemini-embedding-001)"]
    end

    UI -->|"HTTP / JSON (Port 8000)"| API
    API -->|"Async SQLAlchemy / asyncpg"| DB
    API -->|"HTTP Client (POST /api/v1/run/:flow_id)"| LF
    LF --> UnifiedFlow
    LF --> IngestionFlow

    UnifiedFlow -->|"Vector Search (course_id payload filter)"| Qdrant
    UnifiedFlow -->|"Inference & Scaffolding Prompts"| Gemini

    IngestionFlow -->|"Compute 768-dim Embeddings"| Gemini
    IngestionFlow -->|"Upsert Vectors & Chunk Metadata"| Qdrant
```

---

## Technology Stack

| Layer | Technology | Version / Specification | Rationale & Responsibility |
|---|---|---|---|
| **Frontend** | Next.js, React, Tailwind CSS | Next.js 16 (Turbopack, App Router), React 19, Tailwind CSS 4 | Responsive, accessible chat and management UI with real-time markdown parsing. |
| **Backend API** | FastAPI, Python | Python 3.11+ / 3.12, Pydantic v2, ASGI (`uvicorn`) | High-performance asynchronous API enforcing RBAC and course data boundaries. |
| **Relational DB** | PostgreSQL, SQLAlchemy | PostgreSQL 16 Alpine, SQLAlchemy 2.0 (asyncio), Alembic | ACID-compliant storage for users, courses, enrollments, conversation logs, and escalations. |
| **AI Orchestration** | Langflow | Docker container (`langflowai/langflow:latest`) | Visual workflow DAG execution, dynamic prompting, RAG coordination, and modular flow management. |
| **Vector Database** | Qdrant | Qdrant latest, HNSW Cosine Index (768 dimensions) | Scalable vector search with strict payload metadata filtering on `course_id`. |
| **Foundation Models**| Google Gemini | `gemini-flash-lite-latest` (LLM), `models/gemini-embedding-001` (Embeddings) | Low-latency inference for real-time tutoring paired with native 768-dim vector embeddings. |
| **Authentication** | JWT & Argon2id | `python-jose[cryptography]`, `passlib[argon2]` | Cryptographically secure password hashing and stateless token issuance. |
| **Dev Tooling** | IBM Bob | AI Code Generation & Refinement Agent | Accelerated development of backend routes, data models, and UI components. |

---

## Application Workflow & Data Flow

### 1. Ingestion Pipeline
```
[Course Material (PDF/DOCX/PPTX)] 
   ──> FastAPI POST /courses/{id}/documents 
   ──> Langflow Ingestion Flow 
   ──> Recursive Text Splitter (Chunk: 1000, Overlap: 200) 
   ──> Gemini Embedding Model (768-dim) 
   ──> Qdrant Upsert (Payload: course_id, document_name, chunk_id)
```

### 2. Socratic & RAG Query Pipeline
```
[Student Message] 
   ──> FastAPI POST /conversations/{id}/messages 
   ──> Backend Authorizes Course Enrollment 
   ──> Inject Mode Prefix & course_id Filter 
   ──> Langflow Unified Flow
         ├── Guardrail Node: Checks prompt injection & academic honesty
         ├── Qdrant Node: Retrieves top-k chunks matching course_id
         ├── Document Parser: Assembles grounded context string
         ├── Pedagogical Prompt: Injects Socratic scaffolding or Rubric instructions
         └── Gemini LLM: Synthesizes guided response
   ──> FastAPI extracts response & citations 
   ──> Stored in PostgreSQL & returned to Client UI
```

---

## Repository Structure

```text
socratica/
├── backend/                       # FastAPI application service
│   ├── app/
│   │   ├── api/v1/                # Versioned REST API endpoints
│   │   │   ├── endpoints/         # Auth, chat, courses, documents, escalations, health
│   │   │   └── router.py          # Main v1 router aggregation
│   │   ├── core/                  # Configuration, security, logging, dependency injection
│   │   ├── db/                    # Async SQLAlchemy session management
│   │   ├── models/                # SQLAlchemy database models
│   │   ├── schemas/               # Pydantic v2 validation schemas
│   │   └── services/              # Langflow client, health monitor, text sanitizers
│   ├── migrations/                # Alembic database schema migrations
│   ├── tests/                     # Pytest suite (unit, integration, RBAC, service status)
│   ├── asgi.py                    # ASGI application entrypoint
│   └── Dockerfile                 # Backend container definition
├── frontend/                      # Next.js web application
│   ├── app/                       # App Router pages (/login, /register, /chat, /)
│   ├── components/                # React UI components (chat, navigation, modals)
│   ├── lib/                       # API clients and utilities
│   ├── package.json               # Frontend dependencies and build scripts
│   └── tsconfig.json              # TypeScript configuration
├── flows/                         # Canonical Langflow flow definitions
│   ├── exports/
│   │   ├── socratica_unified.json # Canonical all-in-one assistant flow
│   │   └── socratica_ingestion.json # Canonical document ingestion flow
│   └── README.md                  # Detailed flow architecture documentation
├── docs/                          # Technical specifications and audit reports
│   ├── prd.md                     # Product Requirements Document
│   ├── ai.md                      # Engineering guidelines and architectural decisions
│   └── audit/                     # Verification and unified flow reports
├── scripts/                       # Verification scripts
│   └── verify_e2e_complete.py     # End-to-end integration test script
├── docker-compose.yml             # Docker Compose for local PostgreSQL, Qdrant, backend
├── pyproject.toml                 # Backend dependencies, Ruff, and Pytest configuration
├── .env.example                   # Environment variable template
├── LICENSE                        # MIT License
└── README.md                      # Root documentation
```

---

## Prerequisites & System Requirements

- **Linux / macOS / Windows (WSL2)**
- **Docker** (v24.0+) & **Docker Compose** (v2.0+)
- **Python** (v3.11 or v3.12)
- **Node.js** (v18.x or higher) & **npm** (v9.x or higher)
- **Google Gemini API Key** (acquired from [Google AI Studio](https://aistudio.google.com/))

---

## Environment Configuration

Copy the template configuration files:

```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

### Essential Backend Environment Variables (`.env`)

| Variable | Description | Required | Sample / Default Value |
|---|---|:---:|---|
| `DATABASE_URL` | Async PostgreSQL connection string | Yes | `postgresql+asyncpg://socratica:changeme@localhost:5432/socratica` |
| `POSTGRES_PASSWORD`| PostgreSQL superuser password | Yes | `changeme` |
| `JWT_SECRET` | 64-character hex secret for token signing | Yes | Generate via `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `LANGFLOW_BASE_URL`| Langflow server host URL | Yes | `http://localhost:7860` |
| `LANGFLOW_UNIFIED_FLOW_ID` | UUID of the imported unified flow | Yes | `fe99317c-abcc-4e05-85fd-e2d897fcbdf1` |
| `LANGFLOW_INGESTION_FLOW_ID`| UUID of the document ingestion flow | Optional | `a080844a-76c6-4841-98ea-9e23b817ecb5` |
| `QDRANT_URL` | Qdrant vector database URL | Yes | `http://localhost:6333` |
| `QDRANT_COLLECTION`| Vector collection name | Yes | `socratica` |
| `FRONTEND_ORIGIN` | CORS origin allowed to communicate with API | Yes | `http://localhost:3000` |
| `NEXT_PUBLIC_API_BASE_URL` | Backend URL consumed by Next.js frontend | Yes | `http://localhost:8000` |

> [!IMPORTANT]
> **API Key Isolation**: The backend `.env` file does **not** store `GEMINI_API_KEY`. Google Gemini credentials are administered directly inside Langflow Global Variables or container environment configs.

---

## Installation & Local Setup

### 1. Launch Supporting Infrastructure

Start the PostgreSQL database and Qdrant vector store:

```bash
docker compose up db qdrant -d
```

Start Langflow (either via local docker compose or dedicated repository):

```bash
# If using a sibling Langflow compose setup:
cd ../ibm-hacktiv8-langflow
docker compose up -d
cd ../socratica
```

Verify service availability:
- PostgreSQL: `localhost:5432`
- Qdrant Dashboard: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
- Langflow Studio: [http://localhost:7860](http://localhost:7860)

### 2. Configure Backend Service

```bash
cd backend

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install backend dependencies in editable development mode
pip install -e ".[dev]"

# Apply database migrations
alembic upgrade head

# Launch FastAPI development server
uvicorn asgi:app --host 0.0.0.0 --port 8000 --reload
```

- API Base URL: [http://localhost:8000](http://localhost:8000)
- Interactive OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Configure Frontend Application

```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

- Web Client: [http://localhost:3000](http://localhost:3000)

---

## Langflow Flow Configuration

1. Access Langflow Studio at [http://localhost:7860](http://localhost:7860).
2. Click **Import** and select the canonical flow exports from the repository:
   - `flows/exports/socratica_unified.json`
   - `flows/exports/socratica_ingestion.json`
3. Configure the **Gemini API Key**:
   - Go to **Settings** $\rightarrow$ **Global Variables**.
   - Add variable `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) containing your API key.
4. Ensure the Qdrant node in both flows connects to `http://localhost:6333` (or `http://qdrant:6333` in Docker bridge) with collection name `socratica`.
5. Note the generated flow IDs and update `LANGFLOW_UNIFIED_FLOW_ID` in your `.env` file.

---

## API Documentation

### Public Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health check with optional live probe parameter (`?probe=true`) |
| `GET` | `/api/v1/health/langflow` | Langflow and LLM connectivity status probe |
| `POST` | `/api/v1/auth/register` | Register a new user account (`student`, `lecturer`, or `ta`) |
| `POST` | `/api/v1/auth/login` | Authenticate user and issue JWT access and refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh an expired access token |

### Protected Endpoints (Bearer Authentication)

| Method | Route | Allowed Roles | Description |
|---|---|:---:|---|
| `GET` | `/api/v1/auth/me` | All | Fetch current authenticated user profile |
| `GET` | `/api/v1/courses` | All | List courses the user is enrolled in or instructing |
| `POST` | `/api/v1/courses` | Lecturer | Create a new academic course |
| `GET` | `/api/v1/courses/{id}` | Enrolled | Get detailed syllabus, meeting schedule, and statistics |
| `POST` | `/api/v1/courses/{id}/enroll` | Student | Enroll current user into a course |
| `GET` | `/api/v1/courses/{id}/documents` | Enrolled | List ingested course documents |
| `POST` | `/api/v1/courses/{id}/documents` | Lecturer / TA | Upload course document and trigger Langflow ingestion |
| `DELETE` | `/api/v1/courses/{id}/documents/{doc_id}` | Lecturer / TA | Remove document record and indexed vectors |
| `GET` | `/api/v1/conversations` | All | List user's active conversation threads |
| `POST` | `/api/v1/conversations` | All | Initialize a new conversation thread within a course |
| `GET` | `/api/v1/conversations/{id}` | Owner | Retrieve message history for a specific thread |
| `POST` | `/api/v1/conversations/{id}/messages` | Owner | Submit query to AI assistant (triggers Langflow RAG) |
| `GET` | `/api/v1/escalations` | Student | List escalated questions initiated by the user |
| `GET` | `/api/v1/escalations/course/{id}` | Lecturer / TA | List pending student escalations for review |
| `PATCH` | `/api/v1/escalations/{id}` | Lecturer / TA | Submit instructor response and resolve escalation |

---

## Knowledge Ingestion & RAG Pipeline

```mermaid
flowchart LR
    Doc["Uploaded Document<br/>(PDF, DOCX, PPTX)"] --> Upload["FastAPI Endpoint<br/>/courses/{id}/documents"]
    Upload --> LF["Langflow Ingestion Node"]
    LF --> Split["Recursive Character Splitter<br/>(Chunk: 1000, Overlap: 200)"]
    Split --> Embed["Gemini Embeddings<br/>(models/gemini-embedding-001)"]
    Embed --> Qdrant[("Qdrant Vector Store<br/>Payload: course_id, document_name, chunk_id")]
```

1. **Format Handling**: The ingestion endpoint supports `.pdf`, `.docx`, `.pptx`, `.txt`, and `.md` files up to 50MB.
2. **Deterministic Metadata**: Each text chunk retains `course_id`, `document_id`, `document_name`, `page`, and `chapter`.
3. **Tenant Boundary**: Qdrant queries generated during student interactions enforce a strict metadata filter on `course_id`. A student in Course A cannot retrieve materials from Course B.
4. **Citation Extraction**: Retrieved vector chunks are parsed by FastAPI to verify the authenticity of document citations before returning responses to the user interface.

---

## Testing & Quality Assurance

Socratica features an extensive verification regime covering unit logic, RBAC, RAG orchestrators, and production builds:

### 1. Backend Pytest Suite
Run unit tests, RBAC isolation tests, and service status classifications:

```bash
cd backend
source .venv/bin/activate
pytest -v
```

*Status: 61+ unit and service mock tests passing out of the box (requires PostgreSQL and Langflow for live DB integration tests).*

### 2. Frontend Lint & Production Compilation
Verify TypeScript typings, React 19 client components, and Next.js 16 build:

```bash
cd frontend
npm run lint
npm run build
```

*Status: Clean build with 0 ESLint warnings and 0 compilation errors.*

### 3. End-to-End Architectural Verification
Execute the automated end-to-end integration suite against live services:

```bash
python3 scripts/verify_e2e_complete.py
```

The script verifies:
- Infrastructure connectivity across PostgreSQL, Qdrant, and Langflow.
- User registration, login, and JWT issuance.
- Course creation and enrollment boundaries.
- Document upload and ingestion execution.
- Vector retrieval and citation parsing.
- Socratic mode hint progression and academic integrity guardrails.

---

## Security & Known Limitations

### Security Features
- **Centralized Credential Store**: LLM provider credentials are not exposed to the frontend or saved in backend application `.env` files.
- **Strict Tenant Isolation**: Authorization is evaluated server-side. The `course_id` used in RAG queries is derived from verified user enrollments, never from user prompt text.
- **Indirect Prompt Injection Defense**: Course documents are treated as untrusted data during prompt formatting, neutralizing adversarial instructions embedded inside syllabus files.
- **Cryptographic Standards**: Password hashing utilizes `Argon2id` with unique salts; session authentication uses `HS256` signed JWTs with strict expiration windows.

### Known MVP Limitations
- **External Database Requirement**: Integration tests requiring live database sessions depend on an active PostgreSQL service.
- **Synchronous Ingestion Flow**: Document ingestion is triggered asynchronously via HTTP to Langflow, but large files (>50MB) require additional queue management (e.g., Celery/Redis) in high-concurrency environments.
- **Citation Precision**: Granular page citations are dependent on the document parser's ability to extract page markers from specific PDF formats.

---

## Future Roadmap

The following enhancements are planned for post-hackathon iterations:

- [ ] **LMS Interoperability**: LTI 1.3 integration for single sign-on (SSO) and roster synchronization with Canvas, Blackboard, and Moodle.
- [ ] **Automated Evaluation Benchmarking**: Continuous automated testing against an academic RAG benchmark (Faithfulness, Answer Relevance, and Context Recall).
- [ ] **Multimodal Voice Tutoring**: Interactive speech-to-speech Socratic dialogue for auditory learners.
- [ ] **Lecturer Analytics Dashboard**: Deep-dive visual analytics highlighting high-frequency student misconceptions and course-wide knowledge gaps.

---

## Hackathon Submission & Project Impact

### IBM SkillsBuild × Hacktiv8 National Hackathon Context
Socratica was created to address the critical challenge of superficial learning in the era of generative AI. By re-centering the educational experience around guided inquiry, pedagogical scaffolding, and grounded course materials, Socratica demonstrates how AI can empower educators and cultivate independent thinkers.

### Demonstration & Submission Artifacts
- **Repository**: [https://github.com/your-username/socratica](https://github.com/your-username/socratica) *(Update with your repository URL)*
- **Demo Video Walkthrough**: *Pending upload / Hackathon presentation*
- **Live Deployment URL**: *Pending deployment*
- **Presentation Deck**: *Available upon request / Hackathon portal*

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
