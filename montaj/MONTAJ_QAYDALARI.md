# Montaj qaydaları — TƏK MƏNBƏ (hər videoda məcburi)

Drive linki + montaj sorğusu gələndə **yalnız bu fayl** oxunur. Başqa qayda faylına baxmaq lazım deyil (köhnə qayda faylları silinib). `IS_AXINI.md` yalnız
**əmr istinadıdır** (fx, bg, karusel, seminar, kurs, tədbir və s. necə işlədilir); ziddiyyətdə bu fayl keçərlidir.
Müştəri profilindən (`templates/expert-reels/experts/<ad>.json`) yalnız **müştəriyə aid** olanlar götürülür: rəng ailəsi, şrift,
ad/titul, lüğət və müştərinin öz məhdudiyyətləri (məs. animasiya/araya kadr yoxdur — onlar qorunur). Ümumi qayda profilə yazılmır.

## 1. İş axını
1. Link gələndə ilkin sorğu yoxdur. Yalnız müştəri adı bilinmirsə onu soruş. Qovluqda bir neçə video varsa — **ardıcıl**, hər biri ayrı.
2. `new --title "<ad>" --link "<link>" --client "<Profil adı>" --type <N>` → `storyboard <pid> --quick` → `framefix` → `voice-clean`
   → transkripti oxu (`retakes` köməkçidir) → `music`.
3. **Hər video üçün 3 storyboard variantı (məcburi; mövzu imkan verirsə 5-ə qədər).** Variantlar bir-birindən tamamilə fərqli montaj üslubu olmalıdır
   (montaj növü, animasiya ilə cümləyə bağlı və ya birbaşa kadr dəyişmə, hook üsulu, ritm, tipoqrafiya, musiqi) — yalnız rəng/mətn fərqi yox.
   Variantı ən keyfiyyətli, ən maraqlı və izləyicini sona qədər saxlayan formada qur — **render vaxtına görə sadələşdirmə**. Hər variantın yanında:
   **təxmini montaj müddəti** və bu video üçün **niyə** seçilib (reklamda — hansı daha çox geri dönüş gətirər). Qərar istifadəçinindir.
   `variants <pid> A.json B.json C.json` → `storyboard_variantlari.jpg` (360p proksidən, saniyələr; video önizləmə üçün `--mp4`).
   **Hər təklif həm yazılı, həm şəkilli göndərilir** (heç vaxt yalnız mətn). `fx` (arxada yazı, sticker və s.) olan variantda onun şəkli ayrıca: `fx <pid> --preview --spec '{...}'` → `effektler.jpg` (~7 s); `variants` önizləməsi `fx`-i göstərmir.
   Göndər: storyboard şəkli + variant izahları + 2–3 musiqi nümunəsi + `kadraj.jpg` + material qeydləri. İstifadəçi ilə birlikdə seçilir.
4. Seçimdən sonra: `choose <pid> <plan.json>` → `render <pid>` (preflight daxildir) → `verify <pid>` → yekun `_ig.mp4` + 2–4 sətir.
5. İstifadəçi təsdiq edəndən sonra: `choose <pid> --remember` (profilin `history`-sinə yazır; təsdiqsiz heç nə yazılmır).
6. **Tam render bir dəfə.** Səhvlər renderdən əvvəl (variants, preflight) tutulur. `verify` yalnız yekun faylda, bir dəfə.

## 2. Hər videoda məcburi
**Kadr.** `framefix`: əyrilik düzəlir, obyekt ortalanır, baş üstü, aşağı və yan boşluq ayarlanır; uzaqdan çəkilibsə düzgün yaxınlaşdırılır
(≤1.12x, çoxu lazımdırsa bunu yaz). Yazı və kartlar bədənin böyük hissələrini örtmür; yer lazımdırsa kadr 2 hissəyə bölünür
(danışan bir hissədə, element digərində). Üz heç vaxt örtülmür.

**Element növbəsi (B-roll, animasiya, kart, birbaşa kadr dəyişmə).** Element girəndə ya tam kadr dəyişir (ekspert görünmür —
ya B-roll, ya animasiya), ya kadr bölünür; yarıörtmə yoxdur. Dəyişiklik **fikir bitəndən sonra** olur. 0.1–1 s göstərilən
element və ya ekspert olmaz: element ən azı ~2 s, elementlər arasında ekspert ən azı ~2 s. Bəzi videoda animasiya danışıqdakı
cümlələrə bağlı ekranda gəlir, bəzisində birbaşa kadr dəyişir — **videoya və mövzuya görə sən seç**. "Hər videoda B-roll/animasiya
olmalıdır" və ya "hamısı dümdüz olmalıdır" kimi qayda yoxdur.

**Hook və axıcılıq.** İlk saniyələr `skills/creative/hook-design.md` ilə seçilir (üsul + səbəb 1 cümlə); danışığın sırası dəyişmir.
Video başdan sona izləyicini saxlamalı, dinamik olmalıdır — mexaniki "hər N saniyə effekt" yoxdur, dinamika məzmundan gəlir.
`skills/creative/broll-function.md`: hər elementin funksiyası və izah etdiyi fikir var; yoxdursa qoyulmur.

**Kəsim və pauza.** Yalnız təkrar, alınmayan cəhd və kənar söhbət çıxır. Söz və heca kəsilmir. Vurğu yaradan və ya fikri anlamağa vaxt
verən pauza qalır; saniyə həddi ilə mexaniki kəsim yoxdur. Arxa səs kəsiləndə/təmizlənəndə ekspertin səsi dəyişmir (`voice-clean`).

