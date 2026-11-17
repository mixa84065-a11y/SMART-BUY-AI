from pathlib import Path
import re

p = Path("app/src/main/java/com/smartbuy/ai/MainActivity.java")
s = p.read_text(encoding="utf-8")

def replace_method(name, next_name, body):
    global s
    pattern = rf"    void {name}\([^)]*\)\s*\{{.*?(?=    void {next_name}\()"
    s2, n = re.subn(pattern, body + "\n", s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"Could not replace method {name}: {n}")
    s = s2

# New visual palette matching the approved purple mockup.
s = s.replace(
    "final int BG=0xFF0B1020, PANEL=0xFF151D32, PANEL2=0xFF1D2942, TEXT=0xFFF4F6FF,\n        MUTED=0xFF9AA8C4, PURPLE=0xFF8B78FF, GREEN=0xFF48D6A0, GOLD=0xFFFFC86B;",
    "final int BG=0xFF08091A, PANEL=0xFF11132B, PANEL2=0xFF1B1C42, TEXT=0xFFF7F4FF,\n        MUTED=0xFFB5B0D0, PURPLE=0xFF842BFF, GREEN=0xFF39E58C, GOLD=0xFFFFC86B;"
)

# Header: compact brand lockup and menu button.
start = s.index("    void header(){")
end = s.index("    void nav(){", start)
header = """    void header(){
        LinearLayout h=new LinearLayout(this);h.setGravity(Gravity.CENTER_VERTICAL);h.setPadding(dp(2),dp(4),dp(2),dp(8));
        TextView logo=txt("🛒",31,0xFFB77BFF,true);h.addView(logo);
        LinearLayout names=new LinearLayout(this);names.setOrientation(1);names.setPadding(dp(9),0,0,0);
        names.addView(txt("SMART BUY AI",19,TEXT,true));
        names.addView(txt("Сравнивай. Выбирай. Покупай выгодно!",9,MUTED,false));
        h.addView(names,new LinearLayout.LayoutParams(0,-2,1));
        TextView menu=txt("☰",25,TEXT,true);menu.setPadding(dp(12),dp(6),dp(4),dp(6));
        menu.setOnClickListener(v->{
            String[] items={"Обновить каталог","Все магазины","SMART BUY Premium","Настройки профиля"};
            new AlertDialog.Builder(this).setItems(items,(d,w)->{
                if(w==0)refreshRemoteCatalog(true);if(w==1)sourceList();if(w==2)premium();if(w==3)profile();
            }).show();
        });
        h.addView(menu);root.addView(h);
    }
"""
s=s[:start]+header+s[end:]

# Bottom navigation with active purple state.
start=s.index("    void buildNav(){")
end=s.index("    void reset(",start)
nav="""    void buildNav(){
        if(nav==null)return;
        nav.removeAllViews();nav.setBackground(round(0xFF101127,18));
        String[] labels={"Главная","Избранное","История","Профиль"};String[] icons={"⌂","♡","◷","♙"};
        for(int i=0;i<labels.length;i++){
            final int ix=i;boolean selected=labels[i].equals(activeNav);
            LinearLayout item=new LinearLayout(this);item.setOrientation(1);item.setGravity(Gravity.CENTER);
            item.setPadding(0,dp(5),0,dp(4));
            item.addView(txt(icons[i],23,selected?0xFFB66BFF:MUTED,true));
            item.addView(txt(labels[i],10,selected?TEXT:MUTED,selected));
            item.setOnClickListener(v->{if(ix==0)home();if(ix==1)favorites();if(ix==2)tracking();if(ix==3)profile();});
            nav.addView(item,new LinearLayout.LayoutParams(0,dp(58),1));
        }
    }
"""
s=s[:start]+nav+s[end:]

