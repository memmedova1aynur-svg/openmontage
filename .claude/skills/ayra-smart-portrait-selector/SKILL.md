---
name: "ayra-smart-portrait-selector"
description: "Videodan cover üçün peşəkar portret seçir — 30–100 namizəd kadr, MediaPipe üz nöqtələri ilə göz açıqlığı, ağız, təbəssüm, başın bucağı, baxış, fokus və işıq balları, oxşarların atılması, ən yaxşı 12-dən contact sheet, sonra art direktor gözü ilə son seçim. Təsadüfi video kadrı ilə cover QADAĞANDIR. İstifadə et: hər cover/thumbnail/portretli dizayn başlamazdan əvvəl, 'kadr seç', 'portret', 'cover üçün foto' deyiləndə."
---

# AYRA Smart Portrait Selector

## Alət (yerli, API-siz)
```bash
python3 .claude/skills/ayra-smart-portrait-selector/select_portraits.py <video> <çıxış> [--n 80] [--top 12] [--exclude 2.0,15.6]
```
Model: `/root/montaj-data/models/face_landmarker.task` (yoxdursa: storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task).
Çıxış: `candidates.json` (bütün ballar), `top/<t>.png` (tam kadrlar), `contact_sheet.jpg`.
Kadr sayı: video uzunluğu × 0.7, 30–100 arası. Mənbə: **orijinal çəkiliş** (montaj olunmuş videodan yox — qrafika/altyazı olmasın).

## Ballar
göz açıqlığı (blink) ×3 · ağız (jawOpen, pucker) ×3 · baş pozası (yaw/pitch/roll) ×2 · baxış kameraya ×2 · fokus (üzdə Laplacian) ×1.5 · təbəssüm ×1.2 · sakit qaş ×1 · işıq ×0.8. Sərt filtr: blink > 0.5 və ya jawOpen > 0.45 → bal ×0.4. 1.5 s-dən yaxın oxşar kadrlar atılır.

## İnsan gözü ilə son seçim (məcburi)
`contact_sheet.jpg`-yə bax (Read). Avtomatik bal yalnız siyahını daraldır. Seçim meyarları:
- Təbii ifadə, inamlı baxış, rahat duruş, estetik mimika.
- Konseptə uyğunluq: jurnal → yüngül təbəssüm, baş azca əyik; ekspert portreti → bağlı ağız, birbaşa baxış; konseptual → mövzunun emosiyası.
- Əllər kadrdadırsa, kəsim yerini düşün (barmaq yarısı kəsilməsin).
- Əvvəl rədd edilmiş kadrları `--exclude` ilə çıxar.
Uyğun kadr yoxdursa: müştərinin təsdiqli portret kitabxanası (`Approved References`) və ya fotosuz editorial cover. Uğursuz portreti məcburi işlətmə.

## Portret işi (yalnız foto retuşu)
İcazəli: ekspozisiya, white balance, yüngül kontrast, ölçülü sharpening (UnsharpMask r 1.4, 35%), crop, fon maskası (`rembg` birefnet-portrait, 768 px-də, bir proses = bir kadr — yaddaş), geyimdəki kiçik əşya (lav-mikrofon) retuşu — yalnız toxuma köçürmə ilə (`cv2.seamlessClone`), yeri əl ilə yoxlanır.
QADAĞAN: AI ilə üz yaratmaq, göz/dodaq/burun formasını, bədən proporsiyasını dəyişmək, dərini plastikləşdirmək.
Stiker effektinə qarşı: alfa kənarını 0.8 px yumşalt, fon "studiya kağızı" kimi düz rəng + motivli yumşaq işıq düşməsi, bütün kompozisiyaya eyni dən (grain).
Böyütmə: 1080 mənbədən 2× üzərində böyütmə yumşaq görünə bilər — tam ölçüdə üzə yaxından bax.

## Çıxış
Seçilmiş kadr(lar) + qısa əsaslandırma ("#1 25.2 s — bağlı ağız, birbaşa baxış, ekspert portreti üçün") → ayra-design-director və ayra-professional-cover-designer.
