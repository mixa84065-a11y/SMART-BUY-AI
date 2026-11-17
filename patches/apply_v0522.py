from pathlib import Path
import re

main = Path("app/src/main/java/com/smartbuy/ai/MainActivity.java")
if not main.is_file():
    raise SystemExit("Android MainActivity.java not found after source archive extraction.")
s = main.read_text(encoding="utf-8")

if "import android.graphics.BitmapFactory;" not in s:
    s = s.replace("import android.graphics.Color;\n", "import android.graphics.Color;\nimport android.graphics.BitmapFactory;\n")
if "static final String DEFAULT_API_BASE" not in s:
    s = s.replace(
        '    static final String CATALOG_URL="https://raw.githubusercontent.com/mixa84065-a11y/SMART-BUY-AI/main/catalog/catalog.json";',
        '    static final String CATALOG_URL="https://raw.githubusercontent.com/mixa84065-a11y/SMART-BUY-AI/main/catalog/catalog.json";\n'
        '    static final String DEFAULT_API_BASE="https://smart-buy-ai-api-xe0j.onrender.com";'
    )

def replace_method(name, next_name, body):
    global s
    pattern = rf"    void {name}\([^)]*\)\s*\{{.*?(?=    (?:void|static class) {next_name}\b)"
    updated, count = re.subn(pattern, body + "\n", s, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"Cannot safely replace {name}(): matched {count}")
    s = updated

render = '''    void renderSearch(String q){
        if(q.trim().isEmpty()){home();return;}
        String server=prefs.getString("api_base_url",DEFAULT_API_BASE).trim();
        if(server.isEmpty())server=DEFAULT_API_BASE;
        remoteSearch(q,server);
    }
'''
replace_method("renderSearch", "StoreSearch", render)

# Append the public Plati catalogue to both successful and empty discovery results.
s = s.replace(
    'content.addView(note("Пока нет предложений",data.optString("data_note","В подключённых открытых фидах совпадений нет.")));\n'
    '                        loadMatchingCandidates(q, server);',
    'content.addView(note("Пока нет предложений из обычных фидов",data.optString("data_note","Проверяем дополнительные открытые каталоги.")));\n'
    '                        searchPlatiCatalog(q,server);\n'
    '                        loadMatchingCandidates(q, server);'
)
s = s.replace(
    'content.addView(note("Источник данных",data.optString("data_note","Предложения получены из подключённых фидов.")));\n'
    '                    // Cross-store product identity matching',
    'content.addView(note("Источник данных",data.optString("data_note","Предложения получены из подключённых фидов.")));\n'
    '                    searchPlatiCatalog(q,server);\n'
    '                    // Cross-store product identity matching'
)
s = s.replace(
    'content.addView(note("Проверь адрес сервера",ex.getMessage()==null?"Ошибка соединения":ex.getMessage()));});}',
    'content.addView(note("Проверь адрес сервера",ex.getMessage()==null?"Ошибка соединения":ex.getMessage()));searchPlatiCatalog(q,server);});}'
)