home="""    void home(){
        activeNav="Главная";buildNav();content.removeAllViews();
        LinearLayout searchBox=new LinearLayout(this);searchBox.setGravity(Gravity.CENTER_VERTICAL);
        searchBox.setPadding(dp(13),0,dp(12),0);searchBox.setBackground(round(0xFF201A4A,20));
        GradientDrawable sb=(GradientDrawable)searchBox.getBackground();sb.setStroke(dp(1),0xFF6343C8);
        search=new EditText(this);search.setSingleLine(true);search.setTextColor(TEXT);search.setHintTextColor(0xFFB8B1D7);
        search.setHint("Поиск товаров и брендов");search.setTextSize(15);search.setPadding(dp(3),dp(10),dp(3),dp(10));
        search.setBackgroundColor(Color.TRANSPARENT);searchBox.addView(txt("⌕",27,TEXT,false));
        searchBox.addView(search,new LinearLayout.LayoutParams(0,dp(52),1));
        TextView mic=txt("🎙",22,0xFFB15BFF,true);searchBox.addView(mic);
        LinearLayout.LayoutParams searchLp=new LinearLayout.LayoutParams(-1,-2);searchLp.setMargins(0,dp(8),0,dp(12));content.addView(searchBox,searchLp);
        search.setOnEditorActionListener((v,a,e)->{renderSearch(search.getText().toString());return true;});
        searchBox.setOnClickListener(v->{if(search!=null){search.requestFocus();((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).showSoftInput(search,InputMethodManager.SHOW_IMPLICIT);}});
        mic.setOnClickListener(v->Toast.makeText(this,"Голосовой поиск появится в следующем обновлении",Toast.LENGTH_SHORT).show());
        TextView go=action("Найти товары  →",PURPLE);content.addView(go);go.setOnClickListener(v->renderSearch(search.getText().toString()));

        LinearLayout categoryStrip=new LinearLayout(this);categoryStrip.setOrientation(0);
        HorizontalScrollView categoryScroll=new HorizontalScrollView(this);categoryScroll.setHorizontalScrollBarEnabled(false);
        String[] names={"Одежда","Электроника","Для дома","Красота","Ещё"};
        String[] icons={"👕","📱","⌂","🧴","▦"};
        for(int i=0;i<names.length;i++){
            final String cat=names[i].equals("Ещё")?"Все":names[i];
            LinearLayout tile=new LinearLayout(this);tile.setOrientation(1);tile.setGravity(Gravity.CENTER);
            TextView icon=txt(icons[i],25,0xFFDAD0FF,true);icon.setGravity(Gravity.CENTER);
            icon.setBackground(round(0xFF211D50,16));tile.addView(icon,new LinearLayout.LayoutParams(dp(62),dp(62)));
            TextView label=txt(names[i],10,TEXT,true);label.setGravity(Gravity.CENTER);label.setPadding(0,dp(5),0,0);tile.addView(label);
            LinearLayout.LayoutParams tlp=new LinearLayout.LayoutParams(dp(72),-2);tlp.setMargins(0,dp(7),dp(8),dp(6));categoryStrip.addView(tile,tlp);
            tile.setOnClickListener(v->{activeCategory=cat;renderCategory(cat);});
        }
        categoryScroll.addView(categoryStrip);content.addView(categoryScroll);
        LinearLayout smart=new LinearLayout(this);smart.setGravity(Gravity.CENTER_VERTICAL);smart.setPadding(dp(16),dp(14),dp(14),dp(14));
        GradientDrawable smartBg=new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,new int[]{0xFF6B12F5,0xFF32116F,0xFF1A1648});smartBg.setCornerRadius(dp(20));smartBg.setStroke(dp(1),0xFF8D54FF);smart.setBackground(smartBg);
        TextView star=txt("⭐",32,GOLD,true);smart.addView(star);
        LinearLayout smartText=new LinearLayout(this);smartText.setOrientation(1);smartText.setPadding(dp(10),0,0,0);
        smartText.addView(txt("Умный поиск и сравнение",15,Color.WHITE,true));
        smartText.addView(txt("Найдём лучшие предложения\nво всех магазинах",11,0xFFE4D9FF,false));
        smart.addView(smartText,new LinearLayout.LayoutParams(0,-2,1));smart.addView(txt("›",30,Color.WHITE,true));
        LinearLayout.LayoutParams smartLp=new LinearLayout.LayoutParams(-1,-2);smartLp.setMargins(0,dp(10),0,dp(8));content.addView(smart,smartLp);
        smart.setOnClickListener(v->{search.setText("");search.requestFocus();((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).showSoftInput(search,InputMethodManager.SHOW_IMPLICIT);});
        content.addView(section("Популярные категории"));
        LinearLayout popular=new LinearLayout(this);HorizontalScrollView popScroll=new HorizontalScrollView(this);popScroll.setHorizontalScrollBarEnabled(false);
        String[] popularNames={"Кроссовки","Куртки","Платья","Смартфоны","Наушники"};
        String[] popularIcons={"👟","🧥","👗","📱","🎧"};
        for(int i=0;i<popularNames.length;i++){
            final String label=popularNames[i];LinearLayout item=new LinearLayout(this);item.setOrientation(1);item.setGravity(Gravity.CENTER);
            TextView art=txt(popularIcons[i],31,TEXT,true);art.setGravity(Gravity.CENTER);art.setBackground(round(0xFF171A3A,17));item.addView(art,new LinearLayout.LayoutParams(dp(82),dp(82)));
            TextView cap=txt(label,10,TEXT,true);cap.setGravity(Gravity.CENTER);cap.setPadding(0,dp(5),0,0);item.addView(cap);
            LinearLayout.LayoutParams ip=new LinearLayout.LayoutParams(dp(88),-2);ip.setMargins(0,dp(5),dp(8),0);popular.addView(item,ip);
            item.setOnClickListener(v->{search.setText(label);renderSearch(label);});
        }
        popScroll.addView(popular);content.addView(popScroll);
        content.addView(section("Преимущества"));
        LinearLayout advantages=new LinearLayout(this);String[] advIcons={"🛡","⚖","★","ϟ"};String[] adv={"Проверенные\nмагазины","Полное\nсравнение","Реальные\nотзывы","Выгодные\nцены"};
        for(int i=0;i<adv.length;i++){LinearLayout a=new LinearLayout(this);a.setOrientation(1);a.setGravity(Gravity.CENTER);a.setPadding(dp(4),dp(10),dp(4),dp(10));a.setBackground(round(0xFF19183D,15));a.addView(txt(advIcons[i],23,i==3?GOLD:0xFFD1B9FF,true));TextView t=txt(adv[i],9,TEXT,true);t.setGravity(Gravity.CENTER);a.addView(t);LinearLayout.LayoutParams ap=new LinearLayout.LayoutParams(0,dp(92),1);ap.setMargins(dp(2),dp(4),dp(2),dp(4));advantages.addView(a,ap);}
        content.addView(advantages);
        LinearLayout promo=new LinearLayout(this);promo.setGravity(Gravity.CENTER_VERTICAL);promo.setPadding(dp(12),dp(12),dp(12),dp(12));
        GradientDrawable promoBg=new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,new int[]{0xFF2115A4,0xFF4E0BC4,0xFF7419D8});promoBg.setCornerRadius(dp(20));promo.setBackground(promoBg);
        promo.addView(txt("🤖",54,Color.WHITE,true));
        LinearLayout promoText=new LinearLayout(this);promoText.setOrientation(1);promoText.setPadding(dp(8),0,0,0);
        promoText.addView(txt("SMART BUY AI",16,GOLD,true));promoText.addView(txt("Найди лучшую цену\nс ИИ!",13,Color.WHITE,true));
        TextView start=txt("Начать поиск  →",11,Color.WHITE,true);start.setGravity(Gravity.CENTER);start.setPadding(dp(10),dp(7),dp(10),dp(7));start.setBackground(round(0xFF8A2BFF,18));promoText.addView(start);
        promo.addView(promoText,new LinearLayout.LayoutParams(0,-2,1));LinearLayout.LayoutParams promoLp=new LinearLayout.LayoutParams(-1,-2);promoLp.setMargins(0,dp(13),0,dp(14));content.addView(promo,promoLp);
        promo.setOnClickListener(v->{search.requestFocus();((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).showSoftInput(search,InputMethodManager.SHOW_IMPLICIT);});
        String updated=prefs.getString("remote_catalog_updated","");
        content.addView(note("Каталог v"+catalogVersion,updated.isEmpty()?"Магазины и категории обновляются отдельно от APK.":"Обновлено: "+updated));
        content.addView(section("Выгодные предложения"));
        for(Product product:products){if(activeCategory.equals("Все")||product.category.equals(activeCategory))productCard(product);}
        content.addView(note("Важно","Демо-цены показываются только как пример интерфейса. Реальные предложения появятся после подключения и проверки товарных источников."));
    }
    void renderCategory(String category){
        activeCategory=category;home();
        if(!category.equals("Все"))Toast.makeText(this,"Категория: "+category,Toast.LENGTH_SHORT).show();
    }
"""
replace_method("home", "showClothingFilters", home)