**Zoom və keçidlər (MƏCBURİ — icra statusu §4; icra olunana qədər də qayda qüvvədədir, §4-dəki əvəzi tətbiq olunur).** Zoom yalnız hamar və yumşaq olur: planda `zooms` standart olaraq hamardır (smoothstep yaxınlaşma + qısa hamar geri çəkilmə, `scale` ≤1.12), `multicam` calm da hamardır. `smooth:false` (sıçrayış) işlədilmir.
Kəsimdə keçid hiss edilməməlidir: kəsim cümlə sərhədində, səsin ən sakit yerində, 12 ms səs keçidi, lazım olsa J/L-cut. Sərt sıçrayış yoxdur.

**Altyazı.** `skills/creative/caption-typography.md`: 4 rol ayrıdır (altyazı, hook, vurğu, CTA); Azərbaycan hərfləri düzgün; ≤2 sətir;
safe zone; mətn bloku enin ≤86%-i; kontrast kifayət qədər. ASR səhvləri `corrections` ilə düzəlir; mənanı dəyişən təxmin yoxdur — şübhəli sözlər siyahıda.

**Musiqi.** Standart olaraq VAR (yalnız istifadəçi bu müştəri/video üçün "yox" deyibsə istisna). Dinamik və sahəyə uyğun (uşaq/ana → şən kids;
təhsil/reklam → educational/corporate; hekayə/psixologiya → mövzuya uyğun, amma yavaş piano və kədərli yox). Yalnız CC0 və Mixkit; CC-BY və
qeyri-kommersiya yox. Planda `volume`/`vol` yazma — `"auto"` (danışıqdan ≈16 LU aşağı).

**SFX.** Videoya və vizual elementə uyğun seçilir; hər SFX bir elementə bağlıdır; element silinirsə SFX də silinir; köhnə versiyadan qalan SFX olmur.

**Rəng.** `look: auto`. Şablon, müştəriyə bağlı sabit filtr, saturation artımı, üz/dəri emalı yoxdur. Brend rəngi yalnız altyazı və qrafikaya aiddir.

**Çıxış.** Instagram üçün 1080x1920 (4K göndərilmir), H.264, −14 LUFS, pik ≤−1.5 dBTP. Zəmanət ("sıfır keyfiyyət itkisi", ölçülməmiş vaxt) verilmir.

**Dürüstlük.** Qiymət, tarix, əlaqə, rəqəm, çağırış, titul yalnız danışıqdan/profildən/istifadəçidən. Real olmayan məkan həqiqi kimi göstərilmir.
Müştəri mediası, transkript və şəxsi məlumat GitHub-a yüklənmir.

**Davamlılıq.** Müştərinin rəng ailəsi sabit; hook, altyazı üslubu və kart ardıcıllığı son 3 videodan (`history`) fərqli (`variation`).

## 3. YALNIZ istifadəçi deyəndə
Güzgü çevirmə (`hflip`), arxa fonu bulanıqlaşdırma/dəyişmə, ödənişli xidmət və API, hazır rəng şablonu.

## 4. Hazırda sistemdə YOXDUR (əvəzi)
Bunlar qaydadan azad etmir: §2-dəki qaydalar məcburidir, kod isə ayrıca işdir. İcra olunana qədər aşağıdakı əvəzi tətbiq olunur və təhvildə bunun hələ tam hamar olmadığı açıq yazılır.
- **Hiss edilməyən video keçidi (MƏCBURİ qayda, icra gözlənilir):** videoda dissolve/crossfade yoxdur → cümlə sərhədində, səsin ən sakit yerində kəsim + 12 ms səs keçidi + J/L-cut; yumşaq video keçidi hələ icra olunmayıb. (Hamar zoom artıq var.)
- **Bədən örtülməsi yoxlaması:** `verify`/preflight yalnız üzü yoxlayır → vizual kadrda özün yoxla, kart bədəni örtərsə kadrı böl.
- **Element ≥2 s qaydası:** preflight xəbərdarlıq edir, avtomatik düzəltmir → planda vaxtları özün düzəlt.

## 5. Plan faylı (şablon — mətnləri danışıqdan yaz)
```json
{
  "approach": "M01+M02", "title": "<qısa ad>",
  "variation": {"tone": "...", "primary": "#...", "primaryDeep": "#...", "captions": "box", "anim": "pop"},
  "corrections": [{"from": "<ASR səhvi>", "to": "<düzgün>"}],
  "captions": {"enabled": true},
  "graphics": [{"type": "title", "text": "<hook sualı>", "start": 0.15, "dur": 4.5, "y": 0.19}],
  "sfx": [{"kind": "pop", "t": 0.2}],
  "music": [{"start": 0.0, "volume": "auto", "fadeIn": 1.2, "fadeOut": 2.0, "duck": true, "file": "<music çıxışındakı fayl>"}],
  "look": "auto"
}
```
`variation` `storyboard` çıxışındakı təklifdən götürülür. Qrafika `y`-ləri preflight-da interfeys zonasına görə avtomatik düzəlir.
Azərbaycan dili: `ə ğ ı İ ö ü ş ç` şriftdə olmalıdır; `i→İ`, `ı→I` (`lib/az_text`); rəqəmlər `1 200`, `4,5`.
