from pathlib import Path

main = Path("backend/app/main.py")
source = main.read_text(encoding="utf-8")

if "from sqlalchemy import func" not in source:
    source = source.replace(
        "from sqlalchemy import or_, select",
        "from sqlalchemy import func, or_, select",
        1,
    )

anchor = '@app.get("/v1/products", response_model=list[ProductOut])'
if "async def catalog_status(" not in source:
    endpoint = r'''

@app.get("/v1/catalog/status")
async def catalog_status(db: Session = Depends(get_db)):
    """Honest server-side catalogue coverage; never counts store names as products."""
    feeds, registry_status = await _configured_feeds()
    product_count = db.scalar(select(func.count(Product.id))) or 0
    offer_count = db.scalar(select(func.count(Offer.id))) or 0
    review_count = db.scalar(select(func.count(Review.id))) or 0
    snapshot_count = db.scalar(select(func.count(PriceSnapshot.id))) or 0
    last_price_update = db.scalar(select(func.max(PriceSnapshot.observed_at)))
    return {
        "catalog": "SMART BUY AI",
        "products": product_count,
        "offers": offer_count,
        "reviews": review_count,
        "price_history_points": snapshot_count,
        "configured_public_feeds": len(feeds),
        "feed_registry": registry_status,
        "last_price_update": last_price_update.isoformat() if last_price_update else None,
        "data_status": "live" if offer_count else "awaiting_sources",
        "notice": (
            "Показатели отражают только реально импортированные данные. "
            "Список магазинов не считается каталогом товаров; цены и отзывы не создаются автоматически."
        ),
    }

'''
    if anchor not in source:
        raise SystemExit("Could not locate product search route in backend/app/main.py")
    source = source.replace(anchor, endpoint + anchor, 1)

main.write_text(source, encoding="utf-8")
print("Added /v1/catalog/status with real database and feed counts.")
