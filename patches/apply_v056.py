from pathlib import Path

def replace_once(path, old, new):
    p = Path(path)
    source = p.read_text(encoding="utf-8")
    if old not in source:
        raise SystemExit(f"Patch anchor not found in {path}: {old[:100]!r}")
    p.write_text(source.replace(old, new, 1), encoding="utf-8")

discovery = "backend/app/discovery.py"
replace_once(discovery,
'''def _param(offer: ET.Element, *names: str) -> str | None:
    wanted = {n.casefold() for n in names}
    for node in offer.iter():
        if _local(node.tag) != "param":
            continue
        label = (node.attrib.get("name") or "").strip().casefold()
        if label in wanted and node.text and node.text.strip():
            return node.text.strip()
    return None


def _price(value: str | None) -> float | None:
''',
'''def _param(offer: ET.Element, *names: str) -> str | None:
    wanted = {n.casefold() for n in names}
    for node in offer.iter():
        if _local(node.tag) != "param":
            continue
        label = (node.attrib.get("name") or "").strip().casefold()
        if label in wanted and node.text and node.text.strip():
            return node.text.strip()
    return None


def _shipping(offer: ET.Element) -> float | None:
    """Read a YML delivery option price without treating product price as shipping."""
    for node in offer.iter():
        if _local(node.tag) == "option" and node.attrib.get("cost") is not None:
            value = _price(node.attrib.get("cost"))
            if value is not None:
                return value
    return _price(_param(offer, "shipping", "delivery cost", "стоимость доставки"))


def _positive_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        number = int(value.strip())
        return number if number > 0 else None
    except (TypeError, ValueError):
        return None


def _price(value: str | None) -> float | None:
''')
replace_once(discovery,
'''    # Namespace-independent YML offers.
    currencies: dict[str, str] = {}
    for currency in root.iter():
        if _local(currency.tag) == "currency":
            code = currency.attrib.get("id")
            rate = currency.attrib.get("rate")
            if code:
                currencies[code] = "RUB" if rate in (None, "1") else code
    for offer in (n for n in root.iter() if _local(n.tag) == "offer"):
''',
'''    # Namespace-independent YML offers. Resolve category IDs to readable names.
    categories = {node.attrib.get("id"): (node.text or "").strip()
                  for node in root.iter() if _local(node.tag) == "category"
                  and node.attrib.get("id")}
    for offer in (n for n in root.iter() if _local(n.tag) == "offer"):
''')
replace_once(discovery,
'''        available = offer.attrib.get("available", "true").strip().lower()
        rows.append({
''',
'''        available = offer.attrib.get("available", "true").strip().lower()
        category_id = _text(offer, "categoryId")
        minimum_order = _positive_int(_param(offer, "min_order_quantity", "minimum order quantity", "минимальный заказ", "минимальное количество"))
        rows.append({
''')
replace_once(discovery,
'''            "category": _text(offer, "categoryId", "category"),
''',
'''            "category": categories.get(category_id, category_id) if category_id else _text(offer, "category"),
''')
replace_once(discovery,
'''            "price": price,
            "currency": currency,
            "url": _link(offer),
            "in_stock": available in {"true", "1", "yes"},
            "seller": source,
''',
'''            "price": price,
            "currency": currency,
            "shipping": _shipping(offer),
            "url": _link(offer),
            "in_stock": available in {"true", "1", "yes"},
            "seller": _text(offer, "seller", "sellerName") or source,
            "is_wholesale": minimum_order is not None and minimum_order > 1,
            "min_order_quantity": minimum_order,
''')

tests = Path("backend/tests/test_discovery.py")
t = tests.read_text(encoding="utf-8")
if "test_yml_resolves_category_shipping_and_wholesale_minimum" not in t:
    t += '''

def test_yml_resolves_category_shipping_and_wholesale_minimum():
    xml = \'''<yml_catalog><shop><categories><category id="10">Бытовая техника</category></categories>
      <offers><offer id="sku-2" available="true"><name>Чайник</name><price>2500</price>
        <currencyId>RUB</currencyId><categoryId>10</categoryId><url>https://shop.example/kettle</url>
        <delivery-options><option cost="199" days="2"/></delivery-options>
        <param name="Минимальный заказ">4</param><sellerName>Поставщик</sellerName>
      </offer></offers></shop></yml_catalog>\'''
    row = parse_yml_or_rss(xml, "shop")[0]
    assert row["category"] == "Бытовая техника"
    assert row["shipping"] == 199
    assert row["seller"] == "Поставщик"
    assert row["is_wholesale"] is True
    assert row["min_order_quantity"] == 4


def test_yml_free_delivery_is_zero_not_unknown():
    xml = \'''<yml_catalog><shop><offers><offer id="sku-3"><name>Книга</name><price>500</price>
      <delivery-options><option cost="0"/></delivery-options></offer></offers></shop></yml_catalog>\'''
    row = parse_yml_or_rss(xml, "shop")[0]
    assert row["shipping"] == 0
'''
    tests.write_text(t, encoding="utf-8")

gradle = Path("app/build.gradle")
g = gradle.read_text(encoding="utf-8")
g2 = g.replace("versionCode 15", "versionCode 16", 1).replace("versionName '0.5.5'", "versionName '0.5.6'", 1)
if g2 == g:
    raise SystemExit("Expected v0.5.5 Android version markers were not found")
gradle.write_text(g2, encoding="utf-8")

readme = Path("backend/README.md")
r = readme.read_text(encoding="utf-8")
if "### YML import details (v0.5.6)" not in r:
    r += '''

### YML import details (v0.5.6)
- Category IDs are resolved to category names when the feed includes a category tree.
- YML delivery-options/option@cost is imported as delivery cost and included in total-price comparison; zero means free delivery.
- Seller name is kept separate from feed source when supplied by the feed.
- A declared minimum-order quantity greater than one is marked as wholesale and stays separate from retail rankings.
- A store is not marked live merely because it exists in the app directory. Only explicitly configured, successfully fetched feeds supply live prices.
'''
    readme.write_text(r, encoding="utf-8")
