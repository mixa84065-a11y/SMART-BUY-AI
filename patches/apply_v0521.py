from pathlib import Path

root = Path("backend/app")
module = r'''"""Read-only public Plati.Market catalogue integration through official MCP."""
import asyncio
import json
import os
import re
import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/v1/integrations/plati", tags=["integrations"])
MCP_URL = "https://mcp.plati.market/mcp"
_SEARCH_CACHE = {}
_SEARCH_CACHE_TTL = 90
ALLOWED_HOSTS = {"plati.market", "www.plati.market"}


def _partner_id():
    value = os.getenv("PLATI_PARTNER_ID", "").strip()
    return value if re.fullmatch(r"[A-Za-z0-9_-]{1,40}", value) else ""


def _safe_product_url(value):
    if not value:
        return None
    parsed = urlparse(str(value).strip())
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ALLOWED_HOSTS:
        return None
    return urlunparse(parsed._replace(scheme="https", fragment=""))


def _affiliate_url(value):
    safe = _safe_product_url(value)
    partner_id = _partner_id()
    if not safe or not partner_id:
        return safe
    parsed = urlparse(safe)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["ai"] = partner_id
    return urlunparse(parsed._replace(query=urlencode(query)))


def _mcp_result(payload):
    if not isinstance(payload, dict):
        raise ValueError("Некорректный ответ MCP")
    if payload.get("error"):
        err = payload["error"]
        raise ValueError(str(err.get("message") or "Ошибка MCP"))
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("MCP не вернул result")
    if result.get("isError"):
        content = result.get("content") or []
        message = content[0].get("text") if content and isinstance(content[0], dict) else None
        raise ValueError(message or "Ошибка инструмента Plati.Market")
    structured = result.get("structuredContent")
    if isinstance(structured, dict):
        return structured
    content = result.get("content") or []
    for item in content:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            try:
                parsed = json.loads(item["text"])
                if isinstance(parsed, dict):
                    return parsed
            except ValueError:
                continue
    raise ValueError("MCP вернул пустой или неизвестный формат результата")


async def _call_tool(client, name, arguments):
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    response = await client.post(
        MCP_URL,
        json=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError:
        # Streamable HTTP may return an SSE envelope: data: {JSON}
        payload = None
        for line in response.text.splitlines():
            if line.startswith("data:"):
                try:
                    payload = json.loads(line[5:].strip())
                    break
                except ValueError:
                    pass
        if payload is None:
            raise ValueError("Не удалось разобрать ответ MCP")
    return _mcp_result(payload)


def _price_rub(price):
    if isinstance(price, dict):
        value = price.get("rur")
    else:
        value = None
    try:
        number = float(value)
        return number if number > 0 else None
    except (TypeError, ValueError):
        return None


async def _detail(client, product_id, semaphore):
    async with semaphore:
        try:
            return await _call_tool(client, "get_product_from_plati_market", {
                "product_id": str(product_id),
                "lang": "ru-RU",
                "currency": "RUR",
            })
        except (httpx.HTTPError, ValueError):
            return {}


@router.get("/status")
async def plati_status():
    return {
        "provider": "plati_market_mcp",
        "status": "public_catalog",
        "partner_id_configured": bool(_partner_id()),
        "catalog_search_supported": True,
        "affiliate_links_enabled": bool(_partner_id()),
        "authentication_required": False,
        "read_only": True,
        "supported_operations": ["search_products", "read_product_metadata"],
        "scope": "Публичный каталог цифровых товаров Plati.Market",
        "notice": "Поиск открыт без API-ключа. Партнёрский параметр ai добавляется только при настройке PLATI_PARTNER_ID.",
    }


@router.get("/search")
async def plati_search(
    q: str = Query(..., min_length=3, max_length=120),
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(10, ge=1, le=50),
):
    cache_key = (q.strip().casefold(), page, page_size)
    cached = _SEARCH_CACHE.get(cache_key)
    now = time.monotonic()
    if cached and now - cached[0] < _SEARCH_CACHE_TTL:
        return cached[1]
    timeout = httpx.Timeout(25.0, connect=8.0)
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": "SMART-BUY-AI/1.0"},
        ) as client:
            data = await _call_tool(client, "get_products_from_plati_market", {
                "query": q,
                "pagesize": page_size,
                "pagenum": page,
                "lang": "ru-RU",
            })
            rows = data.get("products", []) if isinstance(data, dict) else []
            if not isinstance(rows, list):
                rows = []
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Plati.Market вернул HTTP {exc.response.status_code}.")
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Не удалось получить каталог Plati.Market: {str(exc)[:180]}")

    products = []
    for row in rows:
        if not isinstance(row, dict) or row.get("id") is None:
            continue
        raw_url = _safe_product_url(row.get("url")) or f"https://plati.market/itm/{row['id']}"
        url = _affiliate_url(raw_url)
        price = row.get("price") if isinstance(row.get("price"), dict) else {}
        title = row.get("name") or "Товар Plati.Market"
        description = row.get("description") or ""
        seller = row.get("seller") if isinstance(row.get("seller"), dict) else {}
        products.append({
            "id": str(row.get("id")),
            "title": str(title)[:300],
            "description": str(description)[:1200],
            "price": _price_rub(price),
            "currency": "RUB",
            "image": f"https://graph.digiseller.ru/img.ashx?id_d={row['id']}&maxlength=400",
            "url": url,
            "affiliate_link": url if _partner_id() else None,
            "seller": {"id": seller.get("id"), "name": seller.get("name")},
            "sold": row.get("sold"),
            "rating": None,
            "source": "Plati.Market",
            "live_data": True,
        })
    result = {
        "provider": "plati_market",
        "query": q,
        "page": page,
        "page_size": page_size,
        "total_pages": data.get("totalPages") if isinstance(data, dict) else None,
        "count": len(products),
        "affiliate_links_enabled": bool(_partner_id()),
        "products": products,
        "notice": "Актуальные данные публичного каталога Plati.Market. Цена и наличие могут измениться на странице продавца.",
    }
    if len(_SEARCH_CACHE) > 200:
        _SEARCH_CACHE.clear()
    _SEARCH_CACHE[cache_key] = (time.monotonic(), result)
    return result
'''
(root / "plati_affiliate.py").write_text(module, encoding="utf-8")
print("Installed public Plati.Market MCP catalogue adapter.")
