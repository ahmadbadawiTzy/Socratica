# Laporan Audit: Langflow Flow & Kesesuaian Integrasi Website SocratIca

- **Tanggal Audit:** 04 Oktober 2026
- **Auditor:** Senior AI Engineer, Langflow Specialist & Full-Stack Integration Auditor
- **Status Kode Saat Ini:** Tidak ada kode atau konfigurasi yang diubah selama proses audit.
- **File Laporan:** `docs/audit/langflow-website-integration-audit.md`

---

## A. Ringkasan Eksekutif

Audit komprehensif berbasis bukti (*evidence-based audit*) telah dilakukan terhadap seluruh alur pemrosesan AI (Langflow), backend FastAPI, database PostgreSQL, Qdrant Vector Store, dan frontend Next.js pada proyek **SocratIca**.

### 1. Kondisi Umum Flow Langflow
- Terdapat **6 file flow** di repositori (`flows/exports/*.json`) dan **6 flow** terdaftar pada instance Langflow aktif (`http://localhost:7860`).
- Dari 5 file flow terpisah warisan (`socratica_ingestion.json`, `socratica_retrieval_qa.json`, `socratica_socratic.json`, `socratica_assignment_evaluator.json`, `socratica_guardrail.json`), kelimanya memiliki **definisi handle terputus** (`outputs: []`, `sourceHandle: null`, `targetHandle: null`) serta memakai komponen lama `ChatGoogleGenerativeAI` yang mengeluarkan tipe `LanguageModel` (incompatible dengan `ChatOutput`).
- Flow gabungan **`socratica_unified.json`** (`fe99317c-abcc-4e05-85fd-e2d897fcbdf1`) telah berhasil diperbaiki struktur port dan koneksinya menggunakan format standar Langflow 1.x, dan berhasil di-build (`POST /api/v1/build/{flow_id}/flow` status 200 OK).
- Namun, pada pengujian eksekusi *runtime* (`POST /api/v1/run/{flow_id}`), flow tersebut mengalami kendala operasional yang menghalangi eksekusi end-to-end.

### 2. Tingkat Kesesuaian dengan Website
- **Socratic Mode (`mode="socratic"`):** **SESUAI SEBAGIAN.** Struktur prompt cocok untuk bimbingan Sokratik, tetapi terkendala pada eksekusi retriever dan autentikasi model LLM.
- **Q&A Mode (`mode="qa"`):** **TIDAK SESUAI.** Konfigurasi `.env` memetakan `LANGFLOW_RETRIEVAL_FLOW_ID` ke flow unified yang memiliki system prompt murni Sokratik (menolak memberikan jawaban langsung), bertentangan dengan kebutuhan mahasiswa untuk mendapatkan jawaban faktual langsung dari materi kuliah.
- **Evaluator Mode (`mode="evaluator"`):** **TIDAK SESUAI.** Konfigurasi `.env` memetakan mode ini ke flow unified tanpa prompt rubrik evaluasi tugas.
- **Document Ingestion (`api.documents.upload`):** **TIDAK SESUAI.** Backend mengirimkan *tweaks* node `file-input-1`, tetapi node tersebut tidak tersedia di dalam flow unified `fe99317c-abcc-4e05-85fd-e2d897fcbdf1`.
- **Multi-tenant Course Isolation (PRD RAG-03):** **TIDAK SESUAI.** Komponen retriever standar Langflow belum menerapkan filter `course_id`, sehingga terdapat risiko kebocoran konteks antar mata kuliah.

### 3. Masalah Paling Berdampak (Top Blockers)
1. **Kegagalan Resolusi DNS Qdrant:** Node Qdrant dikonfigurasi dengan hostname `socratica-qdrant`, sementara pada jaringan Docker internal hostname yang valid adalah `qdrant` atau `socratica-qdrant-1`, menyebabkan error `[Errno -2] Name or service not known`.
2. **Ketiadaan Kredensial Gemini di Runtime:** Kunci API Google Gemini (`GEMINI_API_KEY` / `GOOGLE_API_KEY`) belum didefinisikan pada environment container Langflow maupun pada template node.
3. **Mismatch Nama Koleksi Qdrant:** Qdrant menggunakan koleksi bernama `socratica`, sedangkan node flow unified mencari koleksi `socratica_materials`.
4. **Hilangnya Pipeline Ingestion pada Unified Flow:** Pengunggahan dokumen materi oleh Dosen/TA gagal dieksekusi karena node pemrosesan berkas tidak ada di flow yang dituju.

