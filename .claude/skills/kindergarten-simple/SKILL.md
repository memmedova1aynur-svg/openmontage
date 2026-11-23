---
name: kindergarten-simple
description: «Kindergarten Simple» — bağça idarəçisinin (müştəri kodu «AH») təsdiqlənmiş sadə danışıq videosu stili, kartlı siyahı tərzi, «Tez sual, tez cavab» yumoristik format, reklam və karusel sistemi. İstifadə et: «kindergarten simple», «AH stili», «bağça idarəçisi videosu», bu müştəri üçün video/karusel istənəndə.
---

# Kindergarten Simple (müştəri «AH»)

Müştəri adı repoda yazılmır. Qovluq `instagram-clients/<müştəri>/` (gitignore); çəkilişlər Drive-dan.

## Ümumi (bütün danışıq videoları)
- Şaquli 1080×1920, 30 fps, H.264. Sinədən yuxarı kəsim.
- Sıx kəsim, amma söz sonu kəsilmir (kəsim sonunda ~0.24 s boşluq); söz müddətinə ümumi hədd qoyma.
- Kadr arxasından sual adətən çıxarılır, video cavabla başlayır (sual məzmun üçün lazımdırsa saxla).
- Altyazı: sadə ağ, Inter qalın, qara kontur, ortadan bir az aşağı. **Musiqi yoxdur.**
- Rəng: təbii — ton dəyişmə/istiləşdirmə/saraltma OLMAZ; yalnız kontrast 1.04, doyğunluq 1.07, yüngül kəskinlik.
- @handle videonun üzərinə YAZILMIR. Hər videoda bir mövzu. Güzgü kimi tərs yazılıbsa çevir.
- Səs: sakit məkan — DeepFilterNet 18 dB, −14 LUFS; küylü məkan — «orta» ayar (DFN 10 dB + HPF 110 + yüngül EQ), güclü təmizləmə səsi boğur.

## Kartlı tərz (siyahı/sadalama)
- Kartlar yuxarıda (y≈240–470), altyazıya və üzə toxunmur. Krem `#F6F2E9`, tünd yaşıl `#1F3D34`, qızılı `#B98A2F`, qırmızı `#B03A2E`; Montserrat.
- Yumşaq açılma/sönmə, alçaq səviyyəli səs. Söhbət tipli videolara kart qoyulmur.

## «Tez sual, tez cavab» (yumoristik)
- Altyazı Playfair Display qalın kursiv 74, deyilən söz yaşıl `#5AE646`. Sualda geniş kadr, cavabda yaxınlaşma (1.3–1.38).
- Cavabın üstündə əyri «möhür» yazısı (Əla!, Doğru deyil…) + səs; əvvəldə «Tez sual, tez cavab · N-ci hissə».
- Televiziyadan reaksiya kadrları yox (müəllif hüququ).

## Reklam (təlim)
- Açılış başlıq kartı, mövzu etiket kartları, sonda 3 s krem son kadr (təlimin adı, dərs/modul sayı, format, «Ətraflı məlumat üçün yazın», @handle). Telefon nömrəsi yazılmır.

## Karusel
- 1080×1350, ≤6 səhifə. Krem fon, tünd yaşıl Montserrat 800 başlıq, qızılı vurğu; yuxarıda ad, aşağıda səhifə nömrəsi və sahə sətri; üz qabığında tünd yaşıl düymə zolağı + ox.
- «Paylaşım xətrinə paylaşım» yox — hər postun məqsədi (şərh, saxlama, təlimə maraq). Sitat postları edilmir.
