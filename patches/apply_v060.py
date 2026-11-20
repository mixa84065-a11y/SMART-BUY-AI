from pathlib import Path

# Wire authorized Pampadu merchant exports into the existing public-feed importer.
# Keep this patch narrow: previous source-code anchors were brittle and broke builds.
main = Path("backend/app/main.py")
if not main.is_file():
    raise SystemExit(f"FastAPI entrypoint not found: {main}")

source = main.read_text(encoding="utf-8")
marker = "# SMART_BUY_AI_PAMPADU_ENV_FEEDS"
if marker not in source:
    source += r'''

# SMART_BUY_AI_PAMPADU_ENV_FEEDS
def _smartbuy_add_pampadu_feeds():
    import os
    configured = str(getattr(settings, "public_feed_urls", "") or "").strip().rstrip(";")
    additions = []
    env_sources = (
        ("hoff", "PAMPADU_HOFF_FEED_URL"),
        ("cozy_home", "PAMPADU_COZY_HOME_FEED_URL"),
        ("adamas", "PAMPADU_ADAMAS_FEED_URL"),
        ("dogeat", "PAMPADU_DOGEAT_FEED_URL"),
        ("ekonika", "PAMPADU_EKONIKA_FEED_URL"),
        ("koleso", "PAMPADU_KOLESO_FEED_URL"),
        ("citilink", "PAMPADU_CITILINK_FEED_URL"),
        ("thomas_munz", "PAMPADU_THOMAS_MUNZ_FEED_URL"),
        ("goldapple", "PAMPADU_GOLDAPPLE_FEED_URL"),
        ("shopping_live", "PAMPADU_SHOPPING_LIVE_FEED_URL"),
        ("bethowen", "PAMPADU_BETHOWEN_FEED_URL"),
    )
    for source_id, env_name in env_sources:
        url = os.environ.get(env_name, "").strip()
        if url:
            additions.append(f"{source_id}={url}")
    if additions:
        by_source = {}
        for item in [part for part in configured.split(";") if part.strip()] + additions:
            if "=" in item:
                key, value = item.split("=", 1)
                by_source[key.strip()] = value.strip()
        settings.public_feed_urls = ";".join(f"{key}={value}" for key, value in by_source.items())

_smartbuy_add_pampadu_feeds()
'''
    main.write_text(source, encoding="utf-8")

print("Connected authorized Pampadu exports to the existing public-feed importer.")


# SMART_BUY_AI_PAMPADU_STARTUP_IMPORT
# Run the existing importer once after each backend start when explicitly enabled.
# This avoids depending on an operator-only POST endpoint for the first catalogue fill.
main = Path("backend/app/main.py")
source = main.read_text(encoding="utf-8")
startup_marker = "# SMART_BUY_AI_PAMPADU_STARTUP_IMPORT"
if startup_marker not in source:
    source += r'''

# SMART_BUY_AI_PAMPADU_STARTUP_IMPORT
import inspect as _smartbuy_inspect
import logging as _smartbuy_logging
import os as _smartbuy_os
from datetime import datetime as _smartbuy_datetime, timezone as _smartbuy_timezone

_SMARTBUY_FEED_IMPORT_STATE = {
    "status": "not_started",
    "started_at": None,
    "finished_at": None,
    "detail": "Автоимпорт ожидает запуска backend.",
}

async def _smartbuy_pampadu_import_worker():
    if _smartbuy_os.getenv("PAMPADU_AUTO_IMPORT_ON_STARTUP", "false").strip().lower() != "true":
        return
    import logging
    logger = logging.getLogger("smartbuy.feed_import")
    _SMARTBUY_FEED_IMPORT_STATE["status"] = "running"
    _SMARTBUY_FEED_IMPORT_STATE["started_at"] = _smartbuy_datetime.now(_smartbuy_timezone.utc).isoformat()
    _SMARTBUY_FEED_IMPORT_STATE["detail"] = "Запущен штатный импорт настроенных товарных фидов."
    db_generator = None
    try:
        refresh = globals().get("_refresh_configured_feeds")
        if not callable(refresh):
            raise RuntimeError("Штатная функция _refresh_configured_feeds не найдена.")
        get_db_fn = globals().get("get_db")
        if not callable(get_db_fn):
            raise RuntimeError("Функция get_db не найдена; сессию БД создать нельзя.")
        db_generator = get_db_fn()
        db = next(db_generator)
        signature = _smartbuy_inspect.signature(refresh)
        kwargs = {}
        args = []
        for parameter in signature.parameters.values():
            if parameter.name in {"db", "session", "database"}:
                if parameter.kind == _smartbuy_inspect.Parameter.POSITIONAL_ONLY:
                    args.append(db)
                else:
                    kwargs[parameter.name] = db
            elif parameter.name in {"settings", "config"}:
                if parameter.kind == _smartbuy_inspect.Parameter.POSITIONAL_ONLY:
                    args.append(globals().get("settings"))
                else:
                    kwargs[parameter.name] = globals().get("settings")
            elif parameter.default is _smartbuy_inspect.Parameter.empty and parameter.kind not in {
                _smartbuy_inspect.Parameter.VAR_POSITIONAL,
                _smartbuy_inspect.Parameter.VAR_KEYWORD,
            }:
                raise RuntimeError("Неизвестный обязательный параметр импортера: " + parameter.name)
        result = refresh(*args, **kwargs)
        if _smartbuy_inspect.isawaitable(result):
            import asyncio as _smartbuy_asyncio
            result = await _smartbuy_asyncio.wait_for(result, timeout=55)
        _SMARTBUY_FEED_IMPORT_STATE["status"] = "completed"
        _SMARTBUY_FEED_IMPORT_STATE["detail"] = (
            str(result)[:800] if result is not None
            else "Штатная функция импорта завершилась без исключения."
        )
        logger.info("SMART BUY AI Pampadu startup import completed: %s", _SMARTBUY_FEED_IMPORT_STATE["detail"])
    except Exception as exc:
        _SMARTBUY_FEED_IMPORT_STATE["status"] = "error"
        _SMARTBUY_FEED_IMPORT_STATE["detail"] = type(exc).__name__ + ": " + str(exc)[:700]
        logger.exception("SMART BUY AI Pampadu startup import failed")
    finally:
        if db_generator is not None:
            try:
                db_generator.close()
            except Exception:
                pass
        _SMARTBUY_FEED_IMPORT_STATE["finished_at"] = _smartbuy_datetime.now(_smartbuy_timezone.utc).isoformat()


@app.get("/v1/sources/import-status")
async def smartbuy_feed_import_status():
    return dict(_SMARTBUY_FEED_IMPORT_STATE)
'''
    main.write_text(source, encoding="utf-8")

