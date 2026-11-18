from pathlib import Path
import re

def once(path, old, new, label):
    p=Path(path); s=p.read_text(encoding='utf-8')
    if new in s: return
    if old not in s: raise SystemExit(f'{label}: patch anchor missing')
    p.write_text(s.replace(old,new,1),encoding='utf-8')

# Keep the product photo from YML/CSV feed rows all the way to Android.
once('backend/app/models.py','    url: Mapped[str | None] = mapped_column(Text, nullable=True)\n','    url: Mapped[str | None] = mapped_column(Text, nullable=True)\n    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)\n','Offer model')
once('backend/app/schemas.py','    url: str | None\n    is_wholesale: bool\n','    url: str | None\n    image_url: str | None = None\n    is_wholesale: bool\n','OfferOut schema')
once('backend/app/schemas.py','    url: str | None = Field(default=None, max_length=2000)\n','    url: str | None = Field(default=None, max_length=2000)\n    image_url: str | None = Field(default=None, max_length=2000)\n','Feed input schema')
once('backend/app/main.py','Base.metadata.create_all(bind=engine)\n','''Base.metadata.create_all(bind=engine)
# Additive migration for existing SQLite/PostgreSQL databases.
from sqlalchemy import inspect
if "image_url" not in {c["name"] for c in inspect(engine).get_columns("offers")}:
    with engine.begin() as conn:
        conn.exec_driver_sql("ALTER TABLE offers ADD COLUMN image_url TEXT")
''','Image URL database migration')
once('backend/app/main.py','url=row.url, is_wholesale=row.is_wholesale, min_order_quantity=row.min_order_quantity)','url=row.url, image_url=row.image_url, is_wholesale=row.is_wholesale, min_order_quantity=row.min_order_quantity)','Feed image import')
once('backend/app/discovery.py','            "url": _link(offer),\n','            "url": _link(offer),\n            "image_url": _text(offer, "picture", "image", "imagelink"),\n','YML image parser')
once('backend/app/discovery.py','            "shipping": _price(val("shipping")), "url": val("link"),\n','            "shipping": _price(val("shipping")), "url": val("link"),\n            "image_url": val("image"),\n','CSV image parser')

