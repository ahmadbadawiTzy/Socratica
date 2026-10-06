# Socratica — Langflow Flows

This directory contains Langflow flow JSON exports for the Socratica RAG pipeline.

## Status
**Phase 2 — Flows available for import.** All 5 flows are ready to import into Langflow.

---

## Quick Import Guide

### Step 1 — Start Langflow
```bash
cd ibm-hacktiv8-langflow
docker compose up -d
# Open: http://localhost:7860
```

### Step 2 — Import each flow
1. Open Langflow UI at `http://localhost:7860`
2. Click **"New Flow"** → **"Import from file"** (or drag & drop)
3. Import each JSON file from `flows/exports/`:
   - `socratica_ingestion.json`
   - `socratica_retrieval_qa.json`
   - `socratica_socratic.json`
   - `socratica_assignment_evaluator.json`
   - `socratica_guardrail.json` (optional for MVP)

### Step 3 — Configure Google Gemini API Key
For **each flow** that contains Gemini components:
1. Click the **Gemini Embeddings** component → set `google_api_key`
2. Click the **Gemini LLM** component → set `google_api_key`

> **Use Langflow's credential store** — do NOT paste keys into source code.
> In Langflow UI: Settings → Credentials → Add credential → name it `GEMINI_API_KEY`
> Then reference it in each component via the credential dropdown.

### Step 4 — Configure Qdrant
For each flow with a Qdrant component:
- `url`: `http://localhost:6333` (or `http://qdrant:6333` if Langflow is in Docker with Qdrant)
- `collection_name`: `socratica`
- `api_key`: leave empty for local Qdrant without auth

### Step 5 — Verify embedding model consistency
All flows use `models/text-embedding-004` for embeddings.
**CRITICAL**: The model in ingestion must match the model in retrieval/QA flows.
If you change the model, re-index all documents.

### Step 6 — Get Flow IDs
For each imported flow:
1. Open the flow in Langflow UI
2. Click **API** tab (top right)
3. Copy the **Flow ID** (UUID in the curl example)

### Step 7 — Configure FastAPI
Add flow IDs to your `.env` file:
```env
LANGFLOW_INGESTION_FLOW_ID=<uuid-from-langflow>
LANGFLOW_RETRIEVAL_FLOW_ID=<uuid-from-langflow>
LANGFLOW_SOCRATIC_FLOW_ID=<uuid-from-langflow>
LANGFLOW_EVALUATOR_FLOW_ID=<uuid-from-langflow>
LANGFLOW_GUARDRAIL_FLOW_ID=<uuid-from-langflow>
```

### Step 8 — Smoke Test
```bash
# With FastAPI running:
curl http://localhost:8000/api/v1/health/langflow
# Expected: {"status":"ok","service":"langflow"}
```

---

## Flow Overview

### Flow A — Document Ingestion (`socratica_ingestion.json`)
```
File Input (PDF/DOCX/PPTX)
  → RecursiveCharacterTextSplitter (512 tokens, 64 overlap)
  → Gemini Embeddings (text-embedding-004)
  → Qdrant Vector Store (collection: socratica)
```
**Triggered by:** `POST /api/v1/courses/{id}/documents` after file upload.
**Metadata injected by FastAPI:** `document_id`, `document_name`, `course_id`, `document_type`, `meeting`, `chapter`, `source_filename`.

### Flow B — Retrieval Q&A (`socratica_retrieval_qa.json`)
```
Chat Input (question)
  → Qdrant Retriever (top-k=5, filter: course_id)
  → RAG Prompt (grounding + injection protection)
  → Gemini LLM (gemini-1.5-flash, temp=0.1)
  → Chat Output (answer + citations)
```
**Used for:** Standard Q&A about course materials.
**Security:** Prompt explicitly separates context (DATA) from instructions. course_id filter from FastAPI auth.

### Flow C — Socratic Mode (`socratica_socratic.json`)
```
Chat Input (student question)
  → Qdrant Retriever (top-k=5, filter: course_id)
  → Socratic Prompt (hint + guiding question)
  → Gemini LLM (gemini-1.5-flash, temp=0.3)
  → Chat Output (hint/question response)
```
**Used for:** Problem-solving guidance. Maintains conversation context via session_id.

### Flow D — Assignment Evaluator (`socratica_assignment_evaluator.json`)
```
Draft Input (student work)
  → Qdrant Retriever (top-k=8, rubric + material)
  → Evaluator Prompt (structured feedback, no grades)
  → Gemini LLM (gemini-1.5-flash, temp=0.2)
  → Evaluation Output
```
**Security:** Draft treated as untrusted DATA. Code is NOT executed.
**Output:** Summary, Strengths, Areas for Improvement, Suggestions. No numeric score.

### Flow E — Guardrail (`socratica_guardrail.json`)
```
User Input
  → Classifier Prompt
  → Gemini LLM (temp=0.0)
  → JSON Classification Result
```
**Returns:** `{classification, reason, safe_to_proceed}`
**MVP Note:** Optional — the Q&A prompt itself includes injection protection.

---

## Security Notes

- No API keys are embedded in these flow JSON files.
- Use Langflow's credential store for all API keys.
- `course_id` filter is always injected server-side by FastAPI — never from user input.
- Retrieved document content is always treated as DATA in prompts, not instructions.
- Student draft content is explicitly labeled as untrusted DATA in the evaluator prompt.

---

## Open Decisions (still required)

| Item | Status |
|---|---|
| OD-04 | Faithfulness evaluation methodology — evaluation set needed |
| OD-05 | Meeting/chapter metadata extraction (manual vs auto) |
| OD-14 | File scanning tool for malicious documents |
