from pathlib import Path

main = Path("backend/app/main.py")
s = main.read_text(encoding="utf-8")
s = s.replace("_last_feed_refresh = 0.0", """# Per-source cooldown prevents one broken feed from blocking healthy feeds.
_feed_refresh_state: dict[str, tuple[float, str, str]] = {}
FEED_REFRESH_TTL_SECONDS = 1800
FEED_ERROR_RETRY_SECONDS = 300


def _feed_cache_state(source: str, now: float, force: bool = False):
    cached = _feed_refresh_state.get(source)
    if force or cached is None:
        return None
    refreshed_at, status, note = cached
    ttl = FEED_ERROR_RETRY_SECONDS if status == "error" else FEED_REFRESH_TTL_SECONDS
    if now - refreshed_at >= ttl:
        return None
    return {"source": source, "status": "cached", "imported": 0,
            "last_status": status, "note": note}
""")
old = '''async def _refresh_configured_feeds(db: Session, force: bool = False):
    global _last_feed_refresh
    now = time.monotonic()
    feeds = configured_feeds(settings.public_feed_urls)
    if not feeds:
        return {"configured": 0, "imported": 0, "results": [], "note": "Открытые фиды не настроены"}
    if not force and now - _last_feed_refresh < 1800:
        return {"configured": len(feeds), "imported": 0, "results": [], "note": "Используем недавно обновлённый каталог"}
    results, total = [], 0
    for source, url in feeds:
        try:
            rows = await fetch_feed(source, url)
            if not rows:
                results.append({"source": source, "status": "empty", "imported": 0})
                continue
            result = import_partner_feed(FeedImportIn(source=source, offers=rows[:1000]), db)
            count = result["created_offers"] + result["updated_offers"]
            total += count
            results.append({"source": source, "status": "ok", "imported": len(rows), "created": result["created_offers"], "updated": result["updated_offers"]})
        except Exception as exc:
            results.append({"source": source, "status": "error", "imported": 0, "reason": str(exc)[:240]})
    _last_feed_refresh = now
    return {"configured": len(feeds), "imported": total, "results": results}
'''
new = '''async def _refresh_configured_feeds(db: Session, force: bool = False):
    now = time.monotonic()
    feeds = configured_feeds(settings.public_feed_urls)
    if not feeds:
        return {"configured": 0, "imported": 0, "results": [], "note": "Открытые фиды не настроены"}
    results, total = [], 0
    for source, url in feeds:
        cached = _feed_cache_state(source, now, force)
        if cached is not None:
            results.append(cached)
            continue
        try:
            rows = await fetch_feed(source, url)
            if not rows:
                note = "Фид доступен, но не содержит распознаваемых товаров"
                _feed_refresh_state[source] = (now, "empty", note)
                results.append({"source": source, "status": "empty", "imported": 0, "note": note})
                continue
            result = import_partner_feed(FeedImportIn(source=source, offers=rows[:1000]), db)
            total += result["created_offers"] + result["updated_offers"]
            note = "Фид успешно обновлён"
            _feed_refresh_state[source] = (now, "ok", note)
            results.append({"source": source, "status": "ok", "imported": min(len(rows), 1000), "created": result["created_offers"], "updated": result["updated_offers"]})
        except Exception as exc:
            note = str(exc)[:240]
            _feed_refresh_state[source] = (now, "error", note)
            results.append({"source": source, "status": "error", "imported": 0, "reason": note, "retry_after_seconds": FEED_ERROR_RETRY_SECONDS})
    return {"configured": len(feeds), "imported": total, "results": results}
'''
if old not in s:
    raise SystemExit("v0.5.7 feed refresh anchor not found")
main.write_text(s.replace(old, new, 1), encoding="utf-8")

tests = Path("backend/tests/test_discovery.py")
t = tests.read_text(encoding="utf-8")
if "test_feed_refresh_cooldown_is_per_source_and_shorter_after_error" not in t:
    t += '''

def test_feed_refresh_cooldown_is_per_source_and_shorter_after_error():
    from app import main
    main._feed_refresh_state.clear()
    main._feed_refresh_state["broken_shop"] = (100.0, "error", "timeout")
    main._feed_refresh_state["working_shop"] = (100.0, "ok", "updated")
    assert main._feed_cache_state("broken_shop", 399.0) is not None
    assert main._feed_cache_state("broken_shop", 401.0) is None
    assert main._feed_cache_state("working_shop", 1799.0) is not None
    assert main._feed_cache_state("working_shop", 1901.0) is None
    assert main._feed_cache_state("working_shop", 101.0, force=True) is None
    main._feed_refresh_state.clear()
'''
    tests.write_text(t, encoding="utf-8")

gradle = Path("app/build.gradle")
g = gradle.read_text(encoding="utf-8")
g2 = g.replace("versionCode 16", "versionCode 17", 1).replace("versionName '0.5.6'", "versionName '0.5.7'", 1)
if g2 == g:
    raise SystemExit("Expected v0.5.6 version markers were not found")
gradle.write_text(g2, encoding="utf-8")

readme = Path("backend/README.md")
r = readme.read_text(encoding="utf-8")
if "### Feed refresh reliability (v0.5.7)" not in r:
    r += '''

### Feed refresh reliability (v0.5.7)
- Refresh cooldown is tracked independently for each configured public feed.
- A failed feed is retried after five minutes; a successful or empty feed is cached for 30 minutes.
- One unavailable shop no longer prevents other configured feeds from refreshing.
- Manual refresh bypasses cooldowns. Only explicitly configured HTTPS structured feeds are fetched.
'''
    readme.write_text(r, encoding="utf-8")
