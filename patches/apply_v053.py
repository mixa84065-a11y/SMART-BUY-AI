from pathlib import Path

def replace_once(path, old, new):
    p = Path(path)
    source = p.read_text(encoding="utf-8")
    if old not in source:
        raise SystemExit(f"Patch anchor not found in {path}: {old[:80]!r}")
    p.write_text(source.replace(old, new, 1), encoding="utf-8")

java = "app/src/main/java/com/smartbuy/ai/MainActivity.java"
replace_once(java,
'final String[] categories={"Все","Электроника","Телефоны","Компьютеры","Дом","Мебель","Интерьер","Сад и ремонт","Одежда","Женская одежда","Мужская одежда","Обувь","Аксессуары","Детская одежда","Красота","Спорт","Детям","Авто","Продукты","Зоотовары","Книги"};',
'final String[] categories={"Все","Электроника","Телефоны","Компьютеры","Бытовая техника","Дом","Мебель","Интерьер","Сад и ремонт","Одежда","Женская одежда","Мужская одежда","Обувь","Аксессуары","Детская одежда","Красота","Спорт","Детям","Игрушки","Авто","Продукты","Зоотовары","Книги","Канцтовары","Аптека"};')
replace_once(java,
'        products.add(new Product("Детская толстовка","Детская одежда","🧒",1990,1790,2190,"Магазин A","Магазин B","Магазин C"));\n',
'''        products.add(new Product("Детская толстовка","Детская одежда","🧒",1990,1790,2190,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Телевизор Xiaomi TV A Pro 55","Электроника","📺",38990,36990,40990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Планшет Samsung Galaxy Tab","Электроника","📲",24990,23990,26990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Монитор 27 дюймов IPS","Компьютеры","🖥️",14990,13990,15990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Стиральная машина узкая","Бытовая техника","🧺",27990,25990,29990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Холодильник двухкамерный","Бытовая техника","🧊",42990,40990,45990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Диван прямой раскладной","Мебель","🛋️",32990,30990,35990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Матрас ортопедический 160×200","Мебель","🛏️",18990,17990,20990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Дрель-шуруповёрт аккумуляторная","Сад и ремонт","🛠️",6990,6490,7490,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Джинсы прямого кроя","Одежда","👖",2990,2790,3290,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Кроссовки для бега","Спорт","👟",5990,5490,6490,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Крем для лица увлажняющий","Красота","🧴",890,790,990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Книга — современная проза","Книги","📚",690,590,750,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Корм для кошек 1,5 кг","Зоотовары","🐾",1190,1090,1290,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Автомобильная шина 205/55 R16","Авто","🚙",6490,6190,6990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Кофе в зернах 1 кг","Продукты","☕",1890,1790,1990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Набор кухонной посуды","Дом","🍳",3490,3290,3790,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Набор школьных принадлежностей","Канцтовары","✏️",1290,1190,1390,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Детская настольная игра","Игрушки","🎲",1490,1390,1690,"Магазин A","Магазин B","Магазин C"));
''')
replace_once(java,
'        TextView best=txt("от "+money(p.min()),17,GREEN,true);prices.addView(best,new LinearLayout.LayoutParams(0,-2,1));\n        TextView compare=txt("Сравнить  →",10,0xFFBDB2FF,true);prices.addView(compare);card.addView(prices);\n        TextView info=txt("3 предложения • "+p.category,10,MUTED,false);card.addView(info);\n',
'        TextView best=txt("Демо-цена: "+money(p.min()),15,GREEN,true);prices.addView(best,new LinearLayout.LayoutParams(0,-2,1));\n        TextView compare=txt("Подробнее  →",10,0xFFBDB2FF,true);prices.addView(compare);card.addView(prices);\n        TextView info=txt("Пример карточки • "+p.category,10,MUTED,false);card.addView(info);\n')
replace_once(java,
'        content.addView(txt(p.name,20,TEXT,true));content.addView(txt("Предложения магазинов",13,MUTED,false));\n        offer(p.shop1,p.p1);offer(p.shop2,p.p2);offer(p.shop3,p.p3);\n',
'        content.addView(txt(p.name,20,TEXT,true));\n        content.addView(note("Демонстрационная карточка", "Цена на экране — условный пример интерфейса. Это не актуальное предложение магазина и не результат проверки наличия."));\n        content.addView(note("Где искать этот товар", "Открой поиск по магазинам, чтобы посмотреть публичные страницы продавцов. Фактическую цену, доставку, размер и наличие нужно проверить на сайте магазина."));\n')
replace_once(java,
'            {"Petshop","petshop.ru","Зоотовары"},{"Четыре Лапы","4lapy.ru","Зоотовары"},\n            {"AliExpress","aliexpress.ru","Международные площадки"},{"Alibaba","alibaba.com","Международные площадки"}\n',
'''            {"Petshop","petshop.ru","Зоотовары"},{"Четыре Лапы","4lapy.ru","Зоотовары"},
            {"Детский мир","detmir.ru","Детям и игрушки"},{"Кораблик","korablik.ru","Детям и игрушки"},
            {"Перекрёсток","perekrestok.ru","Продукты и супермаркеты"},{"Пятёрочка","5ka.ru","Продукты и супермаркеты"},{"Магнит","magnit.ru","Продукты и супермаркеты"},{"Лента","lenta.com","Продукты и супермаркеты"},{"Ашан","auchan.ru","Продукты и супермаркеты"},{"METRO","online.metro-cc.ru","Продукты и супермаркеты"},{"ВкусВилл","vkusvill.ru","Продукты и супермаркеты"},
            {"Аптека.ру","apteka.ru","Аптеки и здоровье"},{"ЕАПТЕКА","eapteka.ru","Аптеки и здоровье"},{"Здравсити","zdravcity.ru","Аптеки и здоровье"},
            {"Zolla","zolla.com","Одежда и обувь"},{"SELA","sela.ru","Одежда и обувь"},{"Finn Flare","finn-flare.ru","Одежда и обувь"},{"BAON","baon.ru","Одежда и обувь"},
            {"AliExpress","aliexpress.ru","Международные площадки"},{"Alibaba","alibaba.com","Международные площадки"}
''')
replace_once(java,
'        content.addView(note("Книги, авто и зоотовары","Читай-город • Book24 • Exist • Автодок • Petshop • Четыре Лапы"));\n',
'''        content.addView(note("Книги, авто и зоотовары","Читай-город • Book24 • Exist • Автодок • Petshop • Четыре Лапы"));
        content.addView(note("Продукты и супермаркеты","Перекрёсток • Пятёрочка • Магнит • Лента • Ашан • METRO • ВкусВилл"));
        content.addView(note("Аптеки и здоровье","Аптека.ру • ЕАПТЕКА • Здравсити. Для лекарств требуется особая проверка ассортимента и доступности; цены пока не импортируются."));
        content.addView(note("Детские магазины","Детский мир • Кораблик"));
        content.addView(note("Дополнительные бренды одежды","Zolla • SELA • Finn Flare • BAON"));
''')

