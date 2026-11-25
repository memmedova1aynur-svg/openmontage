# Montaj qaydaları — TƏK MƏNBƏ (hər videoda məcburi)

Drive linki + montaj sorğusu gələndə **yalnız bu fayl** oxunur. Başqa qayda faylına baxmaq lazım deyil
(`IS_AXINI.md`, `KINO_DILI.md`, profillərdəki köhnə "ümumi qaydalar" — ziddiyyət olarsa bu fayl keçərlidir).
Müştəri profilindən (`templates/expert-reels/experts/<ad>.json`) yalnız **müştəriyə aid** olanlar götürülür: rəng ailəsi
(`palette`, `theme`), şrift, musiqi janrı, animasiya/B-roll qadağaları, ad/titul, lüğət (`glossary`). Qalanı nəzərə alınmır.

## 1. İş axını (bir keçid, əlavə kod və yeni render yoxdur)
1. Qısa sorğu — yalnız məlum olmayanı soruş (müştəri adı, məqsəd). Sonra linki istə. Qovluqda bir neçə video varsa — **ardıcıl**, hər biri ayrı.
2. `python -m montaj.session new --title "<ad>" --link "<link>" --client "<Ad Soyad (profil adı)>" --type <N>`
3. `storyboard <pid> --quick` → `framefix <pid>` → `voice-clean <pid>` → transkripti oxu (`retakes <pid>` köməkçidir).
4. `music <pid>` → plan yaz (bölmə 3–7) → `choose <pid> <plan.json>` → `render <pid>` → `verify <pid>`.
5. Yekun `_ig.mp4`-ü göndər + 2–4 sətir (nə edildi, ASR şübhəli sözlər siyahısı, yoxlanmayan nə qaldı).
6. İstifadəçi təsdiq edəndən sonra: `choose <pid> --remember` (profilin `history`-sinə yazır).

**Qadağa:** 3 variant, `variants`, storyboard şəkli, rəng variantları, ara yoxlama mesajları, təkrar render, yeni kod/funksiya
yazmaq — istifadəçi açıq istəməyibsə. Səhvlər `render` daxilindəki preflight-da tutulur; tam render **bir dəfə**.
`verify` yalnız yekun faylda, **bir dəfə**. `!` varsa yalnız həmin elementi düzəldib yenidən render et.

## 2. Hər videoda məcburi
| # | Qayda |
|---|---|
| 1 | **Kadraj:** `framefix` — əyrilik düzəlir, obyekt ortalanır, baş üstü və yan boşluq ayarlanır; yaxınlaşma ≤1.12x (daha çox lazımdırsa bunu yaz). |
| 2 | **Kəsim:** yalnız təkrar, alınmayan cəhd və kənar söhbət çıxır. Söz və heca kəsilmir. Vurğu yaradan və ya fikri anlamağa vaxt verən pauza **saxlanır**; saniyə həddi ilə mexaniki kəsim YOXDUR. |
| 3 | **Hook:** ilk saniyələr `skills/creative/hook-design.md` ilə seçilir (üsul + səbəb 1 cümlə). Sıra dəyişmir; səssiz baxışda başa düşülməlidir. |
| 4 | **Altyazı:** `skills/creative/caption-typography.md` — rollar ayrı (altyazı, hook, vurğu, CTA); Azərbaycan hərfləri düzgün; ən çox 2 sətir; safe zone; mətn bloku enin ≤86%-i; üzü örtmür. ASR səhvləri düzəlir (`corrections`), mənanı dəyişən təxmin YOX — şübhəlini istifadəçiyə siyahıla. |
| 5 | **Kart/B-roll:** `skills/creative/broll-function.md` — hər elementin funksiyası və izah etdiyi fikir var; yoxdursa qoyulmur. 56 s-də 0–4 element normaldır. Profil qadağan edirsə (animasiya, araya kadr) qoyulmur. |
| 6 | **Musiqi:** standart VAR (yalnız istifadəçi bu müştəri/video üçün "yox" deyibsə istisna). Yalnız CC0 və Mixkit. Planda `volume`/`vol` YAZMA — `"auto"` (danışığa görə hesablanır). |
| 7 | **SFX:** yalnız vizual elementə bağlı; element silinirsə SFX də silinir; planda `vol` yazma. |
| 8 | **Rəng:** `look: auto`. Şablon, müştəriyə bağlı sabit filtr, saturation artımı, üz/dəri emalı YOX. Brend rəngi yalnız altyazı və qrafikaya aiddir. |
| 9 | **Çıxış:** Instagram üçün 1080x1920 (4K/ağır fayl göndərilmir), H.264, −14 LUFS, pik ≤−1.5 dBTP. HDR mənbə SDR-ə çevrilir (render özü edir). |
| 10 | **Uydurma yoxdur:** qiymət, tarix, əlaqə, rəqəm, çağırış, titul yalnız danışıqdan/profildən/istifadəçidən. Real olmayan məkan həqiqi kimi göstərilmir. |
| 11 | **Davamlılıq + müxtəliflik:** müştərinin rəng ailəsi sabit; hook, altyazı üslubu və kart ardıcıllığı son 3 videodan (`history`) fərqli (`variation`). |
| 12 | **Təhvil:** `verify` təmiz və ya qalan `!` açıq yazılıb; qulaqla dinlənilməyibsə bunu de. "Sıfır keyfiyyət itkisi" zəmanəti vermə. |

## 3. Plan faylı (şablon — hər video üçün mətnləri danışıqdan yaz)
```json
{
  "approach": "M01+M02",
  "title": "<qısa ad>",
  "variation": {"tone": "...", "primary": "#...", "primaryDeep": "#...", "captions": "box", "anim": "pop"},
  "corrections": [{"from": "<ASR səhvi>", "to": "<düzgün>"}],
  "captions": {"enabled": true},
  "graphics": [
    {"type": "title", "text": "<hook sualı>", "start": 0.15, "dur": 4.5, "y": 0.19},
    {"type": "emphasis", "text": "<əsas fikir>", "start": 28.4, "dur": 2.8, "y": 0.60}
  ],
  "sfx": [{"kind": "pop", "t": 0.2}],
  "music": [{"start": 0.0, "volume": "auto", "fadeIn": 1.2, "fadeOut": 2.0, "duck": true, "file": "<music çıxışındakı fayl>"}],
  "look": "auto"
}
```
`variation` dəyərlərini `storyboard` çıxışındakı təklifdən götür. `music` faylı `music <pid>` çıxışındadır. Qrafika `y`-ləri preflight-da
interfeys zonasına görə avtomatik düzəlir.

## 4. Mətnlər və yazı (Azərbaycan dili)
`ə ğ ı İ ö ü ş ç` şriftdə olmalıdır; böyük hərf `i→İ`, `ı→I` (`lib/az_text`). Rəqəmlər `1 200`, `4,5`.
ASR tanıdığı kirill/oxşar `ә` simvolu `ə`-yə normallaşdırılır.

## 5. Sürət (məqsəd, ölçülməyib)
Qısa videoda hədəf ümumi 4–5 dəq. Ən böyük xərc: tam render (≈2–3 dəq, HDR mənbədə) və ilk transkripsiya (≈1 dəq). Bunları
azaltmağın yolu — **təkrar render etməmək**; transkript və analiz keşdən istifadə olunur. Hədəfə çatılmayıbsa ən uzun addımı yaz.
