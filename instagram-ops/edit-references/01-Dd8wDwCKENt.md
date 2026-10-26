# 01: Dd8wDwCKENt

- **Link:** https://www.instagram.com/reel/Dd8wDwCKENt/
- **Müddət:** ~50 san.
- **Növ:** reklam tərzli ekspert danışığı (talking head + qrafika)
- **Mənbə:** vidIQ AI təhlili (26.10.2026). Rəng kodları və saniyələr təxminidir. Fayl əldə olunanda kadrlardan dəqiqləşdirilməlidir.

## Kadr-kadr

| Vaxt | Kadr | Kəsik/keçid | Mətn və qrafika | Səs |
|---|---|---|---|---|
| 0:00–0:02 | Siluet, işıq yanır | işıqla açılış | yoxdur | klik |
| 0:02–0:03 | Orta plan | sərt kəsik | "SATIŞ", sarı çərçivəli | whoosh |
| 0:03–0:05 | 3D kart | glitch/zoom | qırmızı 3D: "Önəmi yoxdur / VİDEO KEYFİYYƏTİ" | bas zərbəsi, glitch |
| 0:05–0:08 | Orta plan | sərt kəsik | söz-söz subtitr + animasiyalı qutu | pop |
| 0:08–0:11 | Punch-in | jump cut | arxada böyük tipografiya | whoosh |
| 0:11–0:14 | B-kamera, tünd isti | neon çərçivə içində | serif subtitr | keçid tonu |
| 0:16–0:20 | Punch-in | sərt kəsik | sarı ulduz: "video keyfiyyətli çıxmalıdır" + 3D kamera | pop |
| 0:20–0:22 | Orta plan + kolaj | pop-in | 3 panelli video kolaj (yuxarı sağ) | UI pop |
| 0:23–0:25 | Geniş plan | jump cut | böyük sarı: "CANAYAXIN DANIŞMA" | bas zərbəsi |
| 0:25–0:28 | B-kamera, kəhrəba | yan bucaq | başın ətrafında neon yazı: "sizcə mən belə danışıram?" | boğuq səs, sintez |
| 0:28–0:32 | Orta plan | sürətli zoom | sürətli subtitr | whoosh |
| 0:33–0:38 | Punch-in | sərt kəsik | 2 sarı etiket: "NƏ DEYİRSƏN" / "NECƏ CƏLB EDİRSƏN" | ikiqat pop |
| 0:38–0:40 | 3D kart | glitch | qırmızı 3D: "AMMA VİDEOYA" | sub-bas, tape stop |
| 0:41–0:50 | Orta plan (CTA) | yavaş push-in | yalnız subtitr | yüngül bit, təmiz səs |

## Resept

```yaml
temp:
  orta_kadr_muddeti_san: 1.8-2.5
  kesikler: [jump cut, punch-in 100->115%, B-kamera, 3D kart]
  hook: 0.8 san-də siluetdən işığa keçid + 0:03-də tam ekran 3D kart
reng:
  arxa_fon_soyuq: "#1C3D47"   # firuzəyi arxa işıq
  uz_isigi_isti: "#F5E1C8"
  vurgu_1: "#FFD200"          # sarı: açar sözlər, etiketlər, ulduz
  vurgu_2: "#C81D25"          # qırmızı: 3D başlıq kartları
  qaranliq_fon: "#0A0A0A"
  grade: isti üz / soyuq fon split, yüksək kontrast, təbii dəri; B-kamera tünd kəhrəba
tipografiya:
  subtitr: ağ, qalın sans-serif (Montserrat tipli), mərkəzdə, açar söz sarı
  zərbə_başlıqları: qalın, sıxılmış qrotesk
  ironik_anlar: neon skript
qrafika:
  - 3D həcmli kartlar (köhnə TV/lövhə forması, qara fon)
  - komiks ulduz nişanları
  - əllərə bağlı sarı etiket (pill) kartları
  - video kolaj inset
ses:
  sfx: hər vizual hadisəyə bir səs (whoosh, pop, bas, klik, tape stop)
  musiqi: alçaq lo-fi/hip-hop, vacib cümlələrdə səviyyəsi enir
final: qrafikasız, yavaş push-in, təmiz səs
```

## Montajda yox, çəkilişdə lazım olanlar

- Siluetdən işığa keçid (işıq idarəsi)
- İkinci kamera bucağı, tünd/kəhrəba ayrıca kadr
- Arxa fonda tipografiyalı divar
