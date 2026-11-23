---
name: turquoise-expert
description: «Turquoise Expert» — disleksiya / uşaq inkişafı üzrə ekspertin (müştəri kodu «S») təsdiqlənmiş Reels montaj stili: firuzəyi brend, sakit-dinamik talking head, izah kartları, interaktiv sual paneli, kinetik tipoqrafiyalı reklam. İstifadə et: «turquoise expert», «firuzəyi stil», «S stili», «disleksiya reklamı», «sual-cavab paneli», bu müştəri üçün yeni video istənəndə.
---

# Turquoise Expert (müştəri «S»)

Müştəri adı repoda yazılmır (açıq fork). Müştəri qovluğu `instagram-clients/<müştəri>/` (gitignore); xam çəkilişlər Drive-dan. Yeni işdə videolar BİR-BİR hazırlanır və göndərilir.

## Brend
- Palitra: fon `#1F4F4F` (tünd firuzəyi) · vurğu `#AAD6D2` · vurğu-2 `#2E8C86` · kağız `#F7FAF9` · mətn `#F7FAF9` · mürəkkəb `#1F4F4F` · altyazıda cari söz `#8FE3D9`.
- Şrift: Montserrat (başlıq və mətn; altyazı 800).

## Ümumi qaydalar (bütün videolar)
- **Kadraj:** sinədən yuxarı (zoom ~1.32), üz yuxarı üçdə birdə, baş üstündə az boşluq. **GÜZGÜ ÇEVRİLMİŞ** (agentlik qərarı, 18.11). Kartlar çənədən aşağı; sual paneli başın üstündə. Mavi şallı geyimdə altyazı sinənin üstündə, kartlar aşağıda.
- **Rəng:** orijinal təbii ton + kontrast 1.04, doyğunluq 1.07, unsharp 0.45. **Vignette, güclü kontrast, isti/soyuq qreyd YOX.** Qırmızılıq olmasın («v3» rəng).
- **Səs:** audio_pro (ölçülmüş küy təmizləmə, −14 LUFS). Fan küyü varsa: fan tonlarını dar kəsim + 110 Hz HPF + DFN 14.
- **Musiqi:** DİNAMİK (sakit ambient YOX), danışıq altında; Mixkit (məs. «Raising Me Higher», «Happy Times»). Kart açılışlarında yumşaq SFX.
- **Subtitr:** Montserrat 800, ≤3 söz, cari söz firuzəyi `#8FE3D9`, MMS forced alignment ilə dəqiq vaxt və düzgün yazılış.
- **İstifadə etmə:** vignette, isti/soyuq rəng, sərt zoom-in/whip keçidlər, emoji, diaqnoz/statistika iddiası, bilinməyən qiymət/tarix, mənbəsiz iddia.

## Təsdiqlənmiş formatlar
1. **Ekspert danışığı (növ 1):** dinamik talking head — cümlə kəsimlərində növbəli yaxınlaşma (1.00 / 1.09), praktik hissədə sakit kadr + izah kartları.
2. **Kadrarxası sual-cavab (növ 2):** interaktiv sual siyahısı — sual yazılır → «oxundu» → cavab kartları → «Cavablandı ✓» → növbəti sual aktivləşir (1/2 → 2/2); iki kamera hissi (1.00 / 1.14).
3. **Reklam / xidmət təqdimatı (növ 3):** kinematik reklam — kinetik tipoqrafiya (hərfləri qarışıb yerinə oturan «DİSLEKSİYA»), daimi «DİSLEKSİYA TƏLİMİ» nişanı, çek-list proqram, sitat anında yavaş yaxınlaşma, CTA kartı + 2 s brend sonluq ekranı.

## İş qaydası
- Montaj darvazası: `python -m montaj.gate start <müştəri> <video> --type N` → concept.md → kəsim → render → `qc_render.py` + gözlə baxış → `gate deliver`.
- Hər video öz formatında; əvvəlkinin kopyası olmur. Musiqisiz variant yalnız istəniləndə.
