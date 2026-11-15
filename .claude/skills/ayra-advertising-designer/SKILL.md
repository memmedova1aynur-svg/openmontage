---
name: "ayra-advertising-designer"
description: "AYRA Advertising — reklam posteri, satış vizualı, tədbir/təlim/seminar afişası, kampaniya seriyası, xidmət təqdimatı (statik + animasiyalı). Tək mesaj, tək CTA, real məlumat; təsdiqlənməmiş tarix/qiymət [yer tutucu] kimi göstərilir. İstifadə et: 'reklam posteri', 'afişa', 'təlim reklamı', 'seminar', 'kampaniya vizualı', 'satış postu' deyiləndə."
---

# AYRA Advertising Designer

## Qaydalar
- Bir vizual = bir təklif = bir CTA. İyerarxiya: təklifin adı → kimə/nə üçün → kim aparır → tarix/format → əlaqə.
- Tarix, qiymət, yer, nəticə vədi YALNIZ müştəri təsdiqləyibsə; yoxsa `[Tarix]` və "Konsept nümunəsi" qeydi.
- Color blocking / bold typography istiqamətləri reklamda cəsarətli ola bilər; dekor yox — rəng blokunun funksiyası olmalıdır (iki zonanı ayırır).
- Portret blokun sərhədini keçə bilər (qatlı kompozisiya), mətn üzə və əllərə dəymir.
- Formatlar: post 1080×1350, story 1080×1920, A4/A3 çap PDF (`--size poster --fmt pdf`), motion versiya `ayra_design.py animate` (8–12 s, MP4 + GIF).

## İş axını
ayra-copywriter (mətn, hook) → ayra-design-director (istiqamət) → layout → render (png, pdf) → motion versiya (istəyə görə) → ayra-visual-design-critic → təqdim.
