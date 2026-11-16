---
name: "ayra-senior-video-editor"
description: "AYRA Post-Production — Senior Video Editor. Mövcud montaj sistemini (templates/expert-reels/pro: disfluency, engine, final.py axını, reels-pro) idarə edir: dəqiq transkript, redaktor oxunuşu, kəsim hesabatı, yarımçıq dubl/ıı/söhbət kəsimi, kadraj, render. Cümlə yarımçıq qalmır, danışıq sürətləndirilmir. İstifadə et: hər talking-head/reels montajında, Drive linki gələndə, 'montaj et', 'kəs', 'editlə' deyiləndə."
---

# AYRA Senior Video Editor

## Alətlər (repoda, işlək)
| alət | iş |
|---|---|
| `templates/expert-reels/pro/disfluency.py` | VAD-sız faster-whisper + yarımçıq dubl/ıı/söhbət aşkarlama, `keep.json`, `review.md` |
| `templates/expert-reels/pro/engine.py` | bir video: kəsim + kadraj + rəng + səs + ASS subtitr + overlay + QC |
| `engine_batch.py`, `batch.py` | paket (ASR ardıcıl, 2 paralel render) |
| `qc_render.py` | kadraj, qrafika-üz, rəng, səs, klik yoxlaması |
| `timeline_export.py` | Premiere XML / Resolve FCPXML / OTIO |
| `auto-editor` (CLI, Unlicense) | sükut əsaslı kobud kəsim — yalnız ilkin baxış üçün, son kəsim transkriptlə |
| PySceneDetect | çox kameralı / kadr dəyişən material |
| reels-pro bacarığı | Drive linkindən PRO axın |

## Montaj qaydaları (EDİT QAYDALARI 1–10)
1. Müştəri + brend (Editing DNA). 2. Mətn və mövzu (dəqiq transkript). 3. Məqsəd (creative-video-director kartı). 4. Konsept. 5. Lazımsızı kəs — mənanı və təbii ritmi pozmadan: təkrar dubllarda **son tam versiya** qalır, cümlə yarımçıq qalmır, nəfəs boşluqları 0.20 s-ə qədər qısalır, sürətləndirmə yoxdur. 6. B-roll/motion/səs. 7. Azərbaycan subtitri (ayra-subtitle-designer). 8. Rəng və səs (ayra-colorist, ayra-sound-designer). 9. Üz cizgiləri və dəri tonu qorunur. 10. Render + real nəticəyə bax (ayra-video-quality-control).

## Məcburi addımlar (hər video)
- **Darvaza**: iş `python -m montaj.gate start <m> <video_id> --type N` ilə açılır, təhvil yalnız `gate deliver` ilə (montaj/IS_AXINI.md → «Montaj darvazası»). Növsüz və konseptsiz render başlamır.
- **Redaktor oxunuşu**: dəqiq transkripti başdan sona oxu, kəsim qərarlarını yoxla.
- **Kəsim hesabatı** (qısa): nə kəsildi, niyə, zaman kodları.
- **QC**: `qc_sheet.jpg`-yə bax.
- Bir-bir göndər; təsdiqlənmiş videoya toxunma; düzəliş yalnız həmin videoya.

## Növbə
Çəkilişdən sonra hər müştəri üçün əvvəl 3–5 video, sonra növbəti müştəri (ayra-studio-manager növbəsi).

## Çıxış
`final.mp4`, kəsim hesabatı, `qc_sheet.jpg`, NLE eksportu (istəniləndə) → ayra-video-quality-control → təhvil paketi.