### 4. Batasan Pengujian
Pengujian runtime dilakukan secara aman melalui API Langflow lokal tanpa mengekspos rahasia dan tanpa memodifikasi skema basis data.

---

## B. Peta Arsitektur Aktual

```
┌────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js 15)                         │
│   - Chat Page (/app/chat/page.tsx)                                     │
│   - Modes: QA ("qa"), Socratic ("socratic"), Evaluator ("evaluator")    │
│   - Document Manager (Upload PDF/DOCX/PPTX, List, Delete)              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP Fetch (/api/v1/...)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                             │
│   - /api/v1/auth/* (JWT AuthN & RBAC)                                  │
│   - /api/v1/courses/* & /documents/* (Course & Ingestion Management)   │
│   - /api/v1/conversations/* (Chat Orchestration & Message History)     │
│   - /api/v1/health/langflow (Service Health Check)                     │
│   - Services: LangflowClient (HTTP Async Client)                       │
└─────────┬─────────────────────────┬──────────────────────────┬─────────┘
          │ SQL (asyncpg)           │ REST API                 │ REST
          ▼                         ▼                          ▼
┌──────────────────┐      ┌─────────────────────┐    ┌─────────────────┐
│ PostgreSQL 16    │      │ Langflow (v1.5+)    │    │ Qdrant Vector DB│
│ Container:       │      │ Container: langflow │    │ Container:      │
│ socratica-db-1   │      │ Port: 7860          │    │ socratica-      │
│ Port: 5432       │      └──────────┬──────────┘    │ qdrant-1        │
│ DB: socratica    │                 │               │ Port: 6333      │
└──────────────────┘                 │ gRPC / REST   │ Col: socratica  │
                                     ▼ (Host: qdrant)└────────┬────────┘
                          ┌─────────────────────┐             │
                          │ Qdrant Vector Store │◄────────────┘
                          │ + Google Gemini API │
                          └─────────────────────┘
```

---

## C. Inventaris File Flow

| Nama File | Nama Flow di JSON | ID Flow Terdaftar | Node Utama | Status Verifikasi Struktur | Kesiapan Eksekusi |
|---|---|---|---|---|---|
| `flows/exports/socratica_unified.json` | Socratica — All-in-One AI Assistant | `fe99317c-abcc-4e05-85fd-e2d897fcbdf1` | ChatInput, Gemini Embeddings, Qdrant Vector Store, Document Parser, Prompt, Gemini 1.5 Flash, ChatOutput | **VALID** (Langflow 1.x Format) | Build OK (200), Run terhambat DNS & API Key |
| `flows/exports/socratica_retrieval_qa.json` | Socratica — Retrieval Q&A | `558b0ec7-f410-4af8-b7b7-3cfb070f16f1` | ChatInput, Embeddings, Qdrant, Prompt, ChatGoogleGenerativeAI, ChatOutput | **CACAT** (Port handle kosong, edge unlinked) | Gagal dieksekusi |
| `flows/exports/socratica_socratic.json` | Socratica — Socratic Learning Mode | `74cdfadd-410b-4b66-8029-d032d5349719` | ChatInput, Embeddings, Qdrant, Prompt, ChatGoogleGenerativeAI, ChatOutput | **CACAT** (Port handle kosong, edge unlinked) | Gagal dieksekusi |
| `flows/exports/socratica_assignment_evaluator.json` | Socratica — Assignment Evaluator | `69227632-ecbe-4e78-884f-292922afb7b9` | ChatInput, Embeddings, Qdrant, Prompt, ChatGoogleGenerativeAI, ChatOutput | **CACAT** (Port handle kosong, edge unlinked) | Gagal dieksekusi |
| `flows/exports/socratica_ingestion.json` | Socratica — Document Ingestion | `a080844a-76c6-4841-98ea-9e23b817ecb5` | FileComponent, Splitter, Embeddings, Qdrant | **CACAT** (Port handle kosong, edge unlinked) | Gagal dieksekusi |
| `flows/exports/socratica_guardrail.json` | Socratica — Guardrail | `222707aa-2840-40e4-bd62-45441827f230` | ChatInput, Prompt, ChatGoogleGenerativeAI, ChatOutput | **CACAT** (Port handle kosong, edge unlinked) | Gagal dieksekusi |

