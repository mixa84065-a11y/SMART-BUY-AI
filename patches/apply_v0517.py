from pathlib import Path

p = Path("backend/app/main.py")
if not p.is_file():
    raise SystemExit(f"FastAPI entrypoint not found: {p}")

source = p.read_text(encoding="utf-8")
old = '''@app.middleware("http")
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
new = '''@app.middleware("http")
async def optional_api_key(request, call_next):
    # Public GET endpoints are used by the Android client. Mutating operations
    # and forced feed refreshes require the server-side operator key.
    protected = request.url.path.startswith("/v1/") and (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        or request.url.path == "/v1/discovery/refresh"
    )
    if protected:
        from starlette.responses import JSONResponse
        if not settings.api_key:
            return JSONResponse(
                status_code=503,
                content={"detail": "Server write access is not configured"},
            )
        if request.headers.get("x-api-key") != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"},
            )
    return await call_next(request)
'''
if new not in source:
    if old not in source:
        raise SystemExit("API-key middleware anchor not found; refusing unsafe patch")
    source = source.replace(old, new, 1)
    p.write_text(source, encoding="utf-8")
print("API-key middleware now returns proper JSON 401/503 responses.")
