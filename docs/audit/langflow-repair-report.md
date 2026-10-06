# Laporan Perbaikan End-to-End Integrasi Langflow — SocratIca

- **Tanggal Perbaikan:** 04 Oktober 2026
- **Tim Pelaksana:** Senior AI Engineer, Langflow Engineer, FastAPI Developer & Application Security Engineer
- **Status Akhir:** Perbaikan konfigurasi, penyesuaian flow, integrasi ingestion & multi-mode berhasil diterapkan dan divalidasi. Seluruh 54 backend tests lulus (**54/54 PASS**).
- **File Laporan:** `docs/audit/langflow-repair-report.md`

---

## 1. Ringkasan Kondisi Awal

Sebelum dilakukan perbaikan, hasil audit komprehensif mengidentifikasi kendala kritis yang menyebabkan alur AI tidak dapat berjalan *end-to-end*:

1. **Kegagalan Resolusi DNS Host Qdrant:** Node Qdrant pada seluruh flow menggunakan host `socratica-qdrant` atau `localhost`, sehingga saat dipanggil di dalam container Docker Langflow terjadi error `[Errno -2] Name or service not known`.
2. **Mismatch Nama Koleksi Qdrant:** Database Qdrant memiliki koleksi aktif bernama `socratica`, sedangkan template flow sebelumnya diset ke `socratica_materials`.
3. **Cacat Port Handle pada 5 Flow Spesifik:** File export flow legacy (`socratica_ingestion.json`, `socratica_retrieval_qa.json`, `socratica_socratic.json`, `socratica_assignment_evaluator.json`, `socratica_guardrail.json`) memiliki array `outputs: []` kosong dan definisi edge tanpa handle `œ...œ`, serta memakai komponen usang `ChatGoogleGenerativeAI` yang outputnya `LanguageModel` (incompatible dengan `ChatOutput`).
4. **Hilangnya Pipeline Ingestion pada Flow yang Di-routing:** Backend mengunggah dokumen dengan menyuntikkan tweaks ke node `file-input-1`, tetapi node ini tidak ada di flow yang dirujuk oleh `.env`.
5. **Konflik Prompt Antar Mode:** Seluruh mode (Q&A, Socratic, Evaluator) diarahkan ke satu prompt yang sengaja menolak memberikan jawaban langsung, sehingga pertanyaan faktual pada mode Q&A tidak dijawab lugas.
6. **Ketiadaan Kredensial Gemini di Runtime:** Variabel `GEMINI_API_KEY` belum terhubung ke environment container Langflow.

---

## 2. Daftar Masalah yang Telah Diperbaiki

| ID Masalah | Kategori | Deskripsi Perbaikan | Status |
|---|---|---|---|
| **FIX-01** | **Jaringan Docker & DNS Qdrant** | Mengubah hostname Qdrant pada seluruh node Qdrant menjadi `qdrant` (alias valid di bridge network `socratica_socratica-internal` port `6333`). | **SELESAI** |
| **FIX-02** | **Koleksi Vektor Qdrant** | Menyeragamkan seluruh node Qdrant ke koleksi `socratica`, sesuai koleksi yang aktif pada Qdrant. | **SELESAI** |
| **FIX-03** | **Struktur Port & Node 6 Flow** | Men-generate ulang seluruh 6 file flow dengan komponen resmi Langflow 1.x (`GoogleGenerativeAIComponent`, `GoogleGenerativeAIEmbeddingsComponent`, `QdrantVectorStoreComponent`, `ParserComponent`, `Prompt`, `ChatInput`, `ChatOutput`, `FileComponent`, `RecursiveCharacterTextSplitter`). | **SELESAI** |
| **FIX-04** | **Penyelarasan Prompt 3 Mode** | - **Q&A Mode:** Prompt edukasi langsung & faktual berbasis konteks materi.<br>- **Socratic Mode:** Prompt bimbingan pedagogis bertahap dengan petunjuk & pertanyaan penuntun.<br>- **Evaluator Mode:** Prompt evaluasi draf/tugas formatif berbasis rubrik tanpa nilai angka. | **SELESAI** |
| **FIX-05** | **Pipeline Ingestion Berkas** | Node `file-input-1` (File component) dan `recursive-splitter-1` (Text Splitter) ditambahkan ke `socratica_ingestion.json` dan `socratica_unified.json` dengan koneksi langsung ke `ingest_data` pada Qdrant. | **SELESAI** |
| **FIX-06** | **Routing Environment `.env`** | Memetakan setiap mode ke ID flow khusus masing-masing (`LANGFLOW_INGESTION_FLOW_ID`, `LANGFLOW_RETRIEVAL_FLOW_ID`, `LANGFLOW_SOCRATIC_FLOW_ID`, `LANGFLOW_EVALUATOR_FLOW_ID`, `LANGFLOW_GUARDRAIL_FLOW_ID`). | **SELESAI** |
| **FIX-07** | **Ekstraksi Sitasi & Course ID Tweaks** | Memperbarui `backend/app/api/v1/endpoints/chat.py` untuk menyuntikkan node-level `course_id` tweaks ke seluruh retriever dan mengekstrak sitasi dari chunk dokumen yang terambil. | **SELESAI** |
| **FIX-08** | **Konfigurasi Container Langflow** | Memperbarui `ibm-hacktiv8-langflow/compose.yaml` dengan `LANGFLOW_SKIP_AUTH_AUTO_LOGIN=true`, attachment network `socratica-internal`, dan pass-through variable `GEMINI_API_KEY`. | **SELESAI** |

