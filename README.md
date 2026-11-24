# Dampak LLM pada Proses Code Review — Replikasi & Modifikasi dengan Oracle AI Vector Search

UAS Software Engineering / AI — **Siti Nurkhalisah (NIM: …)**

ATM (Amati–Tiru–Modifikasi) of Collante et al., *The Impact of Large Language
Models (LLMs) on Code Review Process*, arXiv:2508.11034, extended with
Oracle Database 23ai AI Vector Search (Oracle Academy course
*Introduction to Vector Search with Oracle Database 23ai*).

| RQ | Type | Question |
|---|---|---|
| RQ1 | Imitate | Do the paper's merge-time and review-phase findings hold for 2025-01-01 … 2026-10-31 PRs that mention any LLM tool? |
| RQ2 | Modify (Oracle vector search) | Does in-database embedding + k-NN (`VECTOR_DISTANCE`, COSINE) label LLM-assisted PRs better than the paper's regex heuristics H1–H4? |
| RQ3 | Modify (RAG) | Does a RAG pipeline (examples retrieved from Oracle) classify the LLM task type better than zero-shot prompting? |

## Repository layout

```
data/        dataset (CSV) + hand-label sheets in data/labels/
src/         one script per phase (00_… to 06_…), shared helpers in common.py
sql/         SQL run in Oracle (Phase 3, 6)
prompts/     every LLM prompt used (graded)
results/     console logs, tables, figures produced by the scripts
screenshots/ screenshots for the report
docs/        methodology notes (Bahasa Indonesia)
models/      ONNX model (not committed)
```

## Reproduce — Phase 0 (setup)

Tested target: Arch Linux, Python 3.11–3.13, Docker, Oracle Database Free (23ai).

```bash
# 1. Python env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env

# 2. Oracle Database Free in Docker, with ./models mounted as /opt/oracle/models
docker run -d --name oracle23ai -p 1521:1521 \
  -e ORACLE_PWD='<same as ORACLE_ADMIN_PASSWORD>' \
  -v oracle23ai-data:/opt/oracle/oradata \
  -v "$PWD/models":/opt/oracle/models:ro \
  container-registry.oracle.com/database/free:latest
docker logs -f oracle23ai          # wait for "DATABASE IS READY TO USE!"

# 3. vector memory pool for HNSW indexes, then restart
docker exec -i oracle23ai sqlplus -S / as sysdba <<'SQL'
ALTER SYSTEM SET vector_memory_size = 256M SCOPE = SPFILE;
SQL
docker restart oracle23ai

# 4. schema + check
python src/00_setup_db.py
python src/00_check_setup.py
```

Later phases are documented as they are completed.
