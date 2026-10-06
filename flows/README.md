# Socratica — Langflow Flows (Canonical Architecture)

Direktori ini berisi ekspor JSON flow Langflow kanonikal untuk pipeline Socratica RAG.

---

## 1. Arsitektur Flow Minimal & Terpadu

Arsitektur produksi Socratica dirampingkan menjadi **2 Flow Utama**:

| Flow | File JSON | Flow ID | Deskripsi |
|---|---|---|---|
| **Socratica — All-in-One AI Assistant** | `flows/exports/socratica_unified.json` | `fe99317c-abcc-4e05-85fd-e2d897fcbdf1` | Mengorkestrasi Academic Guardrail, Q&A dengan sitasi, Socratic Tutoring, Evaluator Mode, dan Retrieval Qdrant secara kontekstual dengan Google Gemini. |
| **Socratica — Document Ingestion** | `flows/exports/socratica_ingestion.json` | `a080844a-76c6-4841-98ea-9e23b817ecb5` | Pipeline pemrosesan berkas (PDF, DOCX, TXT), pemecahan teks (chunking), embedding Gemini, dan penyimpanan vektor ke Qdrant. |

Flow lama yang redundant (`socratica_retrieval_qa.json`, `socratica_socratic.json`, `socratica_assignment_evaluator.json`, `socratica_guardrail.json`) telah digabungkan ke dalam `socratica_unified.json` untuk menyederhanakan arsitektur dan menghindari port handle mismatch.

---

## 2. Diagram Pipeline

### A. Pipeline Ingesti Dokumen (`socratica_ingestion.json`)
```
[File Upload]
      │
      ▼
[Recursive Character Text Splitter]
      │
      ▼
[Google Gemini Embeddings (models/gemini-embedding-001)]
      │
      ▼
[Qdrant Document Store (collection: socratica)]
```

### B. Pipeline Asisten & Retrieval (`socratica_unified.json`)
```
[Student Message / Submission]
      │
      ├──────────────────────────────┐
      ▼                              ▼
[Qdrant Retriever (search_query)]  [Intent & Mode Handler]
      │                              │
      ▼                              │
[Parser & Grounded Context]          │
      │                              │
      └──────────────┬───────────────┘
                     ▼
       [Socratica Pedagogical Prompt]
         - Academic Guardrail
         - Mode Socratic / Q&A / Evaluator
                     │
                     ▼
       [Google Gemini 2.5 Flash Lite]
                     │
                     ▼
               [Chat Output]
```

---

## 3. Konfigurasi Kredensial & Koleksi

1. **Gemini API Key:** Dikelola terpusat di Langflow melalui *Settings $\rightarrow$ Global Variables* (`GOOGLE_API_KEY` / `GEMINI_API_KEY`) atau container environment. File JSON flow tidak mengandung API key mentah (`load_from_db: true`).
2. **Koleksi Qdrant:** Kedua flow secara konsisten menggunakan koleksi tunggal kanonikal: `socratica` pada host `qdrant:6333` (Docker internal) atau `localhost:6333`.
3. **Model LLM & Embeddings:**
   - Embeddings: `models/gemini-embedding-001` (vektor 768 dimensi).
   - LLM: `gemini-2.5-flash-lite` (respons cepat, bebas 429 quota exhaustion).

---

## 4. Konfigurasi Environment (`.env`)

```env
LANGFLOW_BASE_URL=http://localhost:7860
LANGFLOW_UNIFIED_FLOW_ID=fe99317c-abcc-4e05-85fd-e2d897fcbdf1
LANGFLOW_INGESTION_FLOW_ID=a080844a-76c6-4841-98ea-9e23b817ecb5
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=socratica
```