product="""    void productCard(Product p){
        LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(12),dp(12),dp(12),dp(12));
        GradientDrawable cardBg=round(0xFF12152E,19);cardBg.setStroke(dp(1),0xFF39305F);card.setBackground(cardBg);
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-1,-2);cp.setMargins(0,dp(7),0,dp(7));content.addView(card,cp);
        LinearLayout top=new LinearLayout(this);top.setGravity(Gravity.CENTER_VERTICAL);
        TextView em=txt(p.emoji,32,TEXT,true);em.setGravity(Gravity.CENTER);em.setBackground(round(0xFFF0EFF6,15));top.addView(em,new LinearLayout.LayoutParams(dp(76),dp(76)));
        LinearLayout info=new LinearLayout(this);info.setOrientation(1);info.setPadding(dp(10),0,dp(3),0);
        info.addView(txt(p.name,14,TEXT,true));info.addView(txt("★  Рейтинг появится из подключённых источников",9,MUTED,false));
        top.addView(info,new LinearLayout.LayoutParams(0,-2,1));
        TextView fav=txt(isFav(p)?"♥":"♡",23,isFav(p)?0xFFFF7799:MUTED,true);top.addView(fav);fav.setOnClickListener(v->{toggleFav(p);home();});
        card.addView(top);
        LinearLayout offers=new LinearLayout(this);offers.setGravity(Gravity.CENTER_VERTICAL);offers.setPadding(0,dp(10),0,dp(8));
        String[] shops={p.shop1,p.shop2,p.shop3};int[] prices={p.p1,p.p2,p.p3};
        for(int i=0;i<3;i++){LinearLayout cell=new LinearLayout(this);cell.setOrientation(1);cell.setPadding(dp(5),dp(7),dp(3),dp(7));cell.setBackground(round(0xFF1B1B39,10));
            cell.addView(txt(shops[i],9,0xFFE1D9FF,true));cell.addView(txt(money(prices[i]),14,Color.WHITE,true));cell.addView(txt("пример цены",8,MUTED,false));
            LinearLayout.LayoutParams clp=new LinearLayout.LayoutParams(0,-2,1);clp.setMargins(dp(2),0,dp(2),0);offers.addView(cell,clp);}
        card.addView(offers);
        LinearLayout bottom=new LinearLayout(this);bottom.setGravity(Gravity.CENTER_VERTICAL);bottom.setPadding(dp(9),dp(8),dp(8),dp(8));bottom.setBackground(round(0xFF101B2B,13));
        bottom.addView(txt("✓  Демо: от "+money(p.min()),12,GREEN,true),new LinearLayout.LayoutParams(0,-2,1));
        TextView more=txt("Подробнее  →",12,Color.WHITE,true);more.setGravity(Gravity.CENTER);more.setPadding(dp(12),dp(9),dp(12),dp(9));more.setBackground(round(PURPLE,16));bottom.addView(more);
        card.addView(bottom);card.setOnClickListener(v->detail(p));more.setOnClickListener(v->detail(p));
    }
"""
replace_method("productCard", "detail", product)

s=s.replace('content.addView(section("Категории"));','content.addView(section("Категории"));')
# Stronger headings and rounded action controls.
s=s.replace('TextView t=txt(s,16,TEXT,true);','TextView t=txt(s,18,TEXT,true);')
s=s.replace('GradientDrawable actionBg=round(color,14);','GradientDrawable actionBg=round(color==PURPLE?0xFF7624F4:color,18);')
# Bump app version but retain package ID/signing identity.
g=Path("app/build.gradle")
gs=g.read_text(encoding="utf-8")
gs=gs.replace("versionCode 19","versionCode 20",1).replace("versionName '0.5.9'","versionName '0.6.0'",1)
g.write_text(gs,encoding="utf-8")

p.write_text(s,encoding="utf-8")
print("SMART BUY AI v0.6.0 purple mockup UI applied")
