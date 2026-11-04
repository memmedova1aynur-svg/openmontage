# Standart montaj üslubu — bütün müştərilər üçün (Premiere Pro səviyyəsi)

Bu fayl istifadəçinin təsdiqlədiyi, artıq "birbaşa Instagram-a" hazır nəticə verən montaj qaydalarıdır (Rəhimə Niyazlı
partiyasında oturuşub, 2026-11). Yeni müştəridə də **soruşmadan** tətbiq olunur. Müştəri profili (`experts/<ad>.json`)
xüsusi qayda verirsə (rəng ailəsi, musiqi, pauza), profil üstündür; ziddiyyət varsa qərar mesajında bir cümlə ilə de.

İş axını: `IS_AXINI.md`. Montaj dili: `KINO_DILI.md`. Bu fayl — **standart görünüş və səs**.

---

## Hazır başlanğıc promptu (yeni söhbət üçün)

> Bu söhbət müştəri videolarının montajı üçündür. Montaj sistemi repodadır və hazırdır — sistem kodunu dəyişmə, səhv
> görsən mənə qısa yaz. Əvvəl `git pull origin main`, sonra `AGENT_GUIDE.md`, `montaj/IS_AXINI.md`,
> `montaj/STANDART_USLUB.md`, `montaj/KINO_DILI.md`, `templates/expert-reels/VIDEO_TYPES.md` və müştərinin profilini oxu.
> Mühit: `export MONTAJ_DATA_DIR=$HOME/montaj-data MONTAJ_OUT_DIR=$HOME/montaj-data/out`; çatışmırsa `bash scripts/cloud-setup.sh`.
>
> Müştəri: **[ad]** (profil: **[profil]**). Material: **[Drive linkləri]**. Növü materialdan özün təyin et (`set-type`).
> STANDART_USLUB.md-dəki bütün qaydaları soruşmadan tətbiq et. Əvvəl bir nümunə (storyboard + rəng + kadraj əvvəl/sonra) —
> təsdiqdən sonra qalanları eyni üslubda, render-ləri tək-tək. Ödənişli xidmət qoşma; müştəri mediasını repoya commit etmə;
> uzun hesabat yazma. Hər videoya Instagram caption-ı yaz.

---

## 1. Görüntü

| Mövzu | Standart | Sistemdə |
|---|---|---|
| **Güzgü** | Avtomatik "hamısını çevir" YOX. Hər videoda kadrdakı yazıya (lövhə, loqo, köynək yazısı) bax: tərsdirsə çevir, düzdürsə toxunma. Auditoriya/B-roll kadrları adətən düzdür. Qərarı bir cümlə ilə de. | klipin `adjust.mirror` |
| **Rəng** | Təmiz, işıqlı, təbii dəri. Normal işıqda **C**. Sarı/isti otaq işığında (kafe, lampa) **N** — sarılıq götürülür, ağ köynək ağ olur, işıqlandırılır, yüngül kəskinlik. Doyğunluq artırılmır (sarılığı gücləndirir). Qaranlıq və dənəvər qalmasın — lazım olsa **D**. | `looks` → planda `"look": "C" \| "N" \| "D"` |
| **Kadraj** | `framefix` HƏR videoda: əyrilik düzəlir, danışan mərkəzdə, başın üstündə təbii boşluq, baş kəsilmir. | `framefix` |
| **Sərt kəsim (jump cut)** | Kəsimdən sonra plan ölçüsü yüngül dəyişir (növbə ilə 7% yaxınlaşma) — kəsim "sıçrayış" kimi görünmür. | planda `"jumpcut": {"zoom": 0.93}` |
| **Kadr sərhədi** | Kəsimlər kadr şəbəkəsinə uyğunlaşır — donmuş/təkrar kadr yoxdur. | avtomatik (`plan`) |
| **Fon** | Bulanıqlaşdırılmır, qaraldılmır — orijinal qalır (yalnız müştəri açıq istəyəndə `bg`). | — |

## 2. Danışıq və kəsim

- **Boş saniyələr** (danışılmayan pauza ≥0.45 s) kəsilir, hər pauzada nəfəs payı qalır, söz kəsilmir:
  `tighten <pid>` (mənalı pauza üçün `--keep <saniyə>`). Sonra `retakes` — təkrar cəhdlər çıxır, tam cəhd qalır.
- Kəsimdən sonra **söz təkrarı olmadığını** yoxla (`verify`, `words`). Sakit sərhəd tapılmayanda `cut` artıq keçir
  və materialı saxlayır (söz təkrarı yaranmır).
- Fikrin ardıcıllığı dəyişmir; reklamda mətn sırası qorunur, hook əvvələ çəkilmir.

## 3. Səs

