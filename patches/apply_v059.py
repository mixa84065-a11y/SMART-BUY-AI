from pathlib import Path

registry_module = '''"""Remote registry for explicitly approved public merchant feeds."""
from __future__ import annotations
import json
import re
from urllib.parse import urlparse
import httpx
from .discovery import _validate_feed_url

MAX_REGISTRY_BYTES = 256 * 1024
_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,59}$")


def parse_registry(payload: str | bytes) -> dict:
    try:
        data = json.loads(payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("Feed registry must be valid JSON") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported feed registry schema_version")
    entries = data.get("feeds", [])
    if not isinstance(entries, list):
        raise ValueError("Feed registry feeds must be a list")
    clean, seen = [], set()
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("Each feed entry must be an object")
        if item.get("active") is not True:
            continue
        source = str(item.get("id", "")).strip().lower()
        name = str(item.get("name", "")).strip()
        url = str(item.get("url", "")).strip()
        if not _ID.fullmatch(source):
            raise ValueError("Feed id must contain 2-60 lowercase letters, digits, '_' or '-'")
        if source in seen:
            raise ValueError(f"Duplicate feed id: {source}")
        if not name or len(name) > 120:
            raise ValueError(f"Feed {source} must have a name up to 120 characters")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f"Feed {source} must use a public HTTPS URL")
        if parsed.port not in (None, 443):
            raise ValueError(f"Feed {source} must use standard HTTPS port 443")
        seen.add(source)
        clean.append({"id": source, "name": name, "url": url,
                      "format": str(item.get("format", "auto"))[:20],
                      "notes": str(item.get("notes", ""))[:300]})
    return {"version": str(data.get("version", "1"))[:40], "feeds": clean}


async def load_remote_registry(registry_url: str) -> dict:
    _validate_feed_url(registry_url)
    timeout = httpx.Timeout(12.0, connect=6.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False,
                                 headers={"User-Agent": "SMART-BUY-AI-Registry/1.0"}) as client:
        async with client.stream("GET", registry_url) as response:
            response.raise_for_status()
            if "html" in response.headers.get("content-type", "").lower():
                raise ValueError("Feed registry URL returned HTML, expected JSON")
            declared = response.headers.get("content-length")
            if declared and int(declared) > MAX_REGISTRY_BYTES:
                raise ValueError("Feed registry is larger than 256 KB")
            chunks, size = [], 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > MAX_REGISTRY_BYTES:
                    raise ValueError("Feed registry is larger than 256 KB")
                chunks.append(chunk)
    return parse_registry(b"".join(chunks))
'''
Path("backend/app/feed_registry.py").write_text(registry_module, encoding="utf-8")

p = Path("backend/app/config.py")
s = p.read_text(encoding="utf-8")
if "feed_registry_url:" not in s:
    s = s.replace(
        '    public_feed_urls: str = ""  # source=https://...;source2=https://...\n',
        '    public_feed_urls: str = ""  # source=https://...;source2=https://...\n'
        '    feed_registry_url: str = ""  # optional remote catalog/feeds.json URL\n')
    p.write_text(s, encoding="utf-8")

p = Path("backend/app/main.py")
s = p.read_text(encoding="utf-8")
if "from .feed_registry import load_remote_registry" not in s:
    s = s.replace("from .discovery import configured_feeds, fetch_feed\n",
                  "from .discovery import configured_feeds, fetch_feed\nfrom .feed_registry import load_remote_registry\n")
if "_feed_registry_cache:" not in s:
    s = s.replace("FEED_ERROR_RETRY_SECONDS = 300\n", '''FEED_ERROR_RETRY_SECONDS = 300
FEED_REGISTRY_TTL_SECONDS = 300
_feed_registry_cache: tuple[float, list[tuple[str, str]], dict] | None = None


async def _configured_feeds():
    """Merge environment feeds with active entries in the remote JSON registry."""
    global _feed_registry_cache
    feeds = configured_feeds(settings.public_feed_urls)
    registry_url = settings.feed_registry_url.strip()
    if not registry_url:
        return feeds, {"status": "not_configured", "note": "Удалённый реестр фидов не настроен"}
    now = time.monotonic()
    if _feed_registry_cache and now - _feed_registry_cache[0] < FEED_REGISTRY_TTL_SECONDS:
        remote, status = _feed_registry_cache[1], _feed_registry_cache[2]
    else:
        try:
            registry = await load_remote_registry(registry_url)
            remote = [(item["id"], item["url"]) for item in registry["feeds"]]
            status = {"status": "ok", "version": registry["version"],
                      "active_feeds": len(remote), "note": "Удалённый реестр загружен"}
            _feed_registry_cache = (now, remote, status)
        except Exception as exc:
            remote = []
            status = {"status": "error", "active_feeds": 0, "note": str(exc)[:200]}
            _feed_registry_cache = (now, remote, status)
    merged = {source: url for source, url in feeds}
    for source, url in remote:
        merged[source] = url
    return list(merged.items()), status
''', 1)

