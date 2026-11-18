---
name: "ayra-video-quality-control"
description: "AYRA Post-Production — Video Quality Control. Final videonu real render üzərində yoxlayır: kadraj (baş üstü ≤0.36, üz ≤0.30), qrafika-üz örtülməsi, cümlə kəsilməsi, subtitr yazılışı, rəng/dəri tonu, LUFS −14±1, klik, A/V sinxron, uzunluq, eksport parametrləri; qc_sheet.jpg-yə baxış məcburidir. Keçməyən video göndərilmir. İstifadə et: hər video təhvilindən əvvəl, 'yoxla', 'QC', 'hazırdır?' deyiləndə."
---

# AYRA Video Quality Control

## Alətlər
`python3 templates/expert-reels/pro/qc_render.py final.mp4 --clean clean_540.mp4 --subs subs.json --out qc/` (kadraj, overlay-on-face piksel fərqi ilə, rəng, səs, klik, yazılış) · `ffmpeg -af ebur128` · `ffprobe` (1080×1920, 30 fps, H.264 High, AAC 48 kHz, faststart) · kadr vərəqi (hər 1–2 s).

## Yoxlama siyahısı
| sahə | hədd |
|---|---|
| Kadraj | baş üstü ≤ 0.36 H, üz hündürlüyü ≤ 0.30 H, üfüq düz |
| Üz | heç bir qrafika (yarımşəffaf da) üzü örtmür (> 10% → FAIL) |
| Kəsim | cümlə yarımçıq deyil, təkrar dubl qalmayıb, sürətləndirmə yox |
| Subtitr | yazılış (glossary), vaxt, UI zonası |
| Rəng | dəri tonu təbii, ekspozisiya, ardıcıllıq |
| Səs | −14 ±1 LUFS, pik ≤ −1 dBTP, klik yox, musiqi danışığı basmır |
| Texniki | A/V sinxron, son kadr tam, uzunluq ≤ platforma limiti |
| Brend | Editing DNA-ya uyğunluq, "istifadə etmə" siyahısı pozulmayıb |

## Müştəri hədləri
Müştərinin `instagram-clients/<m>/montage_rules.json` faylı varsa `--rules` ilə ver — onun kadraj hədləri ümumi hədlərdən üstündür. Darvaza `--rules`-suz QC-ni qəbul etmir.

## Qayda
`qc_sheet.jpg`-yə ÖZÜN bax (Read) və nəticəni `QC/visual_review.md`-yə yaz («NƏTİCƏ: KEÇDİ» / «KEÇMƏDİ» + səbəb). FAIL → düzəliş → yenidən render → yenidən QC. Nəticə qısa QC qeydi kimi təhvil paketinə.