gradle = Path("app/build.gradle")
g = gradle.read_text(encoding="utf-8").replace("versionCode 12", "versionCode 13").replace("versionName '0.5.2'", "versionName '0.5.3'")
gradle.write_text(g, encoding="utf-8")

registry = Path("backend/app/adapters/registry.py")
r = registry.read_text(encoding="utf-8")
anchor = '    "petshop": "Зоотовары: нужен разрешённый товарный фид или партнёрский доступ.",\n'
addition = '''    "onlinetrade": "Электроника и товары для дома: нужен разрешённый товарный фид или партнёрский доступ.",
    "holodilnik": "Бытовая техника: нужен разрешённый товарный фид или партнёрский доступ.",
    "avito": "Объявления и товары: требуется разрешённый источник; состояние товара и продавца нужно показывать отдельно.",
    "detskiy_mir": "Детские товары и игрушки: нужен разрешённый товарный фид или партнёрский доступ.",
    "korablik": "Детские товары: нужен разрешённый товарный фид или партнёрский доступ.",
    "letu": "Красота и уход: нужен разрешённый товарный фид или партнёрский доступ.",
    "rivegauche": "Красота и уход: нужен разрешённый товарный фид или партнёрский доступ.",
    "book24": "Книги и канцелярия: нужен разрешённый товарный фид или партнёрский доступ.",
    "autodoc": "Автотовары: нужен разрешённый товарный фид или партнёрский доступ.",
    "four_lapy": "Зоотовары: нужен разрешённый товарный фид или партнёрский доступ.",
    "mnogomebeli": "Мебель: нужен разрешённый товарный фид или партнёрский доступ.",
    "vseinstrumenti": "Инструменты и ремонт: нужен разрешённый товарный фид или партнёрский доступ.",
    "zolla": "Одежда и обувь: нужен разрешённый товарный фид или партнёрский доступ.",
    "sela": "Одежда для всей семьи: нужен разрешённый товарный фид или партнёрский доступ.",
    "finn_flare": "Одежда: нужен разрешённый товарный фид или партнёрский доступ.",
    "baon": "Одежда и верхняя одежда: нужен разрешённый товарный фид или партнёрский доступ.",
    "perekrestok": "Продукты и супермаркет: нужен разрешённый товарный фид или партнёрский доступ.",
    "pyaterochka": "Продукты и супермаркет: нужен разрешённый товарный фид или партнёрский доступ.",
    "magnit": "Продукты и супермаркет: нужен разрешённый товарный фид или партнёрский доступ.",
    "lenta": "Продукты и супермаркет: нужен разрешённый товарный фид или партнёрский доступ.",
    "auchan": "Продукты и супермаркет: нужен разрешённый товарный фид или партнёрский доступ.",
    "metro": "Продукты и товары для бизнеса: нужен разрешённый товарный фид или партнёрский доступ.",
    "vkusvill": "Продукты и готовая еда: нужен разрешённый товарный фид или партнёрский доступ.",
    "apteka_ru": "Аптечный ассортимент: требуется разрешённый источник и отдельная проверка правил отображения лекарств.",
    "eapteka": "Аптечный ассортимент: требуется разрешённый источник и отдельная проверка правил отображения лекарств.",
    "zdravcity": "Аптечный ассортимент: требуется разрешённый источник и отдельная проверка правил отображения лекарств.",
'''
if anchor not in r: raise SystemExit("Registry patch anchor missing")
registry.write_text(r.replace(anchor, anchor+addition, 1), encoding="utf-8")

