# Dampak LLM pada Proses Code Review

**Replikasi & modifikasi** penelitian Collante et al. dengan **Oracle Database 23ai AI Vector Search**.

Mata kuliah: UAS Software Engineering / AI  
Penyusun: **Siti Nurkhalisah**

## Ringkasan penelitian

Proyek ini mengikuti pendekatan ATM (Amati–Tiru–Modifikasi) dari paper:
*The Impact of Large Language Models (LLMs) on Code Review Process* (arXiv:2508.11034),
lalu menambahkan komponen vector search berbasis Oracle 23ai.

| RQ | Tipe | Pertanyaan |
|---|---|---|
| RQ1 | Imitasi | Apakah temuan merge-time dan review-phase pada paper tetap berlaku untuk PR publik periode 2025-01-01 s.d. 2026-10-31 yang menyebut tool LLM? |
| RQ2 | Modifikasi (Vector Search) | Apakah pelabelan PR dengan embedding + k-NN di Oracle (`VECTOR_DISTANCE`, COSINE) lebih baik daripada heuristik regex H1–H4? |
| RQ3 | Modifikasi (RAG) | Apakah klasifikasi tipe tugas dengan RAG (contoh di-retrieve dari Oracle) lebih baik daripada zero-shot prompting? |

## Struktur repositori

```
data/         dataset mentah dan hasil label manual
docs/         catatan metodologi
models/       lokasi file model ONNX (tidak dikomit)
prompts/      prompt LLM yang digunakan dalam eksperimen
results/      log output, tabel, dan artefak hasil run script
screenshots/  tangkapan layar untuk laporan
sql/          script SQL untuk fase Oracle/vector/RAG
src/          script per fase (00_... dst) + utilitas umum
```

## Status implementasi saat ini

- ✅ Fase 0 (setup lingkungan, koneksi Oracle, dan vector smoke test) sudah tersedia.
- 🔄 Fase berikutnya disiapkan bertahap sesuai alur eksperimen.

## Quick start (Fase 0)

Target yang disarankan: Linux, Python 3.11+, Docker, Oracle Database Free (23ai).

### 1) Siapkan virtual environment Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Siapkan konfigurasi `.env`

```bash
cp .env.example .env
```

Isi nilai penting berikut di `.env`:
- `GITHUB_TOKEN`
- `ORACLE_ADMIN_PASSWORD`
- `ORACLE_USER` dan `ORACLE_PASSWORD`
- `ORACLE_DSN` (default: `localhost:1521/FREEPDB1`)
- `ORACLE_MODEL_DIR_PATH` (default: `/opt/oracle/models`)
- `ONNX_MODEL_FILE` (default: `all_MiniLM_L12_v2.onnx`)

### 3) Jalankan Oracle 23ai Free di Docker

```bash
docker run -d --name oracle23ai -p 1521:1521 \
  -e ORACLE_PWD='<samakan dengan ORACLE_ADMIN_PASSWORD di .env>' \
  -v oracle23ai-data:/opt/oracle/oradata \
  -v "$PWD/models":/opt/oracle/models:ro \
  container-registry.oracle.com/database/free:latest
```

Tunggu sampai log menampilkan:
`DATABASE IS READY TO USE!`

### 4) Aktifkan vector memory pool (sekali saja), lalu restart container

```bash
docker exec -i oracle23ai sqlplus -S / as sysdba <<'SQL'
ALTER SYSTEM SET vector_memory_size = 256M SCOPE = SPFILE;
SQL
docker restart oracle23ai
```

### 5) Buat schema aplikasi dan verifikasi setup

```bash
python src/00_setup_db.py
python src/00_check_setup.py
```

Output akan tersimpan di folder `results/`.

## Catatan model ONNX

Letakkan file model di:

`models/all_MiniLM_L12_v2.onnx`

Folder `models/` akan di-*mount* ke container sebagai `/opt/oracle/models`
melalui objek direktori Oracle `MODEL_DIR`.

## Troubleshooting singkat

- `ORA-01017` saat menjalankan pengecekan:
  - Pastikan `ORACLE_USER` / `ORACLE_PASSWORD` di `.env` sama dengan user yang dibuat oleh `src/00_setup_db.py`.
  - Jalankan ulang `python src/00_setup_db.py` setelah memastikan `ORACLE_ADMIN_PASSWORD` benar.
- Model tidak terbaca (`visible to the database: NO`):
  - Pastikan file ONNX ada di folder `models/` lokal.
  - Pastikan mount Docker ke `/opt/oracle/models` benar.

---

Dokumentasi metodologi rinci ada di `docs/metodologi.md`.
