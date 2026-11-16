from pathlib import Path
p=Path("app/src/main/java/com/smartbuy/ai/MainActivity.java")
s=p.read_text(encoding="utf-8")
s=s.replace('    final String[] categories={','    String[] categories={',1)
s=s.replace('    final ArrayList<Product> products=new ArrayList<>();','    final ArrayList<Product> products=new ArrayList<>();\n    static final String CATALOG_URL="https://raw.githubusercontent.com/mixa84065-a11y/SMART-BUY-AI/main/catalog/catalog.json";\n    String catalogVersion="local";',1)
s=s.replace('        prefs=getSharedPreferences("smartbuy",MODE_PRIVATE);\n        seed();','        prefs=getSharedPreferences("smartbuy",MODE_PRIVATE);\n        loadCachedCatalogState();\n        seed();',1)
s=s.replace('        home();\n    }\n    void seed(){','        home();\n        refreshRemoteCatalog(false);\n    }\n    void seed(){',1)
old='TextView pro=txt("Premium",10,GOLD,true);pro.setPadding(dp(11),dp(8),dp(11),dp(8));pro.setBackground(round(0xFF3B3024,24));pro.setOnClickListener(v->premium());h.addView(pro);'
if old not in s: raise SystemExit("header anchor missing")
s=s.replace(old,old+'\n        TextView refresh=txt("↻",23,GOLD,true);refresh.setPadding(dp(10),dp(3),dp(2),dp(3));refresh.setOnClickListener(v->refreshRemoteCatalog(true));h.addView(refresh);',1)
s=s.replace('        content.addView(section("Категории"));','        String updated=prefs.getString("remote_catalog_updated","");\n        content.addView(note("Облачный каталог v"+catalogVersion,updated.isEmpty()?"Магазины и категории обновляются отдельно от APK.":"Последнее обновление каталога: "+updated));\n        content.addView(section("Категории"));',1)
start=s.index('        String[][] stores={',s.index('    void keylessStoreSearch'))
end=s.index('        String last="";',start)
s=s[:start]+'        String[][] stores=getCatalogStores();\n'+s[end:]
start=s.index('    void sourceList(){')
end=s.index('    void favorites(){',start)
s=s[:start]+'''    void sourceList(){
        reset("Источники сравнения","Облачный список магазинов • каталог v"+catalogVersion);
        content.addView(note("Каталог обновляется отдельно от приложения","Нажми ↻ в верхней части экрана, чтобы проверить обновления. Список магазинов хранится на телефоне и доступен офлайн."));
        String[][] stores=getCatalogStores();String last="";
        for(String[] row:stores){if(!row[2].equals(last)){content.addView(section(row[2]));last=row[2];}
            TextView item=action(row[0]+"  ·  открыть поиск",PANEL2);content.addView(item);
            item.setOnClickListener(v->openStoreSearch("товары",row[0],row[1]));}
        content.addView(note("Важное ограничение","Наличие магазина в каталоге не означает, что он передаёт нам цены или отзывы. Автоматическое сравнение доступно только для подключённых разрешённых фидов. Поиск без фида открывает публичные страницы магазина."));
    }
'''+s[end:]
anchor='    void keylessStoreSearch(String q){'
methods='''    void loadCachedCatalogState(){
        catalogVersion=prefs.getString("remote_catalog_version","local");
        try{JSONObject cached=new JSONObject(prefs.getString("remote_catalog_json",""));JSONArray cats=cached.optJSONArray("categories");if(cats!=null&&cats.length()>0){ArrayList<String> list=new ArrayList<>();for(int i=0;i<cats.length();i++){String c=cats.optString(i,"").trim();if(!c.isEmpty())list.add(c);}if(!list.isEmpty())categories=list.toArray(new String[0]);}}catch(Exception ignored){}
    }
    String[][] getCatalogStores(){
        try{JSONObject catalog=new JSONObject(prefs.getString("remote_catalog_json",""));JSONArray arr=catalog.optJSONArray("stores");
            if(arr!=null&&arr.length()>0){ArrayList<String[]> out=new ArrayList<>();for(int i=0;i<arr.length();i++){JSONObject o=arr.optJSONObject(i);if(o==null)continue;
                String name=o.optString("name","").trim(),domain=o.optString("domain","").trim(),group=o.optString("group","Другие магазины").trim();
                if(name.isEmpty()||domain.isEmpty()||domain.contains("/")||domain.contains(" "))continue;out.add(new String[]{name,domain,group});}
                if(!out.isEmpty())return out.toArray(new String[0][]);}}
        catch(Exception ignored){}
        return new String[][]{{"Wildberries","wildberries.ru","Маркетплейсы"},{"Ozon","ozon.ru","Маркетплейсы"},{"Яндекс Маркет","market.yandex.ru","Маркетплейсы"},{"Мегамаркет","megamarket.ru","Маркетплейсы"},{"AliExpress","aliexpress.ru","Международные площадки"},{"Alibaba","alibaba.com","Международные площадки"}};
    }
    void refreshRemoteCatalog(boolean manual){
        new Thread(()->{HttpURLConnection connection=null;try{
            URL url=new URL(CATALOG_URL);connection=(HttpURLConnection)url.openConnection();connection.setRequestMethod("GET");
            connection.setConnectTimeout(7000);connection.setReadTimeout(10000);connection.setRequestProperty("Cache-Control","no-cache");
            int code=connection.getResponseCode();if(code<200||code>=300)throw new Exception("HTTP "+code);
            ByteArrayOutputStream buffer=new ByteArrayOutputStream();InputStream in=connection.getInputStream();byte[] chunk=new byte[4096];int n;
            while((n=in.read(chunk))!=-1){if(buffer.size()>2*1024*1024)throw new Exception("Каталог слишком большой");buffer.write(chunk,0,n);}
            JSONObject data=new JSONObject(buffer.toString("UTF-8"));JSONArray stores=data.optJSONArray("stores");
            if(stores==null||stores.length()==0)throw new Exception("В каталоге нет магазинов");
            String version=data.optString("version","1");
            prefs.edit().putString("remote_catalog_json",data.toString()).putString("remote_catalog_version",version).putString("remote_catalog_updated",data.optString("updated_at","")).apply();
            runOnUiThread(()->{catalogVersion=version;JSONArray cats=data.optJSONArray("categories");
                if(cats!=null&&cats.length()>0){ArrayList<String> list=new ArrayList<>();for(int i=0;i<cats.length();i++){String c=cats.optString(i,"").trim();if(!c.isEmpty())list.add(c);}if(!list.isEmpty())categories=list.toArray(new String[0]);}
                if(manual)Toast.makeText(this,"Каталог обновлён: v"+catalogVersion+", магазинов: "+stores.length(),Toast.LENGTH_LONG).show();
                if(!manual&&"Главная".equals(activeNav))home();});
        }catch(Exception ex){runOnUiThread(()->{if(manual)Toast.makeText(this,"Не удалось обновить каталог. Используется сохранённая версия.",Toast.LENGTH_LONG).show();});}
        finally{if(connection!=null)connection.disconnect();}}).start();
    }
'''
if anchor not in s: raise SystemExit("keyless method anchor missing")
s=s.replace(anchor,methods+anchor,1)
p.write_text(s,encoding="utf-8")
gradle=Path("app/build.gradle")
g=gradle.read_text(encoding="utf-8").replace("versionCode 14","versionCode 15").replace("versionName '0.5.4'","versionName '0.5.5'")
if g==gradle.read_text(encoding="utf-8"): raise SystemExit("Expected v0.5.4 version markers were not found")
gradle.write_text(g,encoding="utf-8")
