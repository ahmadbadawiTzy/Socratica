# Socratica — Langflow Flows (Canonical Architecture)

This directory contains the canonical Langflow flow definitions for the Socratica educational RAG pipeline.

---

## 1. Streamlined Production Architecture

Socratica operates with **2 Canonical Flows**:

| Flow Name | Export File | Flow ID | Description |
|---|---|---|---|
| **Socratica — All-in-One AI Assistant** | `flows/exports/socratica_unified.json` | `fe99317c-abcc-4e05-85fd-e2d897fcbdf1` | End-to-end pedagogical assistant handling academic guardrails, grounded Q&A with citations, Socratic tutoring, assignment evaluation, and Qdrant vector retrieval powered by Google Gemini. |
| **Socratica — Document Ingestion** | `flows/exports/socratica_ingestion.json` | `a080844a-76c6-4841-98ea-9e23b817ecb5` | Ingestion pipeline processing course documents (PDF, DOCX, TXT), text chunking, Gemini embeddings (768 dimensions), and persistent vector storage in Qdrant. |

Redundant legacy prototype flows (`socratica_retrieval_qa.json`, `socratica_socratic.json`, `socratica_assignment_evaluator.json`, `socratica_guardrail.json`) have been consolidated into `socratica_unified.json` to eliminate port handle mismatches and maintain a clean single source of truth.

---

## 2. Pipeline Diagrams

### A. Document Ingestion Pipeline (`socratica_ingestion.json`)

```
[Document Upload (File)]
          │
          ▼
[Recursive Character Text Splitter]
          │
          ▼
[Google Gemini Embeddings (models/gemini-embedding-001 - 768 dim)]
          │
          ▼
[Qdrant Document Store (collection: socratica)]
```

### B. Assistant & Retrieval Pipeline (`socratica_unified.json`)

```
[Student Query / Submission]
          │
          ├──────────────────────────────┐
          ▼                              ▼
[Qdrant Retriever (search_query)]  [Intent & Mode Handler]
          │                              │
          ▼                              │
[Parser & Grounded Context]              │
          │                              │
          └──────────────┬───────────────┘
                         ▼
           [Socratica Pedagogical Prompt]
             - Academic Guardrail
             - Mode: Socratic / Q&A / Evaluator
                         │
                         ▼
           [Google Gemini Flash-Lite LLM]
                         │
                         ▼
                   [Chat Output]
```

---

## 3. Credentials & Vector Store Configuration

1. **Google Gemini API Key:** Managed centrally in Langflow via *Settings → Global Variables* (`GEMINI_API_KEY` or `GOOGLE_API_KEY`) or container environment variables. Flow JSON files never contain hardcoded plaintext API keys (`load_from_db: true`).
2. **Qdrant Vector Database:** Both flows connect to the canonical collection `socratica` hosted at `http://qdrant:6333` (Docker network) or `http://localhost:6333` (host).
3. **Active Models:**
   - **Embeddings:** `models/gemini-embedding-001` (768-dimensional vectors with cosine distance).
   - **LLM:** `gemini-flash-lite-latest` (high speed, cost-effective, low latency for interactive tutoring).

---

## 4. Environment Variables (`.env`)

Configure the following variables in your root `.env`:

```env
LANGFLOW_BASE_URL=http://localhost:7860
LANGFLOW_UNIFIED_FLOW_ID=fe99317c-abcc-4e05-85fd-e2d897fcbdf1
LANGFLOW_INGESTION_FLOW_ID=a080844a-76c6-4841-98ea-9e23b817ecb5
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=socratica
```
