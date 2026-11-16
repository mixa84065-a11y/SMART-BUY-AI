from pathlib import Path

def replace_once(path, old, new):
    p = Path(path)
    source = p.read_text(encoding="utf-8")
    if old not in source:
        raise SystemExit(f"Patch anchor not found in {path}: {old[:100]!r}")
    p.write_text(source.replace(old, new, 1), encoding="utf-8")

java = "app/src/main/java/com/smartbuy/ai/MainActivity.java"
replace_once(java,
'            {"AliExpress","aliexpress.ru","Международные площадки"},{"Alibaba","alibaba.com","Международные площадки"}',
'''            {"Lamoda","lamoda.ru","Одежда и обувь"},{"Спортмастер","sportmaster.ru","Спорт и одежда"},{"Kari","kari.com","Обувь и аксессуары"},{"Gloria Jeans","gloria-jeans.ru","Одежда"},{"O'STIN","ostin.com","Одежда"},{"Befree","befree.ru","Одежда"},{"Zarina","zarina.ru","Одежда"},{"Love Republic","loverepublic.ru","Одежда"},{"Henderson","henderson.ru","Мужская одежда"},{"Rendez-Vous","rendez-vous.ru","Обувь"},
            {"Hoff","hoff.ru","Мебель и дом"},{"Лемана ПРО","lemanapro.ru","Дом и ремонт"},{"Петрович","petrovich.ru","Стройматериалы"},{"Максидом","maxidom.ru","Дом и ремонт"},{"ВсеИнструменты.ру","vseinstrumenti.ru","Инструменты"},{"Askona","askona.ru","Матрасы и мебель"},{"divan.ru","divan.ru","Мебель"},{"Столплит","stolplit.ru","Мебель"},{"Много мебели","mnogomebeli.com","Мебель"},{"Твой Дом","tvoedom.ru","Товары для дома"},{"Kuchenland","kuchenland.ru","Посуда и дом"},{"Ещё","eshe.club","Дискаунтер и товары для дома"},
            {"М.Видео","mvideo.ru","Электроника"},{"Эльдорадо","eldorado.ru","Электроника"},{"DNS","dns-shop.ru","Электроника"},{"Ситилинк","citilink.ru","Электроника"},{"Читай-город","chitai-gorod.ru","Книги"},{"Лэтуаль","letu.ru","Красота"},{"Рив Гош","rivegauche.ru","Красота"},
            {"AliExpress","aliexpress.ru","Международные площадки"},{"Alibaba","alibaba.com","Международные площадки"}''')

replace_once(java,
'        content.addView(note("Дополнительные бренды одежды","Zolla • SELA • Finn Flare • BAON"));',
'''        content.addView(note("Дополнительные бренды одежды","Zolla • SELA • Finn Flare • BAON • Lamoda • Спортмастер • Kari • Gloria Jeans • O'STIN • Befree • Zarina • Love Republic • Henderson • Rendez-Vous"));
        content.addView(note("Электроника","М.Видео • Эльдорадо • DNS • Ситилинк"));
        content.addView(note("Мебель, ремонт и дом","Hoff • Лемана ПРО • Петрович • Максидом • ВсеИнструменты.ру • Askona • divan.ru • Столплит • Много мебели • Твой Дом • Kuchenland • Ещё"));
        content.addView(note("Книги и косметика","Читай-город • Лэтуаль • Рив Гош"));''')

replace_once(java,
'        products.add(new Product("Детская настольная игра","Игрушки","🎲",1490,1390,1690,"Магазин A","Магазин B","Магазин C"));',
'''        products.add(new Product("Детская настольная игра","Игрушки","🎲",1490,1390,1690,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Платье повседневное","Женская одежда","👗",3490,3190,3890,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Куртка демисезонная","Мужская одежда","🧥",7990,7490,8990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Кроссовки повседневные","Обувь","👟",4990,4590,5490,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Шкаф для спальни","Мебель","🚪",21990,19990,23990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Набор кастрюль","Дом","🍲",4290,3990,4790,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Перфоратор SDS-plus","Сад и ремонт","🔧",8990,8490,9990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Смартфон 256 ГБ","Телефоны","📱",32990,30990,35990,"Магазин A","Магазин B","Магазин C"));
        products.add(new Product("Наушники беспроводные","Электроника","🎧",5990,5490,6490,"Магазин A","Магазин B","Магазин C"));''')