---

## D. Matriks Kesesuaian Kebutuhan Website

| No. | Kebutuhan Website / PRD | Flow Terkait | Bukti Implementasi & Lokasi Kode | Status Kesesuaian | Dampak Terhadap Aplikasi |
|---|---|---|---|---|---|
| 1 | **Socratic Tutoring Mode** (`mode="socratic"`) | `socratica_unified.json` | `frontend/app/chat/page.tsx:32`<br>`backend/app/api/v1/endpoints/chat.py:130` | **SESUAI SEBAGIAN** | Konsep pedagogi prompt sesuai instruksi Sokratik, namun retrieval materi terhambat DNS Qdrant. |
| 2 | **Factual Q&A Mode** (`mode="qa"`) | `socratica_unified.json` | `frontend/lib/modes.ts:2`<br>`backend/app/api/v1/endpoints/chat.py:129` | **TIDAK SESUAI** | Flow yang aktif memakai prompt Sokratik (menolak memberi jawaban langsung), sehingga mode Q&A tidak berfungsi semestinya. |
| 3 | **Assignment Evaluator** (`mode="evaluator"`) | `socratica_unified.json` | `frontend/lib/modes.ts:4`<br>`backend/app/api/v1/endpoints/chat.py:131` | **TIDAK SESUAI** | Mode evaluator dialihkan ke unified flow yang tidak memiliki instruksi analisis rubrik tugas mahasiswa. |
| 4 | **Document Ingestion (Upload File Dosen)** | `socratica_unified.json` | `frontend/components/chat/DocumentManager.tsx:33`<br>`backend/app/api/v1/endpoints/documents.py:152-163` | **TIDAK SESUAI** | Backend mengirim parameter tweaks ke node `file-input-1`, tetapi node ini tidak ada di flow unified, menyebabkan upload gagal diproses. |
| 5 | **Isolasi Mata Kuliah (Course Isolation)** | `socratica_unified.json` | PRD RAG-03<br>`backend/app/api/v1/endpoints/chat.py:313` | **TIDAK SESUAI** | Backend menyuntikkan `course_id` via tweaks, namun komponen Qdrant standar Langflow tidak memiliki port filter `course_id`. |
| 6 | **Sitasi Materi Kuliah (Citations Pill)** | `socratica_unified.json` | `frontend/components/chat/MessageItem.tsx:51-57`<br>`backend/app/api/v1/endpoints/chat.py:136-161` | **SESUAI SEBAGIAN** | Frontend siap menampilkan citation pills, tetapi flow belum memformat metadata sitasi ke dalam field `artifacts.citations`. |
| 7 | **Guardrail Prompt Injection & Abuse** | `socratica_guardrail.json` | PRD SEC-01<br>`backend/app/api/v1/endpoints/chat.py` | **TIDAK SESUAI** | Backend memiliki konfigurasi `LANGFLOW_GUARDRAIL_FLOW_ID`, tetapi endpoint `send_message` tidak memanggil guardrail sebelum eksekusi. |
| 8 | **Sinkronisasi Koleksi Qdrant** | `socratica_unified.json` | `backend/app/core/config.py:67`<br>Qdrant REST API `/collections` | **TIDAK SESUAI** | Qdrant memiliki koleksi `socratica`, sedangkan node flow unified diset ke `socratica_materials`. |

---

## E. Temuan Teknis

