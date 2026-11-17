from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_FILE = ROOT / "backend" / "app" / "main.py"
MODULE_FILE = ROOT / "backend" / "app" / "plati_affiliate.py"
if not APP_FILE.is_file():
    raise SystemExit(f"FastAPI entrypoint not found: {APP_FILE}")

module = r'''"""Read-only Plati/Digiseller affiliate search adapter.

Search protocol and product details follow the official Digiseller API.
Affiliate links are only emitted when PLATI_PARTNER_ID is configured.
"""
import asyncio
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/v1/integrations/plati", tags=["integrations"])
SEARCH_URL = "https://shop.digiseller.ru/xml/shop_search.asp"
DETAIL_URL = "https://api.digiseller.com/api/products/{product_id}/data"
ALLOWED_PRODUCT_HOSTS = {"plati.market", "www.plati.market", "plati.digital", "www.plati.digital", "plati.ru", "www.plati.ru"}


def _partner_id():
    value = os.getenv("PLATI_PARTNER_ID", "").strip()
    return value if re.fullmatch(r"[A-Za-z0-9_-]{1,40}", value) else ""


def _safe_url(raw_url):
    if not raw_url:
        return None
    parsed = urlparse(str(raw_url).strip())
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ALLOWED_PRODUCT_HOSTS:
        return None
    return urlunparse(parsed._replace(scheme="https", fragment=""))


def _affiliate_url(raw_url, partner_id):
    safe = _safe_url(raw_url)
    if not safe or not partner_id:
        return None
    parsed = urlparse(safe)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["ai"] = partner_id
    return urlunparse(parsed._replace(query=urlencode(query)))


def _xml_text(node, *names):
    if node is None:
        return None
    wanted = {name.lower() for name in names}
    for child in list(node):
        if child.tag.split("}")[-1].lower() in wanted:
            value = (child.text or "").strip()
            if value:
                return value
    return None


def _search_xml(query, page, page_size):
    root = ET.Element("digiseller.request")
    seller = ET.SubElement(root, "seller")
    ET.SubElement(seller, "id").text = ""
    products = ET.SubElement(root, "products")
    ET.SubElement(products, "search").text = query
    ET.SubElement(products, "currency").text = "RUB"
    pages = ET.SubElement(root, "pages")
    ET.SubElement(pages, "num").text = str(page)
    ET.SubElement(pages, "rows").text = str(page_size)
    ET.SubElement(root, "lang").text = "ru-RU"
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _parse_search_response(raw):
    root = ET.fromstring(raw)
    retval = _xml_text(root, "retval")
    if retval not in (None, "0"):
        message = _xml_text(root, "retdesc") or "Digiseller отклонил запрос поиска."
        raise ValueError(message)
    products_node = next((n for n in root.iter() if n.tag.split("}")[-1].lower() == "products"), None)
    rows = []
    if products_node is not None:
        for node in list(products_node):
            if node.tag.split("}")[-1].lower() != "product":
                continue
            rows.append({
                "id": _xml_text(node, "id"),
                "title": _xml_text(node, "name"),
                "price": _xml_text(node, "price"),
                "agency_fee": _xml_text(node, "agency_fee"),
            })
    pages_node = next((n for n in root.iter() if n.tag.split("}")[-1].lower() == "pages"), None)
    return rows, {
        "total_pages": pages_node.attrib.get("cnt") if pages_node is not None else None,
        "page": _xml_text(pages_node, "num") if pages_node is not None else None,
        "page_size": _xml_text(pages_node, "rows") if pages_node is not None else None,
    }


def _detail_payload(response):
    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type or response.text.lstrip().startswith("{"):
        payload = response.json()
        return payload.get("product", payload) if isinstance(payload, dict) else {}
    root = ET.fromstring(response.content)
    product = next((n for n in root.iter() if n.tag.split("}")[-1].lower() == "product"), None)
    if product is None:
        return {}
    data = {}
    for child in list(product):
        key = child.tag.split("}")[-1].lower()
        if key == "preview_imgs":
            imgs = []
            for img in list(child):
                for sub in list(img):
                    value = (sub.text or "").strip()
                    if value and sub.tag.split("}")[-1].lower() in {"img_real", "img_small"}:
                        imgs.append(value)
            data["preview_imgs"] = imgs
        else:
            data[key] = (child.text or "").strip()
    return data


async def _get_detail(client, product_id, semaphore):
    if not product_id or not str(product_id).isdigit():
        return {}
    async with semaphore:
        try:
            response = await client.get(
                DETAIL_URL.format(product_id=int(product_id)),
                params={"currency": "RUB", "lang": "ru-RU"},
            )
            response.raise_for_status()
            return _detail_payload(response)
        except (httpx.HTTPError, ValueError, ET.ParseError):
            return {}


@router.get("/status")
def plati_status():
    partner_id = _partner_id()
    return {
        "provider": "plati_digiseller_affiliate",
        "status": "ready_for_test" if partner_id else "awaiting_partner_id",
        "partner_id_configured": bool(partner_id),
        "catalog_search_supported": True,
        "affiliate_links_enabled": bool(partner_id),
        "supported_operations": ["search_products", "read_product_metadata"],
        "scope": "Цифровые товары Plati/Digiseller; не весь ассортимент SMART BUY AI",
        "notice": "Поиск каталога доступен через официальный API; персональные партнёрские ссылки требуют PLATI_PARTNER_ID."
    }


@router.get("/search")
async def plati_search(
    q: str = Query(..., min_length=3, max_length=120),
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(10, ge=1, le=20),
):
    partner_id = _partner_id()
    timeout = httpx.Timeout(18.0, connect=6.0)
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": "SMART-BUY-AI/1.0", "Accept": "application/xml, application/json"}
        ) as client:
            response = await client.post(
                SEARCH_URL,
                content=_search_xml(q, page, page_size),
                headers={"Content-Type": "application/xml; charset=utf-8"},
            )
            response.raise_for_status()
            rows, paging = _parse_search_response(response.content)
            semaphore = asyncio.Semaphore(4)
            details = await asyncio.gather(*[
                _get_detail(client, row.get("id"), semaphore) for row in rows
            ])
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Digiseller API вернул HTTP {exc.response.status_code}.")
    except (httpx.HTTPError, ValueError, ET.ParseError):
        raise HTTPException(status_code=502, detail="Не удалось получить или разобрать ответ официального API Digiseller.")

    result = []
    for row, detail in zip(rows, details):
        product_id = str(row.get("id") or "").strip()
        title = row.get("title")
        if not product_id.isdigit() or not title:
            continue
        raw_url = detail.get("url") or detail.get("product_url")
        product_url = _safe_url(raw_url)
        image = None
        preview = detail.get("preview_imgs")
        if isinstance(preview, list) and preview:
            image = preview[0]
        if not image:
            image = f"https://graph.digiseller.ru/img.ashx?id_d={product_id}&maxlength=400"
        affiliate = _affiliate_url(product_url, partner_id)
        result.append({
            "id": product_id,
            "title": title,
            "description": detail.get("info") or detail.get("add_info"),
            "price": detail.get("price_rub") or detail.get("price") or row.get("price"),
            "currency": "RUB",
            "image": image,
            "url": affiliate or product_url,
            "affiliate_link": affiliate,
            "partner_commission_percent": row.get("agency_fee") or detail.get("agency_fee"),
            "available": detail.get("is_available"),
            "seller": detail.get("seller"),
            "source": "Plati / Digiseller",
            "live_data": True,
        })
    return {
        "provider": "plati_digiseller",
        "query": q,
        "page": page,
        "count": len(result),
        "paging": paging,
        "affiliate_links_enabled": bool(partner_id),
        "products": result,
        "notice": "Показаны данные официального каталога Digiseller. Партнёрская ссылка добавляется только при наличии PLATI_PARTNER_ID."
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
print("Installed the official Digiseller XML search and product-details adapter.")
