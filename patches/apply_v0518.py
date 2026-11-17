from pathlib import Path

module = Path("/app/backend/app/yandex_affiliate.py")
if not module.is_file():
    raise SystemExit(f"Yandex adapter not found: {module}")

source = module.read_text(encoding="utf-8")
anchor = '''    return {
        "provider": "yandex_market",
        "status": "ok",
'''
replacement = '''    referral_url = str(link.get("url") or "")
    if "showcaptcha" in referral_url.lower():
        return {
            "provider": "yandex_market",
            "status": "captcha_required",
            "title": None,
            "image": None,
            "price": None,
            "stock_amount": None,
            "reward": None,
            "discount": None,
            "referral_url": None,
            "short_url": None,
            "source_label": "Данные сервиса Яндекс Маркет",
            "source_url": "https://market.yandex.ru/",
            "catalog_search_supported": False,
            "notice": "Яндекс Маркет запросил CAPTCHA. Данные товара не получены; повторите запрос позже."
        }

    return {
        "provider": "yandex_market",
        "status": "ok",
'''
if anchor not in source:
    raise SystemExit("Expected response block not found; refusing to patch.")
module.write_text(source.replace(anchor, replacement, 1), encoding="utf-8")
print("Yandex CAPTCHA responses are now reported explicitly.")
