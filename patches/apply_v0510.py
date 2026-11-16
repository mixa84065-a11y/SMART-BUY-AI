from pathlib import Path

p = Path("backend/app/main.py")
s = p.read_text(encoding="utf-8")
old = '''@app.middleware("http")
async def optional_api_key(request, call_next):
    protected = request.url.path.startswith("/v1/") and request.url.path not in {"/v1/sources", "/v1/discovery/search"}
    if protected and settings.api_key:
        if request.headers.get("x-api-key") != settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return await call_next(request)
'''
new = '''@app.middleware("http")
async def optional_api_key(request, call_next):
    # Public GET endpoints are used by the Android client. Mutating operations
    # and forced feed refreshes require the server-side operator key.
    protected = request.url.path.startswith("/v1/") and (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        or request.url.path == "/v1/discovery/refresh"
    )
    if protected:
        if not settings.api_key:
            raise HTTPException(status_code=503, detail="Server write access is not configured")
        if request.headers.get("x-api-key") != settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return await call_next(request)
'''
if old not in s:
    raise SystemExit("API-key middleware anchor not found")
p.write_text(s.replace(old, new, 1), encoding="utf-8")