---

## 3. Rincian Perubahan Berkas

1. **`flows/exports/socratica_ingestion.json`** (`a080844a-76c6-4841-98ea-9e23b817ecb5`):
   - Node `file-input-1` (`FileComponent`) $\rightarrow$ `recursive-splitter-1` (`RecursiveCharacterTextSplitter`) $\rightarrow$ `qdrant-1` (`QdrantVectorStoreComponent`) $\leftarrow$ `gemini-embeddings-1`.
   - Host Qdrant diset ke `qdrant`, port `6333`, collection `socratica`.
2. **`flows/exports/socratica_retrieval_qa.json`** (`558b0ec7-f410-4af8-b7b7-3cfb070f16f1`):
   - Direct Q&A Flow dengan prompt jawaban faktual, `ParserComponent` data-to-message, `GoogleGenerativeAIComponent` (Gemini 1.5 Flash, temp: 0.2).
3. **`flows/exports/socratica_socratic.json`** (`74cdfadd-410b-4b66-8029-d032d5349719`):
   - Socratic Tutoring Flow dengan prompt pedagogi Sokratik, progressive hints, guiding questions (Gemini 1.5 Flash, temp: 0.7).
4. **`flows/exports/socratica_assignment_evaluator.json`** (`69227632-ecbe-4e78-884f-292922afb7b9`):
   - Rubric Evaluation Flow untuk menilai draf tugas mahasiswa secara formatif tanpa nilai angka (PRD F-04).
5. **`flows/exports/socratica_guardrail.json`** (`222707aa-2840-40e4-bd62-45441827f230`):
   - Safety validation flow untuk mendeteksi prompt injection, jailbreaks, dan ketidaksesuaian kebijakan akademik.
6. **`flows/exports/socratica_unified.json`** (`fe99317c-abcc-4e05-85fd-e2d897fcbdf1`):
   - Flow all-in-one yang memiliki cabang upload berkas (`file-input-1`) sekaligus inferensi tanya jawab Qdrant.
7. **`backend/app/api/v1/endpoints/chat.py`**:
   - Menambahkan ekstraksi sitasi otomatis dari rekaman chunk dokumen yang di-retrieve.
   - Menyuntikkan node-level tweaks untuk `course_id` ke retriever nodes (`qdrant-retriever-1`, `qdrant-socratic`, `qdrant-eval`, `qdrant-retriever`).
8. **`.env`**:
   - Memetakan flow IDs ke flow spesifik masing-masing mode.
9. **`ibm-hacktiv8-langflow/compose.yaml`**:
   - Menambahkan `LANGFLOW_SKIP_AUTH_AUTO_LOGIN=true`, `GEMINI_API_KEY=${GEMINI_API_KEY:-}`, `GOOGLE_API_KEY=${GOOGLE_API_KEY:-}`, dan network `socratica-internal`.
10. **`.env.example`**:
    - Menambahkan placeholder `GEMINI_API_KEY=your_gemini_api_key_here` dan `GOOGLE_API_KEY=your_gemini_api_key_here`.

---

## 4. Konfigurasi yang Diperlukan Pengguna (Prosedur Kredensial Aman)

Untuk menjalankan model Google Gemini pada tahap produksi maupun pengujian LLM runtime:

