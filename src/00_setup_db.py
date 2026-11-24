"""Phase 0 - one-time Oracle setup (run as the admin user SYSTEM).

Creates the application schema used by all later phases and the directory
object MODEL_DIR that points to the ONNX model folder mounted in the container.

    python src/00_setup_db.py
"""
import re
import sys

from common import env, oracle_connect, tee_output

APP_USER = env("ORACLE_USER", required=True)
APP_PWD = env("ORACLE_PASSWORD", required=True)
MODEL_PATH = env("ORACLE_MODEL_DIR_PATH", "/opt/oracle/models")

# basic validation, because user name / password are put into DDL text
if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,29}", APP_USER):
    sys.exit("[ERROR] ORACLE_USER must be letters/digits/underscore and start with a letter")
if '"' in APP_PWD or "'" in MODEL_PATH:
    sys.exit("[ERROR] ORACLE_PASSWORD must not contain double quotes")


def run(cur, sql, label=None):
    print(f"  -> {label or sql}")
    cur.execute(sql)


with tee_output("00_setup_db.txt"):
    print("=== Phase 0: Oracle schema setup ===")
    with oracle_connect(admin=True) as conn:
        cur = conn.cursor()
        print(f"Connected as {conn.username} to {env('ORACLE_DSN')}, server version {conn.version}")

        exists = cur.execute(
            "SELECT COUNT(*) FROM all_users WHERE username = UPPER(:u)", u=APP_USER
        ).fetchone()[0]
        if exists:
            print(f"User {APP_USER.upper()} already exists - only re-applying grants")
        else:
            run(
                cur,
                f'CREATE USER {APP_USER} IDENTIFIED BY "{APP_PWD}" '
                f"DEFAULT TABLESPACE users QUOTA UNLIMITED ON users",
                f"CREATE USER {APP_USER} ... QUOTA UNLIMITED ON users",
            )

        # DB_DEVELOPER_ROLE is the 23ai developer role; CREATE MINING MODEL is
        # needed by DBMS_VECTOR.LOAD_ONNX_MODEL (Phase 3).
        for grant in ("CREATE SESSION", "DB_DEVELOPER_ROLE", "CREATE MINING MODEL"):
            run(cur, f"GRANT {grant} TO {APP_USER}")

        run(cur, f"CREATE OR REPLACE DIRECTORY MODEL_DIR AS '{MODEL_PATH}'")
        run(cur, f"GRANT READ, WRITE ON DIRECTORY MODEL_DIR TO {APP_USER}")

        vmem = cur.execute(
            "SELECT value FROM v$parameter WHERE name = 'vector_memory_size'"
        ).fetchone()
        print(f"\nvector_memory_size = {vmem[0] if vmem else 'n/a'} "
              "(must be > 0 to build an HNSW index in Phase 3)")
    print("Setup finished.")
