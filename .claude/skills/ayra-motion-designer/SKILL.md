---
name: ayra-motion-designer
description: "Hər video üçün motion graphics, B-roll, keçid, kinetik mətn və səs dizaynı planını qurur və Remotion/HyperFrames ilə istehsala ötürür — talking head videolarını sənədli, izahlı və reklam səviyyəsinə qaldırır. İstifadə et: \"motion\", \"animasiya\", \"keçid\", \"B-roll\", \"kinetik mətn\", \"sound design\", \"motion graphics nümunəsi\" deyiləndə və montaj planı (ayra-studio-manager) qurulanda."
---

# AYRA Motion Director

## Prinsip
Hərəkət mənaya xidmət edir: hər animasiya bir şeyi göstərir, vurğulayır və ya keçid verir. Boş "nəfəs alan" hərəkət, səbəbsiz zoom, hər sözə effekt yoxdur.

## İş axını
1. **Material** — dəqiq transkript (`templates/expert-reels/pro/disfluency.py`), mövzu, müştəri brendi (`musteri-brend`), `direction.md`.
2. **Ritm xəritəsi** — videonu 3–6 hissəyə böl: hook (0–3 s), əsas fikirlər, nəticə/CTA. Hər hissə üçün bir vizual cihaz seç (aşağıdakı kataloq). Bir videoda ən çox 3 fərqli cihaz.
3. **Motion vərəqi** (`motion.md`): zaman → cihaz → mətn → hərəkət (giriş/çıxış, easing, müddət) → səs (whoosh/pop/sükut).
4. **İstehsal** — kodla:
   - Remotion (`remotion-best-practices`, repoda `remotion-composer/src/montaj/Motion.tsx`) — şəffaf ProRes 4444 overlay, `engine.py` ilə birləşir.
   - HyperFrames (`hyperframes`, `motion-doctrine`) — HTML əsaslı tam kompozisiya.
   - Ad lövhəsi: `lower-thirds`; səs: `sound-effects`, Mixkit.
5. **Yoxlama** — kadr vərəqi (hər 1 s), üz-qrafika örtülməsi `qc_render.py --clean`, sonra `ayra-design-critic`.

## Cihaz kataloqu
| cihaz | nə vaxt |
|---|---|
| Başlıq kartı (mask reveal, 0.6 s) | hook, mövzu adı |
| Kinetik söz vurğusu | açar söz, rəqəm |
| Sual kartı | sual-cavab formatı |
| Ad lövhəsi (lower third) | ekspertin ilk görünüşü, 2–3 s |
| Siyahı sayğacı (1/3, 2/3) | "3 qayda" tipli videolar |
| Sənəd/mənbə kartı | araşdırma, jurnal istinadı (yalnız real mənbə) |
| İkon + söz | abstrakt anlayış (ikon-kitabxana) |
| Split / müqayisə | iki yanaşma (üzü örtmədən) |

## Vaxt və easing
Giriş 0.35–0.6 s `cubic-bezier(0.22,1,0.36,1)`; çıxış girişdən 30% qısa; kartlar arası ən az 1.2 s sakitlik. Mətn ekranda oxuma müddəti: söz sayı × 0.3 s + 0.8 s.

## Qadağalar
Üzü örtən qrafika (yarımşəffaf da), sürətləndirilmiş danışıq, kəsilmiş cümlə, uydurma statistika, AI ilə real insan təsviri.

## Əməkdaşlıq
Girdi: `ayra-art-director`, `ayra-studio-manager`. Çıxış: montaj sistemi (`engine.py`, `reels-pro`). Yoxlama: `ayra-design-critic`. Köməkçi: `motion-design`, `motion-doctrine`, `kinetic-typography`, `beat-sync-editing`, `lower-thirds`.
