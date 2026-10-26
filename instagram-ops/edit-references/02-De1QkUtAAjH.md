# 02: De1QkUtAAjH

- **Link:** https://www.instagram.com/p/De1QkUtAAjH/
- **Müddət:** ~29 san.
- **Növ:** ekspert izahı, problem → həll, tünd UI motion-qrafika üstünlük təşkil edir
- **Mənbə:** vidIQ AI təhlili (26.10.2026). Rəng kodları və saniyələr təxminidir.

## Kadr-kadr

| Vaxt | Kadr | Keçid | Mətn və qrafika | Səs |
|---|---|---|---|---|
| 0:00–0:02 | Split-screen: yuxarıda UI kartları, aşağıda spiker | birbaşa başlanğıc | 3 kart ardıcıl: "Reklama pul ● gedir" (sarı), "Müştəri ● gəlir" (yaşıl), "Satış 0" (qırmızı) | hər kartda UI pop |
| 0:03–0:04 | Tam ekran spiker | sərt kəsik, ~10% punch-in | alt subtitr qutusu | |
| 0:05–0:09 | 2.5D əyilmiş UI kartı, yavaş push-in | whip zoom / blur | etiket "SATIŞ SÖHBƏTİ", başlıq "Satış harada **qırıldı?**", çat mesajları bir-bir gəlir | mesaj pop, whoosh |
| 0:10–0:15 | UI panel (dashboard) | yuxarı slayd / dissolve | "Mesajları və zəngləri izləyir", nəbz vuran sarı kürə, sayğaclar 133→140, siyahı: yaşıl "Satış oldu", qırmızı "Geri dönüş yox" | bildiriş tonları, sayğac tıqqıltısı |
| 0:16–0:18 | 3D telefon maketi | sərt kəsik | etiket "SAHİBKAR GÖRÜR", "Problem **buradadır**", kilid ekranında bildiriş | bildiriş zəngi |
| 0:19–0:21 | Müqayisə kartları | sürətli itələmə | etiket "QƏRAR", səhv yanaşma (qırmızı) / düzgün yanaşma | snap/pop |
| 0:22–0:28 | Spiker + yuxarıda CTA kartı | sərt kəsik, 0:25-də punch-in | etiket "PAYLAŞIN", "Bezmiş sahibkara **göndərin.**" | yumşaq whoosh |

## Resept

```yaml
temp:
  orta_kadr_muddeti_san: 2.0-3.5
  nisbet: 35% spiker / 65% motion-qrafika
  hook: ilk 2.5 san split-screen (üz + animasiyalı kartlar)
reng:
  fon: "#0E1217"            # tünd boşluq
  fon_2: "#161B22"
  kart: "#1E242C"           # 1px kənar "#2A323D", yüngül kölgə
  vurgu: "#FFD000"          # sarı: açar söz, AI kürəsi
  ugur: "#10B981"           # yaşıl status
  xeta: "#EF4444"           # qırmızı status
  metn: "#FFFFFF"
  ikinci_metn: "#9CA3AF"
  grade: neytral/soyuq, təbii dəri
tipografiya:
  font: Inter / Gilroy / SF Pro tipli sans-serif
  basliqlar: bold, mərkəzdə, açar söz sarı
  etiketlər: BÖYÜK HƏRF, extra-bold, geniş aralıq, şəffaf yumru "pill" içində
  subtitr: ağ bold, 1-3 söz, tünd yarımşəffaf yumru qutu (#000000CC), alt üçdə bir
qrafika:
  forma: böyük künc radiusu (16-24px), tünd glass, yüngül parıltı
  giris: scale + Y slayd, spring/ease-out ~0.25 san
  mikro: sayğaclar, status dəyişməsi, nəbz vuran parıltı
  maketlər: çat UI, dashboard, 3D telefon, müqayisə kartları
  struktur: hər qrafika səhnəsində [ETİKET] + başlıq + vizual
ses:
  sfx: hər kartda UI pop, tam ekran keçiddə alçaq whoosh, rəqəmlərdə tıqqıltı
  musiqi: çox alçaq lo-fi/tech bit
final: spiker + daimi CTA kartı (paylaşmağa çağırış)
```

## Qeyd

Hamısı montajda (Remotion) yaradıla bilər, xüsusi çəkiliş tələb etmir. Ən çox vaxt aparan hissə kart dizaynıdır; bir dəfə şablon kimi qurulandan sonra hər videoda yalnız mətn və rəqəmlər dəyişir.