old = '''async def _refresh_configured_feeds(db: Session, force: bool = False):
    now = time.monotonic()
    feeds = configured_feeds(settings.public_feed_urls)
    if not feeds:
        return {"configured": 0, "imported": 0, "results": [], "note": "Открытые фиды не настроены"}
'''
new = '''async def _refresh_configured_feeds(db: Session, force: bool = False):
    now = time.monotonic()
    feeds, registry_status = await _configured_feeds()
    if not feeds:
        return {"configured": 0, "imported": 0, "results": [],
                "registry": registry_status,
                "note": "Нет активных разрешённых товарных фидов. Каталог магазинов не является источником цен."}
'''
if old not in s:
    raise SystemExit("feed refresh insertion point not found")
s = s.replace(old, new, 1)
s = s.replace('    return {"configured": len(feeds), "imported": total, "results": results}\n',
              '    return {"configured": len(feeds), "imported": total, "results": results, "registry": registry_status}\n', 1)

old = '''    feeds = configured_feeds(settings.public_feed_urls)
    if feeds:
        result.append({"source": "merchant_feeds", "status": "configured", "mode": "public_feed", "note": f"Настроено открытых фидов: {len(feeds)}"})
    return {"items": result, "live_data_enabled": bool(feeds), "automatic_discovery": "configured_feeds_only"}
'''
new = '''    feeds, registry_status = await _configured_feeds()
    for source, _url in feeds:
        cached = _feed_refresh_state.get(source)
        status = cached[1] if cached else "configured"
        note = cached[2] if cached else "Источник добавлен в реестр; доступность проверяется при обновлении"
        result.append({"source": source, "status": status, "mode": "public_feed", "note": note})
    return {"items": result, "live_data_enabled": bool(feeds),
            "feed_registry": registry_status,
            "automatic_discovery": "configured_feeds_only"}
'''
if old not in s:
    raise SystemExit("sources endpoint insertion point not found")
p.write_text(s.replace(old, new, 1), encoding="utf-8")

tests = Path("backend/tests/test_discovery.py")
t = tests.read_text(encoding="utf-8")
if "test_remote_feed_registry_accepts_only_active_https_sources" not in t:
    t += '''

def test_remote_feed_registry_accepts_only_active_https_sources():
    import json
    from app.feed_registry import parse_registry
    data = {"schema_version": 1, "version": "2026.11.1", "feeds": [
        {"id": "shop_one", "name": "Shop One", "url": "https://shop.example/feed.csv", "active": True},
        {"id": "shop_two", "name": "Shop Two", "url": "https://shop.example/off.xml", "active": False},
    ]}
    parsed = parse_registry(json.dumps(data))
    assert parsed["version"] == "2026.11.1"
    assert [x["id"] for x in parsed["feeds"]] == ["shop_one"]


def test_remote_feed_registry_rejects_http_and_duplicate_ids():
    import json
    import pytest
    from app.feed_registry import parse_registry
    insecure = {"schema_version": 1, "feeds": [
        {"id": "shop_one", "name": "Shop", "url": "http://shop.example/feed.xml", "active": True}
    ]}
    with pytest.raises(ValueError, match="HTTPS"):
        parse_registry(json.dumps(insecure))
    duplicate = {"schema_version": 1, "feeds": [
        {"id": "shop_one", "name": "Shop 1", "url": "https://one.example/feed.xml", "active": True},
        {"id": "shop_one", "name": "Shop 2", "url": "https://two.example/feed.xml", "active": True},
    ]}
    with pytest.raises(ValueError, match="Duplicate"):
        parse_registry(json.dumps(duplicate))


def test_remote_feed_registry_rejects_wrong_schema_and_bad_ids():
    import json
    import pytest
    from app.feed_registry import parse_registry
    with pytest.raises(ValueError, match="schema_version"):
        parse_registry(json.dumps({"schema_version": 2, "feeds": []}))
    bad_id = {"schema_version": 1, "feeds": [
        {"id": "Bad ID", "name": "Shop", "url": "https://shop.example/feed.xml", "active": True}
    ]}
    with pytest.raises(ValueError, match="Feed id"):
        parse_registry(json.dumps(bad_id))
'''
    tests.write_text(t, encoding="utf-8")

readme = Path("backend/README.md")
r = readme.read_text(encoding="utf-8")
if "Remote feed registry (v0.5.9)" not in r:
    r += '''

### Remote feed registry (v0.5.9)
- FEED_REGISTRY_URL optionally points to a remote JSON registry such as the repository's catalog/feeds.json.
- Active feeds are loaded and cached for five minutes. Registry edits do not require an APK update or backend code deployment.
- Entries must be explicitly active and use public HTTPS URLs. Redirects, private/local hosts, credentials, HTML responses and oversized registry files are rejected. Each product feed is validated separately.
- PUBLIC_FEED_URLS remains supported as an operator fallback. A store is live only after an approved feed URL is configured and successfully imported.

Example server setting:
FEED_REGISTRY_URL=https://raw.githubusercontent.com/mixa84065-a11y/SMART-BUY-AI/main/catalog/feeds.json
'''
    readme.write_text(r, encoding="utf-8")

gradle = Path("app/build.gradle")
g = gradle.read_text(encoding="utf-8")
g2 = g.replace("versionCode 18", "versionCode 19", 1).replace("versionName '0.5.8'", "versionName '0.5.9'", 1)
if g2 == g:
    raise SystemExit("Expected v0.5.8 version markers were not found")
gradle.write_text(g2, encoding="utf-8")