### [FINDING-01] [CRITICAL] Kesalahan Hostname Qdrant pada Jaringan Docker Internal
- **File & Lokasi:** `flows/exports/socratica_unified.json` (Node `qdrant-retriever`), Flow ID `fe99317c-abcc-4e05-85fd-e2d897fcbdf1`.
- **Bukti Teknis:** Eksekusi Langflow mengembalikan error: `DNS resolution failed for socratica-qdrant: [Errno -2] Name or service not known`. Pengujian resolusi socket di dalam container `langflow` membuktikan bahwa hostname yang terdaftar pada bridge network adalah `qdrant` (IP 172.19.0.3) dan `socratica-qdrant-1`, bukan `socratica-qdrant`.
- **Dampak:** Seluruh pemanggilan AI yang melibatkan pencarian materi di Qdrant mengalami HTTP 500 fatal.
- **Penyebab:** Konfigurasi template node menggunakan string host default yang salah.
- **Rekomendasi:** Ubah nilai field `host` pada node Qdrant di flow menjadi `qdrant`.

### [FINDING-02] [HIGH] Ketiadaan Kredensial Provider Google Gemini di Runtime
- **File & Lokasi:** Container `langflow`, file konfigurasi `.env`, dan `ibm-hacktiv8-langflow/compose.yaml`.
- **Bukti Teknis:** Perintah pengecekan environment di dalam container `langflow` mengonfirmasi `GEMINI_API_KEY` dan `GOOGLE_API_KEY` bernilai `None`/kosong. Begitu pula pada file `.env`.
- **Dampak:** Komponen `GoogleGenerativeAIEmbeddingsComponent` dan `GoogleGenerativeAIComponent` akan gagal saat menghubungi endpoint Google AI API.
- **Penyebab:** Variabel API Key Gemini belum dideklarasikan dan diinjeksi ke dalam container Docker Langflow.
- **Rekomendasi:** Tambahkan `GEMINI_API_KEY` pada `.env` dan teruskan melalui `environment` di `compose.yaml`.

### [FINDING-03] [HIGH] Inkompatibilitas Endpoint Upload Dokumen dengan Flow Unified
- **File & Lokasi:** `backend/app/api/v1/endpoints/documents.py:162-163` dan `flows/exports/socratica_unified.json`.
- **Bukti Teknis:** Kode backend melakukan eksekusi:
  ```python
  await lf.run_flow(
      settings.langflow_ingestion_flow_id,
      LangflowRunRequest(
          input_value=lf_path,
          tweaks={"file-input-1": {"path": lf_path}, ...}
      )
  )
  ```
  Namun pada flow `fe99317c-abcc-4e05-85fd-e2d897fcbdf1`, node `file-input-1` tidak ditemukan.
- **Dampak:** Pengunggahan dokumen materi oleh Dosen/TA melalui UI Document Manager berstatus `FAILED` pada database.
- **Penyebab:** Flow unified saat ini hanya memuat jalur inferensi chat/retrieval, belum menyertakan sub-grafik ingestion.
- **Rekomendasi:** Tambahkan cabang pipeline ingestion (`FileComponent` $\rightarrow$ `RecursiveCharacterTextSplitter` $\rightarrow$ `QdrantVectorStoreComponent`) ke dalam flow unified dengan ID node yang sesuai kontrak backend.

### [FINDING-04] [MEDIUM] Ketidaksesuaian Nama Koleksi Vektor Qdrant
- **File & Lokasi:** `flows/exports/socratica_unified.json` (Node `qdrant-retriever`) vs Qdrant Database.
- **Bukti Teknis:** Qdrant hanya memiliki satu koleksi bernama `"socratica"` (`curl http://localhost:6333/collections` $\rightarrow$ `{"collections":[{"name":"socratica"}]}`). Sementara node flow diset ke `"socratica_materials"`.
- **Dampak:** Permintaan pencarian dokumen mencari ke koleksi yang belum ada, menyebabkan pencarian kosong (0 hasil) atau error collection not found.
- **Penyebab:** Inkonsistensi penamaan antara migrasi database awal dengan definisi node di Langflow.
- **Rekomendasi:** Seragamkan nilai `collection_name` pada node Qdrant menjadi `socratica`.