discovery = Path("backend/app/discovery.py")
d = discovery.read_text(encoding="utf-8")
if "import math\n" not in d: d=d.replace("import ipaddress\n", "import ipaddress\nimport math\n", 1)
old = '        return result if result >= 0 else None\n'
if old not in d: raise SystemExit("Price parser patch anchor missing")
discovery.write_text(d.replace(old, '        return result if math.isfinite(result) and result >= 0 else None\n', 1), encoding="utf-8")

tests = Path("backend/tests/test_discovery.py")
t = tests.read_text(encoding="utf-8")
if "test_price_parser_rejects_non_finite_values" not in t:
    t += '''

def test_price_parser_rejects_non_finite_values():
    from app.discovery import _price
    assert _price("NaN") is None
    assert _price("Infinity") is None
    assert _price("-Infinity") is None
    assert _price("1 299,50") == 1299.5


def test_registry_covers_new_store_categories():
    from app.adapters.registry import ADAPTERS
    expected = {
        "perekrestok", "pyaterochka", "magnit", "lenta", "auchan", "metro",
        "vkusvill", "apteka_ru", "eapteka", "zdravcity", "detskiy_mir",
        "korablik", "zolla", "sela", "finn_flare", "baon", "onlinetrade",
        "holodilnik", "autodoc", "four_lapy"
    }
    assert expected.issubset(ADAPTERS.keys())
'''
    tests.write_text(t, encoding="utf-8")
