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
