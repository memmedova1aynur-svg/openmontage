---
name: kids-quiz-comedy
description: «Kids Quiz Comedy» — uşaqlarla interaktiv sual-cavab videoları (müştəri kodu «XB»): komediya tərzi, düşüncə buludu, cavab stikerləri, gülməli yerdə zoom + səs effekti, çəhrayı/firuzəyi/sarı. İstifadə et: «kids quiz», «uşaq sual-cavab», «XB stili», «tapmaca videosu», bu müştəri üçün yeni video istənəndə.
---

# Kids Quiz Comedy (müştəri «XB»)

Müştəri adı repoda yazılmır. Qovluq `instagram-clients/<müştəri>/` (gitignore); çəkilişlər Drive-dan.

## Format
Uşaqlarla interaktiv sual-cavab: ümumi sual-cavab oyunu · «Mən kiməm?» tapmacaları · «Hansıdır?» seçim oyunu. Hər video 40–60 s.

## Təsdiqlənmiş tələblər
- **Dümdüz altyazılı montaj bəyənilmir.** İnteraktiv, komediya tərzində, peşəkar.
- Uşaq düşünərkən başının üstündə firuzəyi **düşüncə buludu** — cavabın (və ya çaşdırıcı şeyin) şəkli; seçim oyununda iki seçim + «?».
- Deyilən hər əşya/heyvan **stikerlə** göstərilir (yan stikerlər).
- Cavab stikeri: sarı (düzgün ✅) / çəhrayı (səhv 😅); çəhrayı başlıq; tullanma animasiyası.
- Gülməli yerlərdə yaxınlaşma + səs effekti. Cavab anında yaxınlaşma: düzgün 1.13, səhv 1.3.
- Kadr **geniş** (çox yaxınlaşdırma keyfiyyəti pozur): base s=0.88, cy=0.46, düzgün rakurs.
- Rəng: yüngül canlılıq (contrast 1.05, saturation 1.14, brightness +0.012).
- Altyazı: əl ilə yoxlanmış; cavablar sarı, böyük.
- Səs effektləri: tada (düzgün), boing + fail (səhv), blip (stiker) — numpy ilə sintez olunur.
- Səhifə rəngləri: çəhrayı, firuzəyi/səma mavisi, sarı (HEX təsdiqlənməyib — uydurma).
- Emoji: NotoColorEmoji.

## Diqqət
- Uşaq üzü və adı — valideyn razılığı təsdiqlənməlidir.
- Dəqiq eşidilməyən cavab uydurulmur; kontekstə görə yazılıbsa qeyd edilir.
- Rubrikanın adı müştəridən soruşulur.
- Çəkilişlər 1920×1080 + fırlanma metadatası ilə şaquli ola bilər — yoxla.