gradle = Path("app/build.gradle")
g = gradle.read_text(encoding="utf-8").replace("versionCode 13", "versionCode 14").replace("versionName '0.5.3'", "versionName '0.5.4'")
if g == gradle.read_text(encoding="utf-8"):
    raise SystemExit("Expected v0.5.3 version markers were not found")
gradle.write_text(g, encoding="utf-8")

registry = Path("backend/app/adapters/registry.py")
r = registry.read_text(encoding="utf-8")
anchor = '    "zdravcity": "Аптечный ассортимент: требуется разрешённый источник и отдельная проверка правил отображения лекарств.",\n'
addition = '''    "lamoda": "Одежда и обувь: требуется разрешённый товарный фид или партнёрский доступ.",
    "sportmaster": "Спорт и одежда: требуется разрешённый товарный фид или партнёрский доступ.",
    "kari": "Обувь и аксессуары: требуется разрешённый товарный фид или партнёрский доступ.",
    "gloria_jeans": "Одежда: требуется разрешённый товарный фид или партнёрский доступ.",
    "ostin": "Одежда: требуется разрешённый товарный фид или партнёрский доступ.",
    "befree": "Одежда: требуется разрешённый товарный фид или партнёрский доступ.",
    "zarina": "Одежда: требуется разрешённый товарный фид или партнёрский доступ.",
    "love_republic": "Одежда: требуется разрешённый товарный фид или партнёрский доступ.",
    "henderson": "Мужская одежда: требуется разрешённый товарный фид или партнёрский доступ.",
    "rendez_vous": "Обувь и аксессуары: требуется разрешённый товарный фид или партнёрский доступ.",
    "hoff": "Мебель и товары для дома: требуется разрешённый товарный фид или партнёрский доступ.",
    "lemanapro": "Товары для дома и ремонта: требуется разрешённый товарный фид или партнёрский доступ.",
    "petrovich": "Стройматериалы: требуется разрешённый товарный фид или партнёрский доступ.",
    "maxidom": "Товары для дома и ремонта: требуется разрешённый товарный фид или партнёрский доступ.",
    "askona": "Матрасы и мебель: требуется разрешённый товарный фид или партнёрский доступ.",
    "divan": "Мебель: требуется разрешённый товарный фид или партнёрский доступ.",
    "stolplit": "Мебель: требуется разрешённый товарный фид или партнёрский доступ.",
    "mnogomebeli": "Мебель: требуется разрешённый товарный фид или партнёрский доступ.",
    "tvoedom": "Товары для дома: требуется разрешённый товарный фид или партнёрский доступ.",
    "kuchenland": "Посуда и товары для дома: требуется разрешённый товарный фид или партнёрский доступ.",
    "eshe": "Дискаунтер и товары для дома: требуется разрешённый товарный фид или партнёрский доступ.",
    "mvideo": "Электроника: требуется разрешённый товарный фид или партнёрский доступ.",
    "eldorado": "Электроника: требуется разрешённый товарный фид или партнёрский доступ.",
    "dns": "Электроника и бытовая техника: требуется разрешённый товарный фид или партнёрский доступ.",
    "citilink": "Электроника и бытовая техника: требуется разрешённый товарный фид или партнёрский доступ.",
    "chitai_gorod": "Книги и канцелярия: требуется разрешённый товарный фид или партнёрский доступ.",
    "letu": "Красота и уход: требуется разрешённый товарный фид или партнёрский доступ.",
    "rivegauche": "Красота и уход: требуется разрешённый товарный фид или партнёрский доступ.",
'''
if anchor not in r: raise SystemExit("Registry v0.5.4 anchor missing")
registry.write_text(r.replace(anchor, anchor + addition, 1), encoding="utf-8")

tests = Path("backend/tests/test_discovery.py")
t = tests.read_text(encoding="utf-8")
if "test_registry_covers_v054_stores" not in t:
    t += '''

def test_registry_covers_v054_stores():
    from app.adapters.registry import ADAPTERS
    expected = {
        "lamoda", "sportmaster", "kari", "gloria_jeans", "ostin", "befree",
        "zarina", "love_republic", "henderson", "rendez_vous", "hoff",
        "lemanapro", "petrovich", "maxidom", "askona", "divan", "stolplit",
        "mnogomebeli", "tvoedom", "kuchenland", "eshe", "mvideo", "eldorado",
        "dns", "citilink", "chitai_gorod", "letu", "rivegauche"
    }
    assert expected.issubset(ADAPTERS.keys())
'''
    tests.write_text(t, encoding="utf-8")
