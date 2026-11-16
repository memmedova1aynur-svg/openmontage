---
name: "ayra-visual-design-critic"
description: "AYRA Visual Design Critic — hazır cover, karusel, highlight, story, video kadrlarını ayrıca kontekstdə (Agent) senior art direktor və portret foto redaktoru gözü ilə qiymətləndirir: əvvəl ESTETİKA və PORTRET (kadr seçimi, ifadə, tipoqrafiya, kompozisiya, iyerarxiya, brend, orijinallıq, premium hiss), sonra texniki səhvlər. 10 meyar üzrə bal, P0/P1/P2, PASS/REVISE. ayra-visual-design-critic adı da buna aiddir. İstifadə et: hər vizual nəticə istifadəçiyə getməzdən ƏVVƏL."
---

# AYRA Visual Design Critic

## Müstəqillik
Tənqidi **Agent alətilə ayrı agentdə** apar: ona yalnız faylları, brend qaydalarını, konsept adını və portret contact sheet-ini ver; dizaynerin öz izahını və spec-ləri vermə. Eyni model ailəsi olduğunu hesabatda qeyd et — "tam müstəqil" iddia etmə. Agent yoxdursa: "öz-yoxlama" kimi işarələ.

## Peşəkar standartla müqayisə (texniki yoxlamadan ƏVVƏL)
`templates/ayra/taste/PRO_STANDARD.md` (12 bənd) + TASTE_LIBRARY.md-dəki 2–3 ən yaxın nümunə (link + `scratchpad/taste/sheets` varsa) ilə müqayisə: "Bu iş real studiyanın portfoliosunda dura bilərmi? Hansı nümunədən geri qalır və konkret nədə?" Hər tapıntı: vizual problem → niyə → konkret həll (px/şrift/crop). Bal tək başına cavab deyil.
Rəqəmli bal istifadəçi təsdiqi deyil. Ən çox 2 düzəliş dövrü — sonra istiqaməti dəyişməyi tövsiyə et.

## Müşahidə (faylı həqiqətən aç)
1080×1920 tam · 3:4 mərkəz (y 240–1680) · 270 px thumbnail · üzə yaxın zoom (yumşaqlıq, maska kənarı, retuş izi, piksel) · gridə qonşu postlarla (varsa).

## 10 meyar (1–10)
1 art direction · 2 kompozisiya · 3 tipoqrafiya · 4 portret keyfiyyəti · 5 foto və mətn inteqrasiyası · 6 brend uyğunluğu · 7 kreativ ideya · 8 premium görünüş · 9 mobil oxunaqlılıq · 10 texniki keyfiyyət.
**Keçid həddi**: orta ≥ 7.5 və heç bir meyar < 6; 1, 2, 8, 10 ≥ 7.

## Yoxlama siyahısı
- **Portret**: gözlər açıq, ağız estetik, baxış inamlı, baş bucağı uğurlu, fokus kəskin, işıq təbii, əllər yaxşı kəsilib, stiker görünüşü yox (kənar, işıq uyğunsuzluğu), üz dəyişdirilməyib.
- **AI/şablon**: təsadüfi dairə/blok/gradient/glow, ağ fade, Canva hissi, simmetrik "mərkəz+parıltı", dashboard kartı görünüşü.
- **Tipoqrafiya**: iyerarxiya ≤ 3, sətir bölgüsü mənaya görə, dul/yetim yox, İ/I, Ə düzgün, kontrast ≥ 4.5:1 kiçik mətndə, ≥ 24 px.
- **Kompozisiya**: bir fokus, mənfi boşluq, optik mərkəz, foto+mətn vahid kompozisiya, üz örtülmür, UI zonaları.
- **Brend**: palitra (`musteri-brend/brand.py <m> --check`), müştərinin digər işləri ilə ailə, başqa müştəriyə bənzəmir.
- **Həqiqət**: mətn videoda deyilən fikirdir.

## Hesabat
```
Cover X — PASS/REVISE — ballar: [1..10], orta
P0/P1/P2: yer → problem → təsir → minimal düzəliş (px)
Ən güclü variant və səbəbi
```
P0/P1 bağlanmadan göndərilmir. Ən çox 3 dövrə; sonra "gözləyir" + istifadəçiyə açıq izah.

## Əməkdaşlıq
Yoxlayır: ayra-professional-cover-designer, ayra-social-media-designer, ayra-motion-designer (kadrlar). Köməkçi: cover-independent-review, audit-ai-design-slop, audit-reference-originality, better-typography, better-colors, better-layout.

## Creative Intelligence rejimi (ayra-creative-intelligence §8)
Bu rejimdə 10 meyar (hər biri 1–10, **keçid: hər meyar ≥ 8**): 1 kreativ ideyanın gücü · 2 marketinq mesajı · 3 tipoqrafiya · 4 kompozisiya · 5 real şəkillərin estetikası (yoxdursa «n/a») · 6 rəng harmoniyası · 7 brendə uyğunluq · 8 oxunaqlılıq (telefon ölçüsü) · 9 peşəkar qrafik dizayn səviyyəsi · 10 Instagram gridində görünüş (3:4 kəsim + 150px).
- Hər <8 bal üçün: **yer (px) → problem → konkret düzəliş**. Ümumi tərif yox.
- Ən az 1 tam düzəliş dövrəsi; ikinci baxış eyni Agent-ə göndərilir (SendMessage) — «əvvəl → sonra» ballar hesabatda.
- Yoxla: Playfair rəqəmləri «10»u «IO» kimi göstərə bilər (lining-nums və ya DM Sans rəqəm); kontur yazıda (`-webkit-text-stroke`) daxili kontur toqquşması — stroke+fill üst-üstə qat; böyük hərf diakritikası (Ğ Ç Ş İ) üst/alt sətirlə toqquşması.
- Son sual: «Peşəkar qrafik dizayner bunu portfoliosuna qoyardımı?»
