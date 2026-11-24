"""Phase 0 - environment check.

1. Python + package versions
2. GitHub token + rate limits + one tiny Search API call
3. Oracle connection (python-oracledb thin mode) as the app user
4. Vector smoke test that re-uses the 2-D example vectors from the
   Oracle Academy lesson ("What is a Vector, 2 of 2"):
   [1,1] [3,5] [8,2] [5,-3] [-6,-6] [-8,7]
   - VECTOR_DISTANCE with EUCLIDEAN, COSINE and MANHATTAN
   - exact k-NN search with ORDER BY VECTOR_DISTANCE ... FETCH FIRST k ROWS ONLY
5. Is the ONNX model file visible through the MODEL_DIR directory object?

    python src/00_check_setup.py
"""
import platform
import sys
from importlib.metadata import PackageNotFoundError, version

from common import env, github_session, oracle_connect, tee_output

PACKAGES = ["oracledb", "requests", "python-dotenv", "pandas", "numpy", "scipy",
            "statsmodels", "scikit-learn", "matplotlib", "tqdm"]
COURSE_VECTORS = [[1, 1], [3, 5], [8, 2], [5, -3], [-6, -6], [-8, 7]]
QUERY = [2, 2]
ok = {}


def section(title):
    print(f"\n=== {title} ===")


with tee_output("00_setup_check.txt"):
    # ------------------------------------------------------------------ 1
    section("1. Python & packages")
    print(f"Python {sys.version.split()[0]} on {platform.platform()}")
    missing = []
    for p in PACKAGES:
        try:
            print(f"  {p:<15} {version(p)}")
        except PackageNotFoundError:
            print(f"  {p:<15} MISSING")
            missing.append(p)
    ok["packages"] = not missing

    # ------------------------------------------------------------------ 2
    section("2. GitHub API")
    try:
        gh = github_session()
        me = gh.get("https://api.github.com/user", timeout=30)
        me.raise_for_status()
        print(f"  token belongs to: {me.json().get('login')}")
        rl = gh.get("https://api.github.com/rate_limit", timeout=30).json()["resources"]
        print(f"  core   limit {rl['core']['limit']:>5}, remaining {rl['core']['remaining']}")
        print(f"  search limit {rl['search']['limit']:>5}, remaining {rl['search']['remaining']}")
        start = env("COLLECT_START", "2025-01-01")
        q = f"is:pr is:public GPT in:title created:{start}..{start}"
        r = gh.get("https://api.github.com/search/issues",
                   params={"q": q, "per_page": 1}, timeout=30)
        r.raise_for_status()
        print(f"  search test  q='{q}'  total_count={r.json()['total_count']}")
        ok["github"] = True
    except Exception as e:  # noqa: BLE001
        print(f"  [FAIL] {type(e).__name__}: {e}")
        ok["github"] = False

    # ------------------------------------------------------------------ 3
    section("3. Oracle connection (python-oracledb thin mode)")
    try:
        import oracledb

        print(f"  python-oracledb {oracledb.__version__}, thin mode = {oracledb.is_thin_mode()}")
        conn = oracle_connect()
        cur = conn.cursor()
        print(f"  connected as {conn.username} @ {env('ORACLE_DSN')}")
        print(f"  server version: {conn.version}")
        ok["oracle"] = True
        try:
            banner = cur.execute("SELECT banner_full FROM v$version").fetchone()
            if banner:
                print("  " + banner[0].replace("\n", "\n  "))
        except Exception:  # noqa: BLE001  (v$version may be hidden from app users)
            pass
    except Exception as e:  # noqa: BLE001
        print(f"  [FAIL] {type(e).__name__}: {e}")
        ok["oracle"] = False

    # ------------------------------------------------------------------ 4
    if ok.get("oracle"):
        section("4. Vector smoke test (Oracle Academy example vectors)")
        try:
            a, b = "[1,1]", "[3,5]"
            for metric in ("EUCLIDEAN", "COSINE", "MANHATTAN", "DOT"):
                d = cur.execute(
                    f"SELECT VECTOR_DISTANCE(TO_VECTOR(:a), TO_VECTOR(:b), {metric}) FROM dual",
                    a=a, b=b).fetchone()[0]
                print(f"  VECTOR_DISTANCE({a}, {b}, {metric:<9}) = {d:.4f}")

            cur.execute("""
                BEGIN
                  EXECUTE IMMEDIATE 'DROP TABLE phase0_vec PURGE';
                EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
                END;""")
            cur.execute("CREATE TABLE phase0_vec (id NUMBER PRIMARY KEY, v VECTOR(2, FLOAT32))")
            cur.executemany("INSERT INTO phase0_vec VALUES (:1, TO_VECTOR(:2))",
                            [(i + 1, str(v)) for i, v in enumerate(COURSE_VECTORS)])
            conn.commit()

            print(f"\n  Exact k-NN (k=3) for query {QUERY}, EUCLIDEAN:")
            rows = cur.execute("""
                SELECT id, FROM_VECTOR(v) AS vec,
                       VECTOR_DISTANCE(v, TO_VECTOR(:q), EUCLIDEAN) AS dist
                FROM phase0_vec
                ORDER BY dist
                FETCH FIRST 3 ROWS ONLY""", q=str(QUERY)).fetchall()
            for r in rows:
                print(f"    id={r[0]}  v={r[1]:<14} dist={r[2]:.4f}")
            cur.execute("DROP TABLE phase0_vec PURGE")
            ok["vector"] = True
        except Exception as e:  # noqa: BLE001
            print(f"  [FAIL] {type(e).__name__}: {e}")
            ok["vector"] = False

        # -------------------------------------------------------------- 5
        section("5. ONNX model directory")
        try:
            path = cur.execute(
                "SELECT directory_path FROM all_directories WHERE directory_name = 'MODEL_DIR'"
            ).fetchone()
            print(f"  MODEL_DIR -> {path[0] if path else 'NOT FOUND (run src/00_setup_db.py)'}")
            fname = env("ONNX_MODEL_FILE", "all_MiniLM_L12_v2.onnx")
            exists = cur.execute(
                "SELECT DBMS_LOB.FILEEXISTS(BFILENAME('MODEL_DIR', :f)) FROM dual", f=fname
            ).fetchone()[0]
            print(f"  {fname} visible to the database: {'YES' if exists == 1 else 'NO'}")
            ok["onnx_file"] = exists == 1
            vmem = cur.execute(
                "SELECT value FROM v$parameter WHERE name = 'vector_memory_size'").fetchone()
            print(f"  vector_memory_size = {vmem[0] if vmem else 'not visible to this user'}")
        except Exception as e:  # noqa: BLE001
            print(f"  [WARN] {type(e).__name__}: {e}")
            ok["onnx_file"] = False
        conn.close()

    section("SUMMARY")
    for k, v in ok.items():
        print(f"  {k:<10} {'OK' if v else 'FAIL'}")
