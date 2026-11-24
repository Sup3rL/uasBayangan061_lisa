"""Shared helpers for every phase: paths, .env loading, Oracle connection,
GitHub session and a small "tee" logger that writes console output to /results.
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
LABEL_DIR = DATA_DIR / "labels"
RESULTS_DIR = ROOT / "results"
PROMPTS_DIR = ROOT / "prompts"
SQL_DIR = ROOT / "sql"
MODELS_DIR = ROOT / "models"

for _d in (DATA_DIR, RAW_DIR, LABEL_DIR, RESULTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")


def env(name: str, default: str | None = None, required: bool = False) -> str | None:
    """Read a variable from .env / the environment."""
    value = os.getenv(name, default)
    if required and not value:
        sys.exit(f"[ERROR] {name} is empty. Fill it in .env (see .env.example).")
    return value


def oracle_connect(admin: bool = False):
    """Open a python-oracledb connection (thin mode, no Instant Client needed)."""
    import oracledb

    dsn = env("ORACLE_DSN", "localhost:1521/FREEPDB1")
    if admin:
        user = env("ORACLE_ADMIN_USER", "system")
        pwd = env("ORACLE_ADMIN_PASSWORD", required=True)
    else:
        user = env("ORACLE_USER", required=True)
        pwd = env("ORACLE_PASSWORD", required=True)
    return oracledb.connect(user=user, password=pwd, dsn=dsn)


def github_session():
    """requests.Session pre-configured for the GitHub REST API."""
    import requests

    s = requests.Session()
    s.headers.update(
        {
            "Authorization": f"Bearer {env('GITHUB_TOKEN', required=True)}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "uas-llm-code-review-replication",
        }
    )
    return s


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()


@contextmanager
def tee_output(filename: str):
    """Everything printed inside the block is also saved to results/<filename>."""
    path = RESULTS_DIR / filename
    with open(path, "w", encoding="utf-8") as fh:
        old = sys.stdout
        sys.stdout = _Tee(old, fh)
        try:
            yield path
        finally:
            sys.stdout = old
    print(f"\n[saved] {path.relative_to(ROOT)}")
