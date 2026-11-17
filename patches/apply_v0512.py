from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_FILE = ROOT / "backend" / "app" / "main.py"
TOKEN = "m79o9kluxqex2vc9"

if not APP_FILE.is_file():
    raise SystemExit(f"FastAPI entrypoint not found: {APP_FILE}")

source = APP_FILE.read_text(encoding="utf-8")
route_marker = '@app.get("/yandex-verification"'
if route_marker not in source:
    route = f'''

@app.get("/yandex-verification", include_in_schema=False)
def yandex_verification():
    """Public ownership-verification endpoint for Yandex Distribution."""
    return {{"verification_code": "{TOKEN}"}}
'''
    APP_FILE.write_text(source.rstrip() + "\n" + route + "\n", encoding="utf-8")

print(f"SMART BUY AI Yandex verification route added to {APP_FILE}")