print("Added opt-in startup execution and a safe import-status endpoint for the existing feed importer.")


# SMART_BUY_AI_IMPORT_DIAGNOSTICS
# Emit a safe, token-free startup summary after the importer hook has run.
main = Path("backend/app/main.py")
source = main.read_text(encoding="utf-8")
diagnostic_marker = "# SMART_BUY_AI_IMPORT_DIAGNOSTICS"
if diagnostic_marker not in source:
    source += r'''

# SMART_BUY_AI_IMPORT_DIAGNOSTICS
@app.on_event("startup")
async def _smartbuy_log_import_diagnostics():
    import logging as _smartbuy_diag_logging
    import os as _smartbuy_diag_os
    logger = _smartbuy_diag_logging.getLogger("smartbuy.feed_import")
    enabled = _smartbuy_diag_os.getenv("PAMPADU_AUTO_IMPORT_ON_STARTUP", "false").strip().lower() == "true"
    state = globals().get("_SMARTBUY_FEED_IMPORT_STATE", {})
    refresh = globals().get("_refresh_configured_feeds")
    logger.info(
        "SMART BUY AI import diagnostics: enabled=%s importer_found=%s state=%s detail=%s",
        enabled, callable(refresh), state.get("status", "missing"), str(state.get("detail", ""))[:500]
    )
'''
    main.write_text(source, encoding="utf-8")
print("Added token-free startup diagnostics for the Pampadu importer.")

# Keep application startup responsive: run feed refresh in a managed background task.
main = Path("backend/app/main.py")
source = main.read_text(encoding="utf-8")
background_marker = "# SMART_BUY_AI_PAMPADU_BACKGROUND_STARTUP"
if background_marker not in source:
    source += r"""

# SMART_BUY_AI_PAMPADU_BACKGROUND_STARTUP
_SMARTBUY_IMPORT_TASK = None

@app.on_event("startup")
async def _smartbuy_pampadu_startup_import():
    import asyncio as _smartbuy_asyncio
    import os as _smartbuy_background_os
    import logging as _smartbuy_background_logging
    global _SMARTBUY_IMPORT_TASK
    if _smartbuy_background_os.getenv("PAMPADU_AUTO_IMPORT_ON_STARTUP", "false").strip().lower() != "true":
        return
    _SMARTBUY_IMPORT_TASK = _smartbuy_asyncio.create_task(_smartbuy_pampadu_import_worker())
    _smartbuy_background_logging.getLogger("smartbuy.feed_import").info("SMART BUY AI Pampadu import queued in background.")
"""
    main.write_text(source, encoding="utf-8")
print("Moved Pampadu import out of blocking startup and added a 55-second async timeout.")
