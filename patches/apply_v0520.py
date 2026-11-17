from pathlib import Path

main = Path("backend/app/main.py")
source = main.read_text(encoding="utf-8")
if "from fastapi.middleware.cors import CORSMiddleware" not in source:
    source = "from fastapi.middleware.cors import CORSMiddleware\n" + source
cors = '''
# Public read-only search is consumed by the SMART BUY AI website.
# Android clients are not subject to browser CORS restrictions.
if not getattr(app.state, "smart_buy_cors_installed", False):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://smart-buy-ai-site.onrender.com",
            "https://smart-buy-ai.onrender.com",
        ],
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Accept", "Content-Type"],
    )
    app.state.smart_buy_cors_installed = True
'''
if "smart_buy_cors_installed" not in source:
    source = source.rstrip() + "\n\n" + cors + "\n"
main.write_text(source, encoding="utf-8")
print("SMART BUY AI website CORS enabled for read-only GET/OPTIONS requests.")
