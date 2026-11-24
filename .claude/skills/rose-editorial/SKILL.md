---
name: rose-editorial
description: «Rose Editorial» — laktasiya və uşaq inkişafı üzrə mütəxəssisin (müştəri kodu «SM») təsdiqlənmiş vizual və montaj sistemi: çəhrayı–bordo palitra, Playfair serif, editorial kompozisiya, real portret; hər videoya mövzuya görə ayrı üslub (mif-fakt, sənədli, sual-cavab, sayğac…). İstifadə et: «rose editorial», «çəhrayı editorial stil», «SM stili», «ana-uşaq mütəxəssisi videosu», bu müştəri üçün video/cover/karusel istənəndə.
---

# Rose Editorial (müştəri «SM»)

Müştəri adı repoda yazılmır (açıq fork). Müştəri qovluğu `instagram-clients/<müştəri>/` (gitignore); xam çəkilişlər və brend faylları Drive-dan.
Ad lövhəsi titulu: «Laktasiya və uşaq inkişafı üzrə mütəxəssis» («ANA SÜDÜ MƏSLƏHƏTÇİSİ» YAZILMIR).

## Brend (KİLİDLİ — agentlik təsdiqi olmadan dəyişmir)
- Rənglər: `#DC5063` · `#FFB4B4` · `#FFF4F3` · `#FCF0EF` · `#FF838D` · `#AF2240` (2-ci pinned postun orijinal faylından). Başqa rəng əlavə edilmir. (Köhnə «Variant E»: `#DC5063 #AF2240 #FFB4B4 #E29999 #F6D3CF #FFF4F3` — yalnız arxiv.)
- Şriftlər: Playfair Display (serif başlıq: Italic 400 + Black 900) · DM Sans (köməkçi) · Caveat (az, əl yazısı vurğu). Video altyazıda Poppins (300–700, Ə dəstəkli) işlənib.
- Xarakter: çəhrayı–bordo–qırmızı–yumşaq açıq tonların balansı; zərif güclü serif; editorial kompozisiya; real portret; mövzuya uyğun kağız/kart/kitab/sual/xətt detalları; foto/tipoqrafik/qrafik növbələşir.
- Qadağalar: palitranı/fontu/brend xarakterini dəyişmək, başqa müştərinin sistemi, bütün cover-ləri düz fon + mərkəzdə portret formatına salmaq. Kreativlik = sistemin DAXİLİNDƏ yeni ideya/kompozisiya/metafora.

## Portret
- Videodan kadr `ayra-smart-portrait-selector` ilə (göz açıq, ağız yumulu/təbəssüm). Keyfiyyət Real-ESRGAN (üz bərpası YOX), təbii rəng. Üz cizgiləri dəyişmir, gözəllik filtri/generativ portret yox.
- Təbii məkan qorunur; stiker (die-cut) kimi kəsilmir; foto düzbucaqlı çərçivədə, qollar/çiyinlər daxil; kadrın böyük hissəsini tutur.

## Video montaj stili
- **Hər videoya mövzuya görə ayrı üslub (təkrar yox):** mif-fakt · sənədli/araşdırma girişi (jurnal səhifəsi ~3 s, sonra spiker) · sual-cavab şousu · sayğac («3 qayda») · dekoder / split / məktub / podkast. Talking head sakit; effektlə doldurulmur.
- **Kəsim:** təkrar dubllarda son tam versiya; giriş cümləsindəki yenidən başlamalar kəsilir; düşünmə fasilələri və «şey» kəsilir; cümlə yarımçıq qalmır; sürətləndirmə yox.
- **Kadraj:** baş üstü az boşluq, aşağıdan çox kəsmə yox, həddən artıq yaxınlaşdırma yox (~1.08).
- **Rəng:** color_auto, təbii dəri; studiya fonu (bənövşəyi üçbucaqlı divar) videoda olduğu kimi qalır.
- **Subtitr:** ağ/krem mətn, vurğu sözü pastel çəhrayı blokda (`#FFB4B4` fon, `#AF2240` mətn); 2–4 söz; üzdən aşağı, UI zonasından yuxarı; düzgün Azərbaycanca.
- **Motion:** başlıq kartı (mask reveal), «MİF / FAKT» kartları, sual kartları, sayğac; giriş 0.35–0.6 s expo.out. Ad lövhəsi spiker görünən kimi, y≈1400, 2 s.
- **Hook:** ilk 2–3 s ekranda sual və ya mif, danışıqdakı cümlə ilə üst-üstə.
- **Musiqi:** Mixkit, hər videoda fərqli, danışığı örtmür; SFX az.
- **Keçidlər:** sərt kəsim + kart giriş/çıxışları; səbəbsiz zoom yox (cümlə arası <0.1 s olan yerdə zoom/kəsim yox).
- **İstifadə etmə:** üzün üstündən heç nə (tint, split xətti, stiker) keçmir; stikerlər gözə/üzə yaxın yox — yuxarı sağ künc; jurnal səhifəsi 3 s-dən uzun qalmır; kölgəli/AI görünüşlü qrafika; uydurma statistika.

## İş qaydası
- **VİDEOLAR BİR-BİR:** bir video hazırlanır, göndərilir; növbəti yalnız agentliyin rəyindən sonra, o rəydəki düzəliş nəzərə alınaraq.
- Status: DRAFT → REVIEW → APPROVED → READY TO PUBLISH → PUBLISHED (APPROVED yalnız agentlik təsdiqi ilə).
- Montaj darvazası: `python -m montaj.gate start <müştəri> <video> --type N` → concept → kəsim → render → `qc_render.py` + gözlə baxış → `gate deliver`.
- Aylıq sistem: ayda 2 dövr × (strategiya → 10 mövzu → ssenari təsdiqi → çəkiliş → 10 montaj → cover → caption → QC → paylaşım planı).
