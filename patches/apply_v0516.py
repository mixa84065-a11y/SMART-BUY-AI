from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_FILE = ROOT / "backend" / "app" / "main.py"
MODULE_FILE = ROOT / "backend" / "app" / "yandex_affiliate.py"

if not APP_FILE.is_file():
    raise SystemExit(f"FastAPI entrypoint not found: {APP_FILE}")

module = r'''"""Yandex Market Affiliate API adapter.

This API is not a general-purpose product search/catalog API. It supports
referral-link/article operations and order reporting. The link-create response
can include metadata for the supplied Market product URL.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/v1/integrations/yandex", tags=["integrations"])


class _MarketRedirectHandler(HTTPRedirectHandler):
    """Follow short links only while every redirect stays on Yandex Market."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlparse(newurl)
        if target.scheme != "https" or target.hostname not in {
            "market.yandex.ru", "www.market.yandex.ru"
        } or target.username or target.password:
            raise HTTPError(newurl, code, "Redirect left Yandex Market", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _resolve_market_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "market.yandex.ru", "www.market.yandex.ru"
    } or parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="Укажите HTTPS-ссылку market.yandex.ru.")
    request = Request(url, headers={"User-Agent": "SMART-BUY-AI/1.0", "Accept": "text/html"}, method="GET")
    try:
        opener = build_opener(_MarketRedirectHandler())
        with opener.open(request, timeout=12) as response:
            final_url = response.geturl()
            final = urlparse(final_url)
            if final.scheme != "https" or final.hostname not in {
                "market.yandex.ru", "www.market.yandex.ru"
            }:
                raise HTTPException(status_code=400, detail="Ссылка перенаправляет за пределы Яндекс Маркета.")
            return final_url
    except HTTPException:
        raise
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Не удалось раскрыть короткую ссылку Яндекс Маркета (HTTP {exc.code}).")
    except (URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail="Яндекс Маркет не раскрыл короткую ссылку. Попробуйте позже или отправьте полную ссылку на карточку.")


def _config():
    token = os.getenv("YANDEX_MARKET_AFFILIATE_TOKEN", "").strip()
    place_id = os.getenv("YANDEX_MARKET_PLACE_ID", "").strip()
    enabled = os.getenv("YANDEX_MARKET_API_ENABLED", "false").strip().lower() == "true"
    return token, place_id, enabled


@router.get("/status")
def yandex_affiliate_status():
    token, place_id, enabled = _config()
    ready = bool(token and place_id and enabled)
    if ready:
        status = "ready_for_test"
    elif not token:
        status = "awaiting_api_key"
    elif not place_id:
        status = "awaiting_place_id"
    else:
        status = "disabled"
    return {
        "provider": "yandex_market_affiliate",
        "status": status,
        "configured": ready,
        "api_enabled": enabled,
        "token_configured": bool(token),
        "place_id_configured": bool(place_id),
        "catalog_search_supported": False,
        "supported_operations": [
            "create_referral_link",
            "read_link_product_metadata",
            "order_reporting"
        ],
        "notice": "API реферальной программы не предоставляет общий поиск по каталогу."
    }


@router.post("/link")
def create_yandex_referral_link(
    url: str = Query(..., min_length=16, max_length=2048)
):
    token, place_id, enabled = _config()
    if not enabled:
        raise HTTPException(status_code=409, detail="Интеграция Яндекс Маркета пока выключена.")
    if not token:
        raise HTTPException(status_code=503, detail="Не задан API-ключ Яндекс Маркета в Render.")
    if not place_id:
        raise HTTPException(status_code=503, detail="Не задан YANDEX_MARKET_PLACE_ID в Render.")

    resolved_url = _resolve_market_url(url)

    endpoint = "https://api.content.market.yandex.ru/v3/affiliate/partner/link/create"
    query = urlencode({"url": resolved_url, "place_id": place_id, "format": "json"})
    request = Request(
        endpoint + "?" + query,
        headers={
            "Authorization": "OAuth " + token,
            "Accept": "application/json"
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 401:
            raise HTTPException(status_code=502, detail="Яндекс отклонил API-ключ (401). Проверьте ключ.")
        if exc.code == 403:
            raise HTTPException(status_code=502, detail="Яндекс запретил доступ (403). Проверьте права и площадку.")
        if exc.code == 429:
            raise HTTPException(status_code=503, detail="Достигнут лимит запросов Яндекс Маркета. Повторите позже.")
        raise HTTPException(status_code=502, detail=f"Ошибка API Яндекс Маркета: HTTP {exc.code}.")
    except (URLError, TimeoutError):
        raise HTTPException(status_code=502, detail="Не удалось связаться с API Яндекс Маркета.")
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=502, detail="Яндекс вернул некорректный ответ.")

    if not isinstance(payload, dict) or payload.get("status") != "OK":
        raise HTTPException(status_code=502, detail="Яндекс не смог создать реферальную ссылку.")
    link = payload.get("link")
    if not isinstance(link, dict) or not link.get("url"):
        raise HTTPException(status_code=502, detail="В ответе Яндекса отсутствует реферальная ссылка.")

    return {
        "provider": "yandex_market",
        "status": "ok",
        "title": link.get("title"),
        "image": link.get("productPhoto"),
        "price": payload.get("price"),
        "stock_amount": payload.get("stockAmount"),
        "reward": payload.get("promise"),
        "discount": payload.get("discount"),
        "referral_url": link.get("url"),
        "short_url": link.get("shortUrl"),
        "source_label": "Данные сервиса Яндекс Маркет",
        "source_url": "https://market.yandex.ru/",
        "catalog_search_supported": False,
    }
'''

MODULE_FILE.write_text(module, encoding="utf-8")

source = APP_FILE.read_text(encoding="utf-8")
import_line = "from app.yandex_affiliate import router as yandex_affiliate_router"
include_line = "app.include_router(yandex_affiliate_router)"
if import_line not in source:
    source = import_line + "\n" + source
if include_line not in source:
    source = source.rstrip() + "\n\n" + include_line + "\n"
APP_FILE.write_text(source, encoding="utf-8")
print("SMART BUY AI Yandex Affiliate API adapter installed.")
