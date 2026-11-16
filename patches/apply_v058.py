from pathlib import Path

p = Path("backend/app/discovery.py")
s = p.read_text(encoding="utf-8")
s = s.replace("import ipaddress\nimport math\nimport socket\n", "import csv\nimport ipaddress\nimport io\nimport math\nimport re\nimport socket\n", 1)
s = s.replace('result = float(value.replace("\\u00a0", "").replace(" ", "").replace(",", "."))', 'cleaned = value.replace("\\u00a0", " ").strip()\n        cleaned = re.sub(r"\\s*(RUB|USD|EUR|₽|руб\\.?|рублей)\\s*$", "", cleaned, flags=re.IGNORECASE)\n        result = float(cleaned.replace(" ", "").replace(",", "."))', 1)
anchor = "\nasync def fetch_feed(source: str, url: str) -> list[dict]:"
csv_parser = r"""

def _csv_key(value: str) -> str:
    return "".join(ch for ch in (value or "").casefold() if ch.isalnum())


def parse_csv_feed(text: str, source: str) -> list[dict]:
    """Parse common Google Merchant and Yandex universal CSV product feeds."""
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return []
    aliases = {
        "id": ("id", "offerid", "sku", "артикул", "идентификатор"),
        "title": ("title", "name", "productname", "название", "наименование"),
        "price": ("price", "цена", "cost"),
        "link": ("link", "url", "producturl", "ссылка", "ссылка на товар"),
        "brand": ("brand", "vendor", "бренд", "производитель"),
        "gtin": ("gtin", "barcode", "ean", "штрихкод"),
        "category": ("producttype", "category", "type", "категория", "типтовара"),
        "availability": ("availability", "stock", "наличие", "доступность"),
        "shipping": ("shipping", "deliverycost", "стоимостьдоставки"),
        "seller": ("seller", "merchant", "продавец", "магазин"),
        "currency": ("currency", "currencyid", "валюта"),
        "image": ("imagelink", "image", "picture", "изображение", "картинка"),
    }
    fields = {_csv_key(k): k for k in reader.fieldnames if k}
    columns = {name: next((fields[_csv_key(a)] for a in options if _csv_key(a) in fields), None)
               for name, options in aliases.items()}
    if not columns["title"] or not columns["price"]:
        raise ValueError("CSV feed must contain title/name and price columns")
    rows = []
    for index, raw in enumerate(reader):
        def val(key):
            column = columns.get(key)
            value = raw.get(column) if column else None
            return value.strip() if isinstance(value, str) and value.strip() else None
        title, price = val("title"), _price(val("price"))
        if not title or price is None:
            continue
        availability = (val("availability") or "").casefold()
        in_stock = None if not availability else availability in {
            "in stock", "instock", "available", "true", "1", "есть", "в наличии", "да"
        }
        rows.append({
            "external_id": (val("id") or val("link") or f"{source}-{index}")[:180],
            "title": title, "brand": val("brand"), "gtin": val("gtin"),
            "category": val("category"), "price": price,
            "currency": (val("currency") or "RUB").upper(),
            "shipping": _price(val("shipping")), "url": val("link"),
            "seller": val("seller") or source, "in_stock": in_stock,
            "image_url": val("image"), "is_wholesale": False, "min_order_quantity": None,
        })
    return rows
"""
if "def parse_csv_feed(" not in s:
    if anchor not in s: raise SystemExit("CSV insertion anchor not found")
    s = s.replace(anchor, csv_parser + anchor, 1)
old = '    return parse_yml_or_rss(b"".join(chunks).decode("utf-8-sig", errors="replace"), source)\n'
new = '''    body = b"".join(chunks).decode("utf-8-sig", errors="replace")
    if "csv" in content_type or urlparse(url).path.lower().endswith(".csv"):
        return parse_csv_feed(body, source)
    if body.lstrip().startswith(("{", "[")):
        raise ValueError("JSON feeds are not supported yet; use YML/XML/RSS/Atom/CSV")
    return parse_yml_or_rss(body, source)
'''
if old not in s: raise SystemExit("fetch return anchor not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

tests = Path("backend/tests/test_discovery.py")
t = tests.read_text(encoding="utf-8")
if "test_google_merchant_csv_feed_imports_prices_and_links" not in t:
    t += '''

def test_google_merchant_csv_feed_imports_prices_and_links():
    from app.discovery import parse_csv_feed
    csv_text = "id,title,description,link,image_link,price,availability,brand,gtin\\nSKU-1,Кофемашина,Описание,https://shop.example/p/1,https://shop.example/i.jpg,12990.00 RUB,in stock,Acme,4601234567890\\n"
    rows = parse_csv_feed(csv_text, "shop")
    assert len(rows) == 1
    assert rows[0]["external_id"] == "SKU-1"
    assert rows[0]["price"] == 12990
    assert rows[0]["currency"] == "RUB"
    assert rows[0]["in_stock"] is True
    assert rows[0]["gtin"] == "4601234567890"
    assert rows[0]["url"] == "https://shop.example/p/1"


def test_yandex_semicolon_csv_feed_and_out_of_stock():
    from app.discovery import parse_csv_feed
    csv_text = "Артикул;Название;Цена;Ссылка;Категория;Наличие\\nA-2;Книга;450;https://book.example/2;Книги;Нет\\n"
    rows = parse_csv_feed(csv_text, "books")
    assert rows[0]["external_id"] == "A-2"
    assert rows[0]["category"] == "Книги"
    assert rows[0]["in_stock"] is False


def test_csv_feed_requires_title_and_price_columns():
    from app.discovery import parse_csv_feed
    try:
        parse_csv_feed("id,description\\n1,test\\n", "shop")
        assert False, "CSV without title and price must be rejected"
    except ValueError as exc:
        assert "title/name and price" in str(exc)
'''
    tests.write_text(t, encoding="utf-8")

gradle = Path("app/build.gradle")
g = gradle.read_text(encoding="utf-8")
g2 = g.replace("versionCode 17", "versionCode 18", 1).replace("versionName '0.5.7'", "versionName '0.5.8'", 1)
if g2 == g: raise SystemExit("Expected v0.5.7 version markers were not found")
gradle.write_text(g2, encoding="utf-8")

readme = Path("backend/README.md")
r = readme.read_text(encoding="utf-8")
if "### CSV feed support (v0.5.8)" not in r:
    r += '''

### CSV feed support (v0.5.8)
- Supports common Google Merchant and Yandex-style CSV product feeds with comma, semicolon, or tab separators.
- Maps product ID, title, price, currency, URL, brand, GTIN, category, stock, seller, shipping, and image fields when present.
- Parses prices with currency suffixes such as 12990 RUB.
- CSV import still requires an explicitly configured, permitted HTTPS feed; no store is considered connected merely because it appears in the catalog.
'''
    readme.write_text(r, encoding="utf-8")