p=Path('app/src/main/java/com/smartbuy/ai/MainActivity.java'); s=p.read_text(encoding='utf-8')
if 'void addDiscoveryProductCard(' not in s:
    pos=s.index('    void remoteSearch(String q, String server){')
    methods=r'''    double offerTotal(JSONObject o){double p=o.optDouble("price",0);return o.has("total_price")?o.optDouble("total_price",p):p+(o.isNull("shipping")?0:o.optDouble("shipping",0));}
    String offerMoney(double n,String currency){return String.format(java.util.Locale.US,"%,.0f",n).replace(',',' ')+(currency.equalsIgnoreCase("RUB")?" ₽":" "+currency);}
    boolean safeOfferUrl(String value){try{Uri u=Uri.parse(value);return "https".equalsIgnoreCase(u.getScheme())&&u.getHost()!=null;}catch(Exception e){return false;}}
    void openOfferUrl(String value){if(safeOfferUrl(value))try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(value)));}catch(Exception ignored){Toast.makeText(this,"Не удалось открыть товар",Toast.LENGTH_SHORT).show();}}
    void loadFeedImage(String address,ImageView target,TextView placeholder){
        try{Uri u=Uri.parse(address);if(!"https".equalsIgnoreCase(u.getScheme())||u.getHost()==null)return;
            new Thread(()->{HttpURLConnection c=null;try{c=(HttpURLConnection)new URL(address).openConnection();c.setConnectTimeout(7000);c.setReadTimeout(10000);c.setInstanceFollowRedirects(true);c.setRequestProperty("User-Agent","SMART-BUY-AI/1.0");int code=c.getResponseCode();if(code<200||code>=300)return;InputStream in=c.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()>5*1024*1024)throw new Exception("image too large");out.write(b,0,n);}in.close();android.graphics.Bitmap bmp=BitmapFactory.decodeByteArray(out.toByteArray(),0,out.size());if(bmp!=null)runOnUiThread(()->{target.setImageBitmap(bmp);placeholder.setVisibility(View.GONE);});}catch(Exception ignored){}finally{if(c!=null)c.disconnect();}}).start();
        }catch(Exception ignored){}
    }
    void addDiscoveryProductCard(JSONObject product,JSONArray offers,String server){
        LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(13),dp(13),dp(13),dp(13));GradientDrawable bg=round(0xFF12152E,19);bg.setStroke(dp(1),0xFF39305F);card.setBackground(bg);LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-1,-2);cp.setMargins(0,dp(7),0,dp(7));content.addView(card,cp);
        LinearLayout top=new LinearLayout(this);top.setGravity(Gravity.CENTER_VERTICAL);FrameLayout photo=new FrameLayout(this);photo.setBackground(round(Color.WHITE,15));ImageView image=new ImageView(this);image.setScaleType(ImageView.ScaleType.CENTER_CROP);photo.addView(image,new FrameLayout.LayoutParams(-1,-1));TextView ph=txt("🛍️",30,0xFF4B426B,true);ph.setGravity(Gravity.CENTER);photo.addView(ph,new FrameLayout.LayoutParams(-1,-1));top.addView(photo,new LinearLayout.LayoutParams(dp(86),dp(86)));
        LinearLayout info=new LinearLayout(this);info.setOrientation(1);info.setPadding(dp(11),0,0,0);info.addView(txt(product.optString("title","Товар"),14,TEXT,true));String brand=product.optString("brand","");String model=product.optString("model","");String meta=brand+(brand.isEmpty()||model.isEmpty()?"":" • ")+model;if(!meta.isEmpty())info.addView(txt(meta,10,MUTED,false));if(!product.optString("category","").isEmpty())info.addView(txt(product.optString("category"),10,MUTED,false));top.addView(info,new LinearLayout.LayoutParams(0,-2,1));card.addView(top);
        JSONObject firstImage=null; if(offers!=null)for(int i=0;i<offers.length();i++){JSONObject o=offers.optJSONObject(i);if(o!=null&&!o.optString("image_url","").isEmpty()){firstImage=o;break;}}if(firstImage!=null)loadFeedImage(firstImage.optString("image_url"),image,ph);
        ArrayList<JSONObject> sorted=new ArrayList<>();if(offers!=null)for(int i=0;i<offers.length();i++){JSONObject o=offers.optJSONObject(i);if(o!=null)sorted.add(o);}Collections.sort(sorted,(a,b)->Double.compare(offerTotal(a),offerTotal(b)));
        // Keep one best offer per distinct store. A comparison is shown only if at least two stores exist.
        LinkedHashMap<String,JSONObject> stores=new LinkedHashMap<>();for(JSONObject o:sorted){String shop=o.optString("source","Магазин");if(!stores.containsKey(shop))stores.put(shop,o);}ArrayList<JSONObject> distinct=new ArrayList<>(stores.values());
        if(distinct.isEmpty())card.addView(note("Цена пока не поступила","Товар найден, но источник не передал цену."));
        else if(distinct.size()==1){JSONObject o=distinct.get(0);LinearLayout price=new LinearLayout(this);price.setGravity(Gravity.CENTER_VERTICAL);price.setPadding(dp(12),dp(11),dp(12),dp(11));price.setBackground(round(0xFF1B1C42,14));LinearLayout labels=new LinearLayout(this);labels.setOrientation(1);labels.addView(txt(o.optString("source","Магазин"),12,MUTED,true));labels.addView(txt(offerMoney(offerTotal(o),o.optString("currency","RUB")),20,TEXT,true));price.addView(labels,new LinearLayout.LayoutParams(0,-2,1));card.addView(price);String link=o.optString("url","");if(safeOfferUrl(link)){TextView buy=action("Открыть товар  →",PURPLE);card.addView(buy);buy.setOnClickListener(v->openOfferUrl(link));}}
        else{card.addView(txt("Сравнение цен • "+distinct.size()+" магазинов",11,MUTED,true));for(int i=0;i<distinct.size();i++){JSONObject o=distinct.get(i);LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(10),dp(9),dp(10),dp(9));row.setBackground(round(0xFF1B1C42,12));LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,-2);rp.setMargins(0,dp(3),0,dp(3));card.addView(row,rp);row.addView(txt(o.optString("source","Магазин"),11,TEXT,true),new LinearLayout.LayoutParams(0,-2,1));row.addView(txt(offerMoney(offerTotal(o),o.optString("currency","RUB")),14,i==0?GREEN:TEXT,true));String link=o.optString("url","");if(safeOfferUrl(link))row.setOnClickListener(v->openOfferUrl(link));}JSONObject best=distinct.get(0);card.addView(note("✓ Лучшая цена",offerMoney(offerTotal(best),best.optString("currency","RUB"))+" • "+best.optString("source","Магазин")));}
        TextView details=action("Открыть карточку товара  →",PANEL2);card.addView(details);int id=product.optInt("id",-1);if(id>0)details.setOnClickListener(v->remoteProductDetail(id,server));
    }

'''
    s=s[:pos]+methods+s[pos:]
