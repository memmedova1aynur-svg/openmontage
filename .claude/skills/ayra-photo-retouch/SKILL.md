---
name: "ayra-photo-retouch"
description: "AYRA Photo Design — portret maskalama (rembg birefnet-portrait), fon dəyişmə, rəng/işıq korreksiyası, ölçülü retuş, fotomontaj, kollaj, təbii fon kompozisiyası, crop. Üz cizgiləri dəyişdirilmir; təbii alınmayan retuş edilmir (orijinal saxlanılır və ya crop dəyişir). İstifadə et: 'fonu sil', 'maska', 'retuş', 'fotomontaj', 'kollaj', 'işığı düzəlt' deyiləndə və hər portretli dizayndan əvvəl."
---

# AYRA Photo Retouch

## Alətlər
`rembg` (birefnet-portrait; 768 px-də işlət, bir proses = bir kadr — yaddaş), Pillow (ImageEnhance, UnsharpMask), OpenCV (seamlessClone, inpaint), ayra-smart-portrait-selector (kadr).

## Standart addımlar
1. Kadr: smart portrait selector-un contact sheet-indən göz ilə seçim.
2. Maska: alfa 2 px choke (MinFilter 5) + 0.8–1.0 px blur; kənar zonasında rəng defringe (içəri ilə 50% qarışıq).
3. İşıq: ekspozisiya ±5%, kontrast ±3%, WB neytral; dəri tonu dəyişmir.
4. Kəskinlik: UnsharpMask r 1.4, 35%. Böyütmə ≤ 1.5× (1080 mənbədən).
5. Fon: düz studiya rəngi (brend palitrası) + bütün kompozisiyaya 5–6% dən; "stiker" görünüşünə qarşı bədən kadr kənarından çıxsın (bleed) və ya qutu içində kəsilsin.

## Qayda: ikinci dərəcəli detallar
Mikrofon kimi kiçik əşyanın silinməsi bir cəhddə təbii alınmırsa — ORİJİNALI SAXLA və ya crop-u dəyiş. Bu işə ən çox 5 dəqiqə.

## Qadağan
AI ilə üz yaratmaq/dəyişmək, dəri hamarlaşdırma, göz/dodaq/burun/bədən formasının dəyişməsi, görünən ləkə və bulanıq kontur.

## Ekran görüntüsü / video kadrı → 4K (məcburi, cover-dən əvvəl)
`python3 .claude/skills/ayra-photo-retouch/scripts/upscale4k.py giriş.png çıxış.png --crop x0,y0,x1,y1 [--size 2160x3840]`
- Real-ESRGAN x4plus (BSD-3), CPU-da plitə ilə (~2–3 dəq/kadr); model ilk dəfə `~/.cache/ayra-sr/`-ə yüklənir.
- Üz bərpası (GFPGAN/CodeFormer) istifadə olunmur — üz cizgiləri dəyişmir.
- Nəticəyə 15–20% orijinal tekstura qarışdır (plastik dəri olmasın); Instagram UI, subtitr və ikonlar `--crop` ilə kənarda qalır.
