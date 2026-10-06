# Konfigurasi Gemini API & Service Status Socratica

Dokumen ini menjelaskan arsitektur kredensial Google Gemini API dan sistem pemantauan status layanan pada proyek **Socratica**.

---

## 1. Pemisahan Kredensial (Decoupled Credentials)

### Prinsip Utama
- **FastAPI backend TIDAK menyimpan atau membutuhkan Gemini API Key.**
- **Frontend Next.js TIDAK pernah menerima, meminta, atau menyimpan Gemini API Key.**
- Kredensial Gemini API dipusatkan secara eksklusif pada **Langflow**.

### Arsitektur Aliran Data
```
+---------------+        HTTP JSON API        +-------------------+        Langflow API        +-------------------+        Google AI API        +------------------+
|  Frontend UI  |  ========================>  |  FastAPI Backend  |  =======================>  |     Langflow      |  =======================>  |  Gemini 1.5 Pro  |
|   (Next.js)   |   Chat / Health requests    | (Port 8000 /api)  |     (Port 7860 /api)      |    (Docker Svc)   |      (Direct HTTPS)        |  (Google Cloud)  |
+---------------+                             +-------------------+                            +-------------------+                             +------------------+
   (Tanpa Key)                                   (Tanpa Key)                                     [GOOGLE_API_KEY]
                                                                                                 [Global Variable]
```

### Konfigurasi Langflow
Kredensial Gemini API dikelola di Langflow melalui dua metode:
1. **Global Variables Langflow:**
   - Masuk ke dashboard Langflow: `http://localhost:7860/`
   - Buka menu **Settings** $\rightarrow$ **Global Variables**.
   - Daftarkan variabel `GOOGLE_API_KEY` atau `GEMINI_API_KEY` bertipe `Generic` atau `Credential`.
2. **Docker Environment Variables:**
   - Pada `compose.yaml` Langflow (`ibm-hacktiv8-langflow/compose.yaml`), variabel diteruskan ke runtime container:
     ```yaml
     environment:
       - GOOGLE_API_KEY=${GOOGLE_API_KEY}
       - GEMINI_API_KEY=${GEMINI_API_KEY}
     ```

### Kebersihan Flow JSON
Seluruh file JSON ekspor flow di direktori `flows/exports/` dan database Langflow menggunakan template:
```json
"api_key": {
  "load_from_db": true,
  "value": ""
}
```
Tidak ada nilai API key mentah (hardcoded) yang disimpan dalam flow JSON repository Socratica.

---

## 2. Pemantauan Status Layanan (Real Service Status)

Socratica mengimplementasikan **status kesehatan riil** yang mendeteksi status komunikasi aktual sepanjang rantai:
`Frontend -> FastAPI -> Langflow -> Gemini API`.

Status tidak diasumsikan `Connected` hanya karena adanya string konfigurasi atau respon `PING` dari Langflow.

### Definisi Status Layanan

| Status | Deskripsi | Penyebab | Indikator UI |
|---|---|---|---|
| **Connected** | Semua layanan (FastAPI, Langflow, dan Gemini) aktif dan berfungsi normal. | Uji probe berhasil atau respons chat LLM terakhir berhasil didapatkan. | Bulat hijau (`bg-emerald-500`) |
| **Not Connected** | Langflow tidak dapat dihubungi dari backend FastAPI. | Container Langflow mati, down, atau network unreachable (`ConnectError`). | Bulat merah (`bg-rose-500`) |
| **Connection Timeout** | Permintaan ke Langflow atau Gemini melebihi batas waktu (timeout). | Latensi jaringan tinggi, rate limit throttling, atau Langflow freeze. | Bulat kuning (`bg-amber-500`) |
| **Authentication Error** | Kredensial Gemini API di Langflow ditolak oleh Google. | API key tidak valid, expired, atau permission dinonaktifkan (`401/403 Invalid API Key`). | Bulat merah (`bg-rose-500`) |
| **Quota Exceeded** | Kuota Gemini API harian/bulanan telah habis. | Batas kuota gratis atau kredit billing habis (`RESOURCE_EXHAUSTED` / HTTP 429). | Bulat merah muda/merah (`bg-rose-500`) |
| **Rate Limited** | Permintaan per menit (RPM/TPM) melebihi batas sementara. | Terlalu banyak request dalam jendela waktu singkat (`RATE_LIMIT_EXCEEDED`). | Bulat kuning (`bg-amber-500`) |
| **Service Error** | Terjadi kegagalan internal pada Langflow atau Google Gemini. | Flow error, handle mismatch, internal 500 error, atau downstream service unavailable. | Bulat oranye (`bg-orange-500`) |
| **Unknown Error** | Status belum dapat ditentukan atau format error tidak dikenali. | Belum ada riwayat probe atau inisialisasi awal. | Bulat abu-abu (`bg-slate-400`) |

---

## 3. Pencegahan Fake Recovery (Anti-Fake Recovery Rule)

Jika layanan mengalami error spesifik LLM (misalnya **Quota Exceeded** atau **Authentication Error**):
- Pengecekan health check biasa (ping ke `/api/v1/health` Langflow) **TIDAK AKAN** mengubah status Gemini kembali menjadi `Connected`.
- Status `Quota Exceeded` atau `Authentication Error` dipertahankan hingga:
  1. Pengguna mengirimkan chat baru dan mendapatkan respon LLM yang valid, ATAU
  2. Dijalankan probe LLM aktif via `GET /api/v1/health?probe=true` yang terbukti sukses menghasilkan respons.

Hal ini mencegah status berpindah-pindah palsu (flickering) antara merah dan hijau saat kuota LLM habis tetapi server Langflow masih menyala.

---

## 4. Format Respons Endpoint Health

Endpoint: `GET /api/v1/health` (dan alias `/api/health`)

```json
{
  "status": "ok",
  "service": "socratica-backend",
  "langflow": "connected",
  "gemini": "connected",
  "error": null
}
```

Jika terjadi error pada Gemini (misal kuota habis):
```json
{
  "status": "degraded",
  "service": "socratica-backend",
  "langflow": "connected",
  "gemini": "quota_exceeded",
  "error": "Gemini API quota exceeded (RESOURCE_EXHAUSTED). Please check your billing or quota at Google AI Studio."
}
```

---

## 5. Sanitasi Pesan Error (Credential Stripping)

Semua output error yang berasal dari downstream (Langflow log / Google AI response) disaring oleh `classifier.sanitize_text()` sebelum diteruskan ke frontend atau disimpan di log. Parameter sensitif seperti pola regex:
- `AIza[0-9A-Za-z-_]{35}`
- `Bearer [a-zA-Z0-9_\-\.]+`
- Query parameters `key=...`, `api_key=...`, `token=...`

secara otomatis disensor menjadi `[REDACTED_API_KEY]`.
