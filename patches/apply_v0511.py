from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
requirements = ROOT / "backend" / "requirements.txt"
db_file = ROOT / "backend" / "app" / "db.py"

req = requirements.read_text(encoding="utf-8")
if "psycopg[binary]" not in req:
    req = req.rstrip() + "\npsycopg[binary]==3.2.3\n"
    requirements.write_text(req, encoding="utf-8")

source = db_file.read_text(encoding="utf-8")
old = '''connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
'''
new = '''database_url = settings.database_url.strip()
# Neon and other managed PostgreSQL providers commonly supply postgresql:// or
# postgres:// URLs. Use psycopg 3 explicitly so the deployment is deterministic.
if database_url.startswith("postgres://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]
elif database_url.startswith("postgresql://"):
    database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)
'''
if new not in source:
    if old not in source:
        raise SystemExit("Could not find expected SQLAlchemy engine block")
    source = source.replace(old, new)
    db_file.write_text(source, encoding="utf-8")
print("SMART BUY AI v0.5.11: PostgreSQL/Neon support enabled")