# Add Plati search and safe product-card rendering before matching-candidates helper.
if "void searchPlatiCatalog(" not in s:
    insert_at = s.index("    void loadMatchingCandidates(")
    methods = r'''    void searchPlatiCatalog(String q,String server){
        new Thread(()->{
            HttpURLConnection connection=null;
            try{
                String endpoint=server+"/v1/integrations/plati/search?q="+java.net.URLEncoder.encode(q,"UTF-8")+"&page=1&page_size=10";
                URL url=new URL(endpoint);
                connection=(HttpURLConnection)url.openConnection();connection.setRequestMethod("GET");
                connection.setConnectTimeout(10000);connection.setReadTimeout(30000);
                int code=connection.getResponseCode();
                InputStream stream=(code>=200&&code<300)?connection.getInputStream():connection.getErrorStream();
                ByteArrayOutputStream buffer=new ByteArrayOutputStream();byte[] chunk=new byte[4096];int n;
                while((n=stream.read(chunk))!=-1){if(buffer.size()>2*1024*1024)throw new Exception("Ответ слишком большой");buffer.write(chunk,0,n);}
                if(code<200||code>=300)throw new Exception("HTTP "+code);
                JSONObject data=new JSONObject(buffer.toString("UTF-8"));JSONArray items=data.optJSONArray("products");
                runOnUiThread(()->{
                    content.addView(section("Plati.Market — цифровые товары"));
                    if(items==null||items.length()==0){
                        content.addView(note("Поиск Plati.Market", "По этому запросу предложений не найдено. Попробуй уточнить название."));
                        return;
                    }
                    content.addView(note("Найдено предложений: "+items.length(),
                        "Источник: публичный каталог Plati.Market. Цены указаны в рублях и могут измениться у продавца."));
                    for(int i=0;i<items.length();i++){
                        JSONObject item=items.optJSONObject(i);if(item==null)continue;
                        addPlatiProductCard(item);
                    }
                });
            }catch(Exception ex){
                runOnUiThread(()->{
                    content.addView(section("Plati.Market"));
                    content.addView(note("Источник временно недоступен", "Обычный поиск и открытие магазинов остаются доступны. Повтори запрос позже."));
                });
            }finally{if(connection!=null)connection.disconnect();}
        }).start();
    }

    void addPlatiProductCard(JSONObject item){
        LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(12),dp(12),dp(12),dp(12));
        GradientDrawable bg=round(0xFF12152E,18);bg.setStroke(dp(1),0xFF493276);card.setBackground(bg);
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-1,-2);cp.setMargins(0,dp(6),0,dp(6));content.addView(card,cp);
        LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);
        ImageView image=new ImageView(this);image.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        image.setBackground(round(Color.WHITE,12));image.setPadding(dp(4),dp(4),dp(4),dp(4));
        row.addView(image,new LinearLayout.LayoutParams(dp(82),dp(82)));
        String imageUrl=item.optString("image","");
        if(!imageUrl.isEmpty())loadPlatiImage(imageUrl,image);
        LinearLayout info=new LinearLayout(this);info.setOrientation(1);info.setPadding(dp(10),0,0,0);
        String title=item.optString("title","Цифровой товар");
        info.addView(txt(title,13,TEXT,true));
        JSONObject seller=item.optJSONObject("seller");
        String sellerName=seller==null?"Продавец Plati.Market":seller.optString("name","Продавец Plati.Market");
        info.addView(txt(sellerName,10,MUTED,false));
        if(item.has("sold"))info.addView(txt("Продано: "+item.optString("sold"),9,MUTED,false));
        row.addView(info,new LinearLayout.LayoutParams(0,-2,1));card.addView(row);
        double price=item.optDouble("price",0);
        String priceText=price>0?String.format(java.util.Locale.US,"%,.2f ₽",price).replace(',',' '):"Цена уточняется";
        TextView priceView=txt(priceText,18,GOLD,true);priceView.setPadding(0,dp(10),0,dp(5));card.addView(priceView);
        String description=item.optString("description","").trim();
        if(!description.isEmpty())card.addView(txt(description.length()>240?description.substring(0,240)+"…":description,10,MUTED,false));
        TextView open=action("Открыть предложение на Plati.Market  ↗",PURPLE);card.addView(open);
        String productUrl=item.optString("url","");
        open.setOnClickListener(v->openPlatiUrl(productUrl));
        card.setOnClickListener(v->openPlatiUrl(productUrl));
    }

    void loadPlatiImage(String address,ImageView target){
        try{
            Uri uri=Uri.parse(address);
            if(!"https".equalsIgnoreCase(uri.getScheme())||!"graph.digiseller.ru".equalsIgnoreCase(uri.getHost()))return;
            new Thread(()->{
                HttpURLConnection c=null;
                try{
                    c=(HttpURLConnection)new URL(address).openConnection();c.setConnectTimeout(6000);c.setReadTimeout(8000);
                    c.setInstanceFollowRedirects(false);
                    if(c.getResponseCode()!=200)return;
                    InputStream in=c.getInputStream();android.graphics.Bitmap bitmap=BitmapFactory.decodeStream(in);in.close();
                    if(bitmap!=null)runOnUiThread(()->target.setImageBitmap(bitmap));
                }catch(Exception ignored){}finally{if(c!=null)c.disconnect();}
            }).start();
        }catch(Exception ignored){}
    }

    void openPlatiUrl(String address){
        try{
            Uri uri=Uri.parse(address);
            String host=uri.getHost();
            if(!"https".equalsIgnoreCase(uri.getScheme())||host==null||
                !(host.equalsIgnoreCase("plati.market")||host.equalsIgnoreCase("www.plati.market"))){
                Toast.makeText(this,"Некорректная ссылка на товар",Toast.LENGTH_SHORT).show();return;
            }
            startActivity(new Intent(Intent.ACTION_VIEW,uri));
        }catch(Exception e){Toast.makeText(this,"Не удалось открыть предложение",Toast.LENGTH_SHORT).show();}
    }

'''
    s = s[:insert_at] + methods + s[insert_at:]

# Default API server appears in profile and is used without manual setup.
s = s.replace('endpoint.setHint("https://адрес-вашего-сервера"); endpoint.setText(prefs.getString("api_base_url", ""));',
              'endpoint.setHint("https://адрес-вашего-сервера"); endpoint.setText(prefs.getString("api_base_url", DEFAULT_API_BASE));')
s = s.replace('content.addView(note("Поиск без API-ключей","Без сервера приложение открывает поисковые страницы магазинов.',
              'content.addView(note("Поиск без API-ключей","Сервер SMART BUY AI подключён по умолчанию. Без него приложение открывает поисковые страницы магазинов.')

main.write_text(s, encoding="utf-8")

gradle = Path("app/build.gradle")
g = gradle.read_text(encoding="utf-8")
g = re.sub(r"versionCode\s+21", "versionCode 22", g, count=1)
g = re.sub(r"versionName\s+'0\.6\.1'", "versionName '0.6.2'", g, count=1)
gradle.write_text(g, encoding="utf-8")
print("Added live Plati.Market search cards to Android app; package ID and signing config preserved.")
