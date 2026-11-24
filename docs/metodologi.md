# Catatan Metodologi (draf, per fase)

## Fase 0 — Persiapan lingkungan

Penelitian dijalankan di Arch Linux dengan Python dan basis data Oracle Database 23ai
Free yang berjalan di container Docker. Seluruh kode, prompt, dan dataset disimpan di
repositori GitHub dengan struktur `data/`, `src/`, `sql/`, `prompts/`, `results/`, dan
`screenshots/`, sedangkan kredensial (token GitHub dan kata sandi basis data) hanya
disimpan di berkas `.env` yang dikecualikan dari Git. Koneksi dari Python ke Oracle
menggunakan pustaka python-oracledb mode *thin*. Sebelum eksperimen, lingkungan diuji
dengan contoh vektor dua dimensi dari materi Oracle Academy (*What is a Vector*):
jarak antar vektor dihitung dengan fungsi `VECTOR_DISTANCE` memakai beberapa
*distance function* (EUCLIDEAN, COSINE, MANHATTAN, DOT), lalu dilakukan *exact
similarity search* dengan `ORDER BY VECTOR_DISTANCE … FETCH FIRST k ROWS ONLY`.
Selain itu disiapkan *vector memory pool* (`vector_memory_size`) yang dibutuhkan
indeks HNSW dan objek direktori `MODEL_DIR` untuk model ONNX yang akan dipakai pada
tahap *embedding generation* (Fase 3).
