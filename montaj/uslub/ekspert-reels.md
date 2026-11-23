# Üslub kitabçası — Ekspert Reels

> Status: **QARALAMA — təsdiq gözləyir.** `⚠` — mənim təklifim, ölçü sizin təsdiqinizi gözləyir.
> Burada yazılmayan effekt, keçid, animasiya **işlədilmir**. Ümumi qaydalar: `montaj/QAYDALAR.md` §4.

## 1. Format

| Parametr | Dəyər |
|---|---|
| Ölçü | 1080×1920 (9:16) |
| Kodek | H.264, yaxşı keyfiyyət (CRF 18) |
| fps | mənbənin fps-i (dəyişkən fps sabitə çevrilir) |
| Səs | −14 LUFS, pik ≤ −1 dBTP |
| Müddət | danışığa görə; ⚠ hədəf 30–75 s, 90 s-dən uzun olanda planda qeyd |

## 2. Kəsim

- Pauzalar ≥0.45 s kəsilir; kəsim nöqtəsi səsin ən sakit yerinə düşür; söz kəsilmir.
- Təkrar cəhd → sonuncu tam cəhd qalır.
- Yarımçıq fikir, "bir dəqiqə", "yenidən deyim", kameradan kənar danışıq → çıxarılır.
- Cümlələrin sırası dəyişmir.
- Şübhəli kəsim (Claude əmin deyil) → material **saxlanılır** və planda "şübhəli" yazılır.

## 3. Kadraj və keçid

- Oturaq danışıq: kadr oturma xəttindən yuxarı (ayaqlar görünmür). Baş kəsilmir.
- ⚠ Gözlər kadrın yuxarıdan ~1/3 hissəsində.
- Danışıqdakı kəsimlərdə **dissolve/ərimə yoxdur**. Keçid = plan dəyişməsi:
  seqmentlər növbə ilə **1.0 ↔ 1.1** miqyas, üzə görə kadraj.
- ⚠ Eyni miqyas ard-arda iki seqmentdə olmur (jump cut-un qarşısı).
- Virtual "zoom-in/punch-in" yalnız vurğu anında, ⚠ videoda ən çox 2 dəfə.
- Kamera titrəməsi effekti, sürətli zoom, fırlanma — **yoxdur**.

## 4. Altyazı

- Üslub: müştəri profilindəki `style.captions` (məs. `marker`). Profildə yoxdursa — ⚠ sadə ağ, nazik kontur.
- Yer: normalda aşağı hissədə, üzün altında; B-roll bölünmüş ekranda olanda başın üstündə (y ≈ 0.17).
- Kadr dəyişəndə altyazı obyektin üstünə yox, boş sahəyə.
- Animasiya/kart ekranı örtəndə altyazı gizlənir.
- ASR səhvləri profildəki `glossary` ilə düzəldilir; xüsusi adlar, rəqəmlər, telefonlar **hər dəfə** transkriptlə yoxlanır.
- ⚠ Sətirdə ən çox 3–4 söz, ən çox 2 sətir.

## 5. Kartlar və animasiyalar

- Say: videoda **3–4**; hər biri **3–5 s**; danışılan sözə dəqiq (söz başlayanda giriş).
- ⚠ Animasiyalar arasında ən az **4 s** boş (yalnız danışan) ekran. *(Köhnə qaydada "aralarında 1 s boşluq olmasın"
  yazılıb — mənası aydın deyil, dəqiqləşdirin.)*
- İcazəli növlər: müştəri profilindəki `style.pops` kart üslubu; `title`, `emphasis`, `list`, `card`, `lower` (ad/titul).
- Mətn yalnız danışıqdan (qısaldıla bilər, mənası dəyişmir). ⚠ Kartda ən çox 6 söz.
- Kart üzü örtmür: üzün altında; yer yoxdursa kiçilir; sığmırsa başın üstündə.
- Rənglər yalnız müştərinin `theme`-indən.
- ⚠ Animasiya hərəkəti: giriş 0.3–0.4 s, çıxış 0.25 s, yumşaq (ease-out); sıçrama (bounce), fırlanma, parıltı yoxdur.

## 6. B-roll

- Mənbə: yalnız (a) müştərinin göndərdiyi material, (b) Claude-un hazır səhnələri (`scenes` kataloqu),
  (c) pulsuz stok (Mixkit, Pixabay, Wikimedia CC0/PD). Material yoxdursa B-roll **uydurulmur**.
- Yalnız danışılan şeyi **birbaşa** göstərəndə (məhsul, nümunə, proses). Ümumi "əhval" B-rollu yoxdur.
- Yerləşmə: bölünmüş ekran — danışan yuxarıda, B-roll sinədən aşağı (pip y ≈ 0.70, tam en).
- ⚠ Videoda ən çox 2–3 B-roll, hər biri 2–4 s; kart ilə eyni anda yox.
- Rəng şablonu (look C) B-roll-a da tətbiq olunur.

## 7. Səs effektləri (SFX)

Hər animasiya girişinə bir SFX, xarakterinə görə (hər yerdə eyni səs yox):

| Hadisə | SFX |
|---|---|
| Kağız/etiket kartı | `paperclick` |
| Giriş (kart, səhnə) | `whoosh2` / `swish` |
| Vurğu | `p_glint` |
| Siyahı elementi, sayma | `p_tap` / `knock` |
| Üstündən xətt | `scratch` |
| Başlıq | `p_bloom` |

- Səviyyə: nitqdən **−14…−22 dB** aşağı.
- Animasiyasız SFX yoxdur. Kəsimlərə (plan dəyişməsinə) SFX qoyulmur.

## 8. Musiqi

- Yalnız CC0 / lisenziyası yoxlanmış.
- Bütün video boyu, səviyyə 0.12, giriş 1.2 s, çıxış 2.0 s, danışıqda enir (ducking).
- Həmişə dinamik, yavaş musiqi yoxdur. Janr: müştəri profilindəki `house_style.music`, enerjisi videonun mövzusuna uyğun.
- ⚠ Musiqi danışıq zamanı nitqdən ən az 18 dB aşağı (yoxlanacaq).
- Musiqi seçimi üçün variant göndərilmir — sabit üslubdan götürülür (yeni müştəri istisna).

## 9. Rəng və görüntü

- Həmişə `look C`. Kliplər arası işıq bərabərləşdirilir.
- Arxa fon orijinal. Güzgü çevirmə yoxdur.
- HDR mənbə → SDR (avtomatik).

## 10. Açılış və sonluq

- Açılış: ilk kadr danışanın özüdür; ⚠ ilk 1 s-də ilk söz başlayır (əvvəlki səssizlik kəsilir).
- Sonluq kartı yalnız müştəri profilində varsa (telefon, çağırış) — mətn profildən, uydurulmur.
- Video cümlənin sonunda bitir, ⚠ son sözdən sonra 0.3–0.6 s nəfəs.

## 11. Yekun yoxlama siyahısı (Claude, göndərməzdən əvvəl)

- [ ] `verify` və `delivery_qc` — `fail` yoxdur
- [ ] kəsim yerlərində söz kəsilməyib, söz təkrarı yoxdur
- [ ] altyazıda xüsusi adlar, rəqəmlər, telefon düzgündür
- [ ] kart sayı 3–4, hər biri 3–5 s, üzü örtmür
- [ ] B-roll başı örtmür, kart ilə eyni anda deyil
- [ ] musiqi danışığı basmır, SFX yalnız animasiyalarda
- [ ] look C, fon orijinal, güzgü yoxdur