### [FINDING-05] [MEDIUM] Satu System Prompt untuk Semua Mode Percakapan
- **File & Lokasi:** `flows/exports/socratica_unified.json` (Node `socratica-prompt`), `backend/app/api/v1/endpoints/chat.py:128-133`.
- **Bukti Teknis:** Nilai `LANGFLOW_RETRIEVAL_FLOW_ID`, `LANGFLOW_SOCRATIC_FLOW_ID`, dan `LANGFLOW_EVALUATOR_FLOW_ID` di `.env` semuanya merujuk pada flow ID yang sama. Teks prompt berisi arahan pedagogi Sokratik: *"Guide students using the Socratic method: do not simply give away direct answers"*.
- **Dampak:** Mahasiswa yang memilih mode "Q&A" untuk menanyakan hal faktual (misal: jadwal ujian atau definisi dasar) akan tetap direspons dengan pertanyaan balik dan petunjuk, bukan jawaban lugas.
- **Penyebab:** Penyatuan seluruh mode ke dalam 1 flow tanpa mekanisme percabangan prompt dinamis berdasarkan parameter `mode`.
- **Rekomendasi:** Buat prompt dinamis atau teruskan variabel `mode` via tweaks/system message, atau sediakan cabang prompt terpisah untuk Q&A, Socratic, dan Evaluator.

### [FINDING-06] [MEDIUM] Hilangnya Filter `course_id` pada Level Vector Search
- **File & Lokasi:** `ext:qdrant:QdrantVectorStoreComponent@official` vs PRD RAG-03.
- **Bukti Teknis:** Komponen resmi Qdrant di Langflow 1.x menjalankan `vector_store.similarity_search(query=self.search_query, k=self.number_of_results)` tanpa meneruskan filter payload Qdrant (`{"must": [{"key": "course_id", "match": {"value": course_id}}]}`).
- **Dampak:** Potensi kebocoran materi kuliah antar kelas jika mahasiswa di Course A menanyakan topik yang juga ada di Course B.
- **Penyebab:** Komponen default Langflow Qdrant belum mengekspos port input filter metadata.
- **Rekomendasi:** Buat custom component turunan Qdrant yang mendukung filter `course_id` dari backend tweaks.

---

## F. Hasil Pengujian Verifikasi

| Kategori Pengujian | Perintah / Uji yang Dijalankan | Hasil | Keterangan |
|---|---|---|---|
| **Sintaks JSON Flow** | `python3 -c "import json; [json.load(open(f)) for f in glob('flows/exports/*.json')]"` | **LOLOS** | Seluruh 6 file flow memiliki sintaks JSON yang valid tanpa syntax error. |
| **Kompilasi Graph Langflow** | `POST http://localhost:7860/api/v1/build/fe99317c-abcc-4e05-85fd-e2d897fcbdf1/flow` | **LOLOS** | HTTP 200 OK (`{"job_id": "53ca0028-..."}`). Semua port saling cocok. |
| **Backend Unit Tests** | `backend/.venv/bin/pytest backend/tests/ -v` | **LOLOS** | 54/54 tests lulus (Auth, RBAC, Config, Langflow client parsing, Health endpoint). |
| **Konektivitas Docker Qdrant** | `curl -s http://localhost:6333/collections` | **LOLOS** | Layanan Qdrant aktif, koleksi `socratica` tersedia. |
| **Eksekusi Runtime Flow** | `POST http://localhost:7860/api/v1/run/fe99317c-abcc-4e05-85fd-e2d897fcbdf1` | **GAGAL** | Error HTTP 500: DNS resolution failed (`socratica-qdrant`). |
| **Autentikasi Provider AI** | Pemeriksaan environment container Langflow untuk `GEMINI_API_KEY` | **GAGAL** | API Key tidak ditemukan pada container runtime. |
| **End-to-End Ingestion** | Simulasi upload file ke flow unified | **BELUM DIUJI** | Terhambat oleh ketiadaan node `file-input-1` di flow unified. |