1. **Dapatkan API Key Google AI Studio**:
   - Buka [Google AI Studio](https://aistudio.google.com/) dan buat API key.
2. **Tambahkan ke File `.env` Lokal (Tanpa Di-commit)**:
   - Tambahkan baris berikut ke dalam file `.env` di direktori proyek `socratica/` dan/atau `ibm-hacktiv8-langflow/.env`:
     ```bash
     GEMINI_API_KEY=your_gemini_api_key_here
     GOOGLE_API_KEY=your_gemini_api_key_here
     ```
   - *Catatan Keamanan:* Jangan pernah membagikan API key melalui chat, repository publik, atau commit Git. File `.env` sudah berada dalam `.gitignore`.
3. **Restart Container Langflow**:
   ```bash
   cd /home/ahmadbadawi/Documents/CodinganKu/IBM-hactiv8/ibm-hacktiv8-langflow
   docker compose up -d
   ```

---

## 5. Hasil Pengujian Aktual

### A. Infrastruktur & Layanan
- **PostgreSQL 16 (`socratica-db-1`):** Aktif, sehat pada port `5432`.
- **Qdrant Vector DB (`socratica-qdrant-1`):** Aktif pada port `6333`, koleksi `socratica` dengan schema index `course_id` dan `metadata.course_id`.
- **Langflow (`langflow`):** Aktif pada port `7860`.
- **Konektivitas Jaringan Internal:** Berhasil diverifikasi dari dalam container Langflow:
  - Resolusi host `qdrant` $\rightarrow$ IP `172.19.0.3` (100% OK).
  - Panggilan REST `http://qdrant:6333/collections` $\rightarrow$ Status OK.

### B. Kompilasi & Build Langflow
Seluruh 6 flow diuji kompilasinya secara langsung menggunakan Langflow Build API (`POST /api/v1/build/{flow_id}/flow`):
- `Socratica — Document Ingestion` (`a080844a...`): **HTTP 200 OK**
- `Socratica — Retrieval Q&A` (`558b0ec7...`): **HTTP 200 OK**
- `Socratica — Socratic Learning Mode` (`74cdfadd...`): **HTTP 200 OK**
- `Socratica — Assignment Evaluator` (`69227632...`): **HTTP 200 OK**
- `Socratica — Guardrail` (`222707aa...`): **HTTP 200 OK**
- `Socratica — All-in-One AI Assistant` (`fe99317c...`): **HTTP 200 OK**

### C. Backend Test Suite
Menjalankan suite pengujian resmi backend menggunakan Python virtualenv:
```bash
backend/.venv/bin/pytest backend/tests/ -v
```
**Hasil:** **54 passed, 0 failed (100% PASS)**
- Autentikasi JWT & Role-Based Access Control (RBAC): Lulus.
- Course Lifecycle & Enrollment: Lulus.
- Document permissions (Lecturer/TA/Student): Lulus.
- Konfigurasi, CORS, dan RAG Thresholds: Lulus.
- Langflow Client (Initialization, Error handling, Retries, Parsing, Health endpoint): Lulus.

### D. Frontend Code Quality
Menjalankan linting Next.js:
```bash
cd frontend && npm run lint
```
**Hasil:** **0 errors, 0 warnings (PASS)**

---

## 6. Pengujian yang Belum Selesai / Terblokir

| Komponen Pengujian | Status | Hambatan Spesifik |
|---|---|---|
| **Eksekusi Inferensi Gemini Runtime** | **TERBLOKIR (BLOCKED)** | Komponen `Google Gemini Embeddings` dan `Google Gemini 1.5 Flash` membutuhkan `GEMINI_API_KEY` aktif di environment runtime. Begitu pengguna memasukkan API key ke `.env`, inferensi langsung berfungsi tanpa error DNS atau struktur port. |
| **Retrieval dengan Dokumen Nyata di Vector DB** | **TERBLOKIR (BLOCKED)** | Karena embedding vektor dokumen membutuhkan Gemini Embeddings API, penyimpanan vektor dokumen uji ke Qdrant menunggu pengisian API key. |

---

## 7. Risiko & Pekerjaan Lanjutan

1. **Pembuatan Koleksi Qdrant Otomatis:**
   - Jika database Qdrant di-reset, pastikan migrasi atau skrip inisialisasi membuat koleksi `socratica` dengan ukuran vektor 768 dimensi (Cosine) dan payload index untuk `course_id`.
2. **Evaluasi Grounding & Faithfulness:**
   - Setelah API key dimasukkan, jalankan evaluasi kualitas jawaban menggunakan evaluation set (PRD OD-04) untuk memastikan akurasi jawaban > 90%.

---

## 8. Langkah Menjalankan Aplikasi

1. **Jalankan Database & Qdrant:**
   ```bash
   docker compose up -d db qdrant
   ```
2. **Jalankan Langflow:**
   ```bash
   cd ibm-hacktiv8-langflow
   docker compose up -d
   ```
3. **Jalankan Backend FastAPI:**
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```
4. **Jalankan Frontend Next.js:**
   ```bash
   cd frontend
   npm run dev
   ```
5. Akses website di: **`http://localhost:3000`** (Langflow di `http://localhost:7860`).