- `voice-clean` (fon uğultusu, kafe, yağış) → planda `"voicePolish": true`: boğuqluq azalır, sözlər açılır, "s/ş" yumşalır,
  səviyyə bərabərləşir; yekun −14 LUFS (render özü). Studiya mikrofonu səsi yaranmır — təmizlik və aydınlıq.
- **Musiqi** — çox aşağı, fonda hiss olunur: danışıq videosu ~0.03–0.06, reklam ~0.03; danışıqda avtomatik azalır.
  Yalnız CC0 / qeydsiz kommersiya lisenziyası (`music`). Piano/kədərli yox. Müştəri "musiqi yoxdur" desə — planda `music` yox.

## 4. Altyazı və yazılar

- **Altyazı**: sadə, oxunaqlı — Montserrat, ağ, nazik tünd kontur, fonsuz (və ya müştəri ailəsində yumşaq qutu).
  ASR səhvləri düzəldilir (`fix-word --remember` — müştəri lüğətinə).
- **Kartlar/başlıqlar** sözün **deyildiyi anda** çıxır (boş gözləyən kart yox), ekranın ən yuxarısında (y≈0.10) və ya
  sinədən aşağıda — **baş, üz, alın üstünə düşmür** (`verify` yoxlayır).
- Mətnlər yalnız danışıqdan; qiymət, tarix, rəqəm, nəticə, çağırış uydurulmur.

## 5. B-roll

- **Danışıq videosu**: mövzuya uyğun B-roll (müştərinin öz kadrı → hazır animasiya `scenes` → pulsuz stok `stock`).
  **Bölünmüş ekran**: danışan yuxarıda, B-roll aşağıda (sinədən aşağı, başı örtmür; pip `y≈0.70`, və ya aşağı yarı).
  O anda altyazı başın üstünə qalxır: planda `"captionsAboveBroll": true`.
- **Reklam**: daha dinamik — hərəkətli qrafika (təklif, siyahı, CTA), B-roll azdır və ya yoxdur; sonda çağırış (müştərinin verdiyi nömrə/açar söz).
- **Seminar/uzun çıxış**: `highlights` → ən güclü 40–60 s hissələr (`extract`). Ara kadr yalnız **dinləyən** iştirakçılar —
  çay içən, yemək yeyən, söhbət edən, uşaqlı kadrlar yox. Danışan kadrdan çıxanda o an ara kadrla örtülür.
- Stok görüntü real nəticənin sübutu kimi təqdim edilmir.

## 6. Davamlılıq və müxtəliflik

- Rəng ailəsi (müştəri brendi) bütün videolarda eyni; giriş, altyazı üslubu (qutu/kontur), kart düzülüşü, effekt sırası
  video-video dəyişir (`variation`). Eyni partiyada iki video bir-birinin kopyası olmur.

## 7. Foto və karusel (fotolardan)

- Fotoda ağ balans insanların olduğu hissəyə görə (ağ köynək ağ), işıqlandırma, yüngül kəskinlik və ya Real-ESRGAN
  (nəticə orijinalla ~60–70% qarışdırılır — plastik görünməsin).
- Kəsim üzə görə: başın üstündə boşluq, baş/alın kəsilmir. Gözü yumulu, ağzı açıq, yana baxan, eybəcər düşmüş kadr seçilmir.
- Karusellər: hər birinin quruluşu fərqli (tam foto, foto+panel, polaroid, kartlar), brend rəngi sabit; 6 slayd.

## 8. Təhvil

- `render` → `verify` (qara/donmuş kadr, səs piki, oxunma müddəti, üz örtülməsi, Reels zonaları) → `words`.
- Telefona `_ig.mp4`; hər videoya **Instagram caption** (hook sətri, 2–4 qısa abzas, bir çağırış, 3 hashtag).
- Təhvildən sonra yer azdırsa xam/montaj faylları silinir, karusellər və plan/caption faylları saxlanılır.

## Plan nümunəsi (danışıq, bölünmüş ekran B-roll)

```json
{
 "approach": "M01+M02", "look": "C", "jumpcut": {"zoom": 0.93}, "voicePolish": true,
 "captionsAboveBroll": true,
 "captions": {"enabled": true, "style": {"font": "Montserrat", "weight": 700, "color": "#FFFFFF", "stroke": "#2B1A12", "bg": "none"}},
 "graphics": [{"type": "title", "text": "...", "start": 0.2, "dur": 3.4, "y": 0.10}],
 "broll": [{"name": "<fayl>", "mode": "pip", "at": 12.0, "dur": 3.5, "scale": 0.7, "x": 0.5, "y": 0.72}],
 "music": {"file": "<CC0 fayl>", "volume": 0.04}
}
```

Ardıcıllıq: `new` → `storyboard` → `set-type` → `framefix` → `tighten` → `retakes`/`cut` → `voice-clean` → `looks` →
`variants` (3 plan) → qərar mesajı → `choose` → `render` → `verify` → `words` → caption.