---

## G. Rekomendasi Perbaikan (Berdasarkan Prioritas)

### Prioritas 1: Perbaikan Konfigurasi Infrastruktur & Koneksi (Critical)
1. **Perbaiki Host Qdrant:** Ubah setting `host` pada node Qdrant di flow unified dari `socratica-qdrant` menjadi `qdrant`.
2. **Perbaiki Nama Koleksi:** Ubah `collection_name` pada node Qdrant menjadi `socratica` agar selaras dengan database aktual.
3. **Injeksi Kredensial Gemini:** Tambahkan `GEMINI_API_KEY` ke file `.env` dan daftarkan ke file `compose.yaml` pada container `langflow`.

### Prioritas 2: Penambahan Jalur Ingestion pada Unified Flow (High)
1. Gabungkan node `FileComponent` (`file-input-1`) dan `RecursiveCharacterTextSplitter` (`recursive-splitter-1`) ke dalam flow unified.
2. Hubungkan output splitter ke input `ingest_data` pada komponen Qdrant. Dengan ini, satu flow dapat melayani kebutuhan chat sekaligus upload dokumen.

### Prioritas 3: Pemisahan Prompt Antara Mode Q&A, Socratic, dan Evaluator (Medium)
1. Sediakan prompt khusus untuk mode:
   - **Q&A:** Menjawab langsung secara faktual dan akurat berdasarkan materi.
   - **Socratic:** Membimbing mahasiswa dengan pertanyaan bertahap dan petunjuk.
   - **Evaluator:** Menilai draf tugas berdasarkan rubrik penilaian tanpa memberikan nilai numerik.
2. Konfigurasikan ID flow masing-masing di `.env` atau buat percabangan logika di dalam kanvas Langflow.

### Prioritas 4: Penerapan Filter Course ID & Ekstraksi Sitasi (Medium)
1. Modifikasi komponen retriever Qdrant agar menerapkan filter `course_id` yang dikirim dari backend.
2. Tambahkan node pemformat metadata dokumen agar mengekstrak nama dokumen dan nomor halaman ke dalam output sitasi yang diharapkan frontend.

---

## H. Rencana Pengujian Ulang (Re-Verification Plan)

Setelah perbaikan disetujui dan diterapkan:
1. Jalankan tes resolusi jaringan dari dalam container Langflow ke Qdrant (`urllib.request`).
2. Jalankan eksekusi uji runtime via `POST /api/v1/run/{flow_id}` dengan prompt uji dan pastikan respons teks Gemini berhasil keluar tanpa error DNS.
3. Jalankan pengujian upload dokumen via backend FastAPI (`POST /api/v1/courses/{course_id}/documents`) dan verifikasi status berubah menjadi `ready`.
4. Jalankan pengujian tanya jawab di frontend (`http://localhost:3000/chat`) pada mode Q&A dan Socratic untuk memverifikasi perbedaan gaya respons AI.
5. Jalankan seluruh suite pengujian otomatis backend: `backend/.venv/bin/pytest backend/tests/ -v`.

---

## I. Kesimpulan

Secara objektif, implementasi Langflow pada proyek SocratIca saat ini **MEMENUHI SEBAGIAN KEBUTUHAN**:
- **Pencapaian:** Struktur visual kanvas dan kompatibilitas tipe port Langflow 1.x telah berhasil diselaraskan (Build 200 OK), dan backend FastAPI telah memiliki lapisan middleware yang sangat rapi untuk menangani komunikasi Langflow, RBAC, dan audit.
- **Kendala Utama:** Aplikasi belum dapat berfungsi secara penuh *end-to-end* akibat 3 kendala teknis konkret: salah hostname Qdrant (`socratica-qdrant`), ketiadaan API key Gemini di runtime, serta ketiadaan pipeline ingestion pada flow unified.

*Seluruh temuan di atas diperoleh melalui audit berbasis bukti dan belum ada modifikasi file kode/konfigurasi yang dilakukan.*
