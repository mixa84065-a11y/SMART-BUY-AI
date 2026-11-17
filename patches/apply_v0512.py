from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "m79o9kluxqex2vc9"
ROUTE = f'''

@app.get("/yandex-verification", include_in_schema=False)
def yandex_verification():
    """Public ownership-verification page for Yandex Distribution."""
    return {{"verification_code": "{TOKEN}"}}
'''

candidates = []
for path in ROOT.rglob("*.py"):
    if any(part in {".venv", "venv", "__pycache__", "tests"} for part in path.parts):
        continue
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    if "FastAPI(" in source and ("app =" in source or "app=" in source):
        candidates.append((path, source))

if not candidates:
    raise SystemExit("Could not locate FastAPI app entrypoint; refusing to patch an unknown file")

path, source = candidates[0]
if '"/yandex-verification"' not in source:
    source = source.rstrip() + "\n" + ROUTE
    path.write_text(source + "\n", encoding="utf-8")

print(f"SMART BUY AI Yandex verification route added to {path}")
