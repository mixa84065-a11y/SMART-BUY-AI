from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_FILE = ROOT / "backend" / "app" / "main.py"

if not APP_FILE.is_file():
    raise SystemExit(f"FastAPI entrypoint not found: {APP_FILE}")

source = APP_FILE.read_text(encoding="utf-8")
if "from fastapi.responses import HTMLResponse" not in source:
    source = "from fastapi.responses import HTMLResponse\n" + source

marker = '@app.get("/",'
if marker not in source:
    route = r"""

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def smart_buy_public_site():
    """Public information page for SMART BUY AI."""
    return HTMLResponse(content="""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="SMART BUY AI — приложение для поиска товаров и сравнения предложений магазинов.">
<title>SMART BUY AI — умный поиск и сравнение покупок</title>
<style>
:root{color-scheme:dark;--bg:#090d18;--panel:#111a2b;--gold:#f4c95d;--muted:#aeb9ca;--line:#26344b}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 80% 0%,#1b2945 0,transparent 42%),var(--bg);color:#f6f7fb;font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{width:min(980px,calc(100% - 32px));margin:0 auto;padding:54px 0 40px}
.brand{color:var(--gold);font-weight:800;letter-spacing:.16em;font-size:14px}
h1{font-size:clamp(36px,7vw,64px);line-height:1.05;margin:18px 0}
h2{font-size:25px;margin:0 0 12px}.lead{font-size:19px;color:#d8dfeb;max-width:760px}
section,.feature{background:linear-gradient(145deg,#141f33,#0f1727);border:1px solid var(--line);border-radius:20px;padding:24px;margin-top:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:24px}
.feature h3{margin:0 0 7px;color:var(--gold)}.feature p,section p{margin:0;color:var(--muted)}
.pill{display:inline-block;border:1px solid #66552b;border-radius:99px;padding:6px 12px;color:var(--gold);font-size:13px}
a{color:var(--gold)}footer{margin-top:30px;color:var(--muted);font-size:13px}
</style>
</head>
<body><main>
<div class="brand">SMART BUY AI</div>
<h1>Покупать разумнее.<br>Сравнивать проще.</h1>
<p class="lead">SMART BUY AI — мобильное приложение для поиска товаров и сравнения предложений российских и международных интернет-магазинов. Помогает ориентироваться в ассортименте и принимать более взвешенные решения о покупке.</p>
<p><span class="pill">Приложение для Android</span> <span class="pill">Русский язык</span></p>
<div class="grid">
<article class="feature"><h3>Каталог магазинов</h3><p>Категории товаров и подборка российских и международных торговых площадок, включая маркетплейсы.</p></article>
<article class="feature"><h3>Сравнение предложений</h3><p>Задача сервиса — сопоставлять предложения магазинов, чтобы пользователю было удобнее выбирать товары.</p></article>
<article class="feature"><h3>История цен</h3><p>Раздел для отслеживания изменения стоимости товара по мере поступления и накопления данных.</p></article>
<article class="feature"><h3>Отзывы и рейтинги</h3><p>Предусмотрено отображение отзывов и оценок там, где такие данные доступны из подключённых источников.</p></article>
<article class="feature"><h3>ИИ-рекомендации</h3><p>Помощь в подборе товаров и сравнении характеристик на основе доступной информации.</p></article>
<article class="feature"><h3>Обновляемый каталог</h3><p>Список магазинов и категорий может обновляться на сервере независимо от обновления Android-приложения.</p></article>
</div>
<section><h2>Текущий статус сервиса</h2><p>SMART BUY AI развивается. Наличие магазина в каталоге не означает, что для него уже подключена передача актуальных цен и остатков. Реальные предложения, история цен, отзывы и рекомендации доступны по мере подключения и проверки соответствующих источников данных. Мы не заявляем о наличии данных, которые ещё не поступают.</p></section>
<section><h2>О приложении</h2><p>Платформа: Android. Назначение: поиск товаров, каталог магазинов и сравнение торговых предложений. Название приложения: SMART BUY AI.</p><p style="margin-top:12px"><a href="https://github.com/mixa84065-a11y/SMART-BUY-AI">Репозиторий проекта и информация о разработке</a></p></section>
<footer>© SMART BUY AI. Информация на странице описывает назначение и текущую стадию развития сервиса.</footer>
</main></body></html>""")
"""
    source = source.rstrip() + "\n" + route + "\n"

APP_FILE.write_text(source, encoding="utf-8")
print(f"SMART BUY AI public information page added to {APP_FILE}")