old='''                        TextView productTitle=action("Открыть карточку  ·  "+title,PANEL2); content.addView(productTitle);
                        int remoteProductId=product==null?-1:product.optInt("id",-1);
                        if(remoteProductId>0) productTitle.setOnClickListener(v->remoteProductDetail(remoteProductId,server));
                        if(offers==null||offers.length()==0){content.addView(note("Нет предложений","Товар найден, но цена из фида не поступила."));continue;}
                        for(int j=0;j<offers.length();j++){JSONObject offer=offers.optJSONObject(j); if(offer==null)continue;
                            String shop=offer.optString("source", "Магазин"); String seller=offer.optString("seller","");
                            double price=offer.optDouble("price",0); double shipping=offer.isNull("shipping")?0:offer.optDouble("shipping",0);
                            double total=offer.has("total_price")?offer.optDouble("total_price",price+shipping):price+shipping;
                            String currency=offer.optString("currency","RUB"); String link=offer.optString("url","");
                            long age=offer.optLong("age_seconds",-1); String freshness=age<0?"Дата обновления неизвестна":age<3600?"Обновлено менее часа назад":age<86400?"Обновлено сегодня":"Устаревшее предложение — проверь цену";
                            String wholesale=offer.optBoolean("is_wholesale",false)?" • ОПТ":"";
                            content.addView(note(shop+wholesale+" • "+String.format(java.util.Locale.US,"%.0f %s",total,currency), "Цена: "+price+" "+currency+" • доставка: "+shipping+" • "+seller+"\\n"+freshness+"\\n"+link));
                        }
'''
new='''                        if(product!=null)addDiscoveryProductCard(product,offers,server);
'''
if old not in s: raise SystemExit('Android search results renderer anchor missing')
s=s.replace(old,new,1)
old2='''                    content.addView(txt(productInfo.optString("title","Товар"),20,TEXT,true));
                    String specs="Бренд: "+productInfo.optString("brand","—")+" • Модель: "+productInfo.optString("model","—")+" • Штрихкод: "+productInfo.optString("gtin","—");
'''
new2='''                    content.addView(txt(productInfo.optString("title","Товар"),20,TEXT,true));
                    if(offers.length()>0){JSONObject first=offers.optJSONObject(0);if(first!=null&&!first.optString("image_url","").isEmpty()){FrameLayout frame=new FrameLayout(this);ImageView photo=new ImageView(this);photo.setAdjustViewBounds(true);photo.setScaleType(ImageView.ScaleType.FIT_CENTER);frame.addView(photo,new FrameLayout.LayoutParams(-1,dp(210)));TextView ph=txt("🛍️",34,MUTED,true);ph.setGravity(Gravity.CENTER);frame.addView(ph,new FrameLayout.LayoutParams(-1,dp(210)));content.addView(frame);loadFeedImage(first.optString("image_url"),photo,ph);}}
                    String specs="Бренд: "+productInfo.optString("brand","—")+" • Модель: "+productInfo.optString("model","—")+" • Штрихкод: "+productInfo.optString("gtin","—");
'''
if old2 not in s: raise SystemExit('Product detail image anchor missing')
s=s.replace(old2,new2,1)
old3='''                    if(offers.length()>0){content.addView(section("Предложения"));for(int i=0;i<offers.length();i++){JSONObject o=offers.optJSONObject(i);if(o!=null)content.addView(note(o.optString("source"),o.optString("price")+" "+o.optString("currency")+" • доставка "+o.optString("shipping")));}}
'''
new3='''                    if(offers.length()>0){content.addView(section(offers.length()>1?"Сравнение предложений":"Предложение магазина"));ArrayList<JSONObject> rows=new ArrayList<>();for(int i=0;i<offers.length();i++){JSONObject o=offers.optJSONObject(i);if(o!=null)rows.add(o);}Collections.sort(rows,(a,b)->Double.compare(offerTotal(a),offerTotal(b)));for(int i=0;i<rows.size();i++){JSONObject o=rows.get(i);TextView line=action(o.optString("source","Магазин")+" • "+offerMoney(offerTotal(o),o.optString("currency","RUB"))+(i==0&&rows.size()>1?"  ✓":""),i==0?PURPLE:PANEL2);content.addView(line);String link=o.optString("url","");if(safeOfferUrl(link))line.setOnClickListener(v->openOfferUrl(link));}}
'''
if old3 not in s: raise SystemExit('Product detail offers anchor missing')
s=s.replace(old3,new3,1)
p.write_text(s,encoding='utf-8')

g=Path('app/build.gradle');s=g.read_text(encoding='utf-8');s=re.sub(r'versionCode\s+\d+', 'versionCode 24', s, count=1);s=re.sub(r"versionName\s+'[^']+'", "versionName '0.6.4'", s, count=1);g.write_text(s,encoding='utf-8')
print('SMART BUY AI 0.6.4: product photos persisted from YML/CSV feeds; single-store single price; multi-store price comparison; full product card for every category.')
