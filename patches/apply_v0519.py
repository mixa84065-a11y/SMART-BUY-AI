from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_FILE = ROOT / "backend" / "app" / "main.py"
MODULE_FILE = ROOT / "backend" / "app" / "plati_affiliate.py"
if not APP_FILE.is_file():
    raise SystemExit(f"FastAPI entrypoint not found: {APP_FILE}")

module = r'''"""Plati/Digiseller affiliate catalog search adapter.

Uses the documented affiliate search endpoint. It is deliberately read-only:
no checkout, payment, seller account, or product mutation operations.
"""
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/v1/integrations/plati", tags=["integrations"])
API_URL = "https://plati.digital/api/search.ashx"


def _partner_id():
    value = os.getenv("PLATI_PARTNER_ID", "").strip()
    return value if re.fullmatch(r"[A-Za-z0-9_-]{1,40}", value) else ""


def _affiliate_url(raw_url: str, partner_id: str) -> str | None:
    parsed = urlparse(raw_url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in {
        "plati.digital", "www.plati.digital", "plati.ru", "www.plati.ru"
    }:
        return None
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["ai"] = partner_id
    return urlunparse(parsed._replace(scheme="https", query=urlencode(query)))


def _text(item, *keys):
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _xml_items(raw: bytes):
    root = ET.fromstring(raw)
    rows = []
    for node in root.iter():
        if node.tag.lower().split("}")[-1] in {"item", "offer", "product"}:
            row = {}
            for child in list(node):
                row[child.tag.lower().split("}")[-1]] = child.text or ""
            if row:
                rows.append(row)
    if rows:
        return rows
    # Some XML responses wrap records in a result node; accept direct record-like children.
    for node in list(root):
        row = {child.tag.lower().split("}")[-1]: child.text or "" for child in list(node)}
        if row:
            rows.append(row)
    return rows


def _json_items(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "products", "goods", "result", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = _json_items(value)
                if nested:
                    return nested
    return []


@router.get("/status")
def plati_status():
    partner_id = _partner_id()
    return {
        "provider": "plati_digiseller_affiliate",
        "status": "ready_for_test" if partner_id else "awaiting_partner_id",
        "partner_id_configured": bool(partner_id),
        "catalog_search_supported": True,
        "supported_operations": ["search_products"],
        "scope": "Цифровые товары Plati; не весь ассортимент SMART BUY AI",
        "notice": "Для партнёрской атрибуции нужна регистрация и PLATI_PARTNER_ID."
    }


@router.get("/search")
async def plati_search(
    q: str = Query(..., min_length=3, max_length=120),
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(20, ge=1, le=50),
):
    partner_id = _partner_id()
    if not partner_id:
        raise HTTPException(status_code=503, detail="Интеграция Plati ожидает PLATI_PARTNER_ID в настройках сервера.")
    params = {"query": q, "pagesize": page_size, "pagenum": page, "response": "json"}
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=6.0),
            follow_redirects=False,
            headers={"User-Agent": "SMART-BUY-AI/1.0", "Accept": "application/json, application/xml"}
        ) as client:
            response = await client.get(API_URL, params=params)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "json" in content_type or response.text.lstrip().startswith(("{", "[")):
                payload = response.json()
                rows = _json_items(payload)
            else:
                rows = _xml_items(response.content)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Plati API вернул HTTP {exc.response.status_code}.")
    except (httpx.HTTPError, ValueError, ET.ParseError):
        raise HTTPException(status_code=502, detail="Не удалось получить или разобрать каталог Plati.")

    products = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized = {str(k).lower(): v for k, v in row.items()}
        raw_url = _text(normalized, "url", "item_url", "link")
        affiliate_url = _affiliate_url(raw_url, partner_id) if raw_url else None
        title = _text(normalized, "name", "title", "product_name")
        if not title or not affiliate_url:
            continue
        image = _text(normalized, "image", "picture", "img")
        price = _text(normalized, "price_rub", "price_rub", "price", "price_rur")
        products.append({
            "id": _text(normalized, "id", "product_id", "item_id"),
            "title": title,
            "description": _text(normalized, "description", "desc"),
            "price": price,
            "currency": "RUB" if price else None,
            "image": image,
            "url": affiliate_url,
            "seller_id": _text(normalized, "seller_id", "seller"),
            "sold": _text(normalized, "numsold", "sold"),
            "source": "Plati",
            "source_url": "https://plati.digital/",
            "live_data": True,
        })
    return {
        "provider": "plati",
        "query": q,
        "page": page,
        "page_size": page_size,
        "count": len(products),
        "products": products,
        "notice": "Цены и наличие относятся к данным Plati; проверяйте карточку продавца перед покупкой."
    }
'''

MODULE_FILE.write_text(module, encoding="utf-8")
source = APP_FILE.read_text(encoding="utf-8")
import_line = "from app.plati_affiliate import router as plati_affiliate_router"
include_line = "app.include_router(plati_affiliate_router)"
if import_line not in source:
    source = import_line + "\n" + source
if include_line not in source:
    source = source.rstrip() + "\n\n" + include_line + "\n"
APP_FILE.write_text(source, encoding="utf-8")
print("SMART BUY AI Plati affiliate search adapter installed.")
