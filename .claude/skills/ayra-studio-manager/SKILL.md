---
name: ayra-studio-manager
description: "Müştərilərin çəkilişlərini, montaj növbəsini, düzəliş dövrələrini və təhvil tarixlərini sistemləşdirir — hansı video hansı mərhələdədir, kim nəyi təsdiqləyib, növbəti addım nədir. İstifadə et: \"növbə\", \"status\", \"neçə video qalıb\", \"təhvil\", \"çəkiliş planı\", \"nə bitdi\", \"plan qur\" deyiləndə və yeni Drive qovluğu gələndə."
---

# AYRA Production Manager

## Tək mənbə
`instagram-clients/_agency/istehsal.json` (gizli). Hər element:
```json
{"musteri":"<qovluq>","video":"03_Nene_baba","menbe":"drive:<id> və ya fayl","merhele":"montaj|qc|gonderildi|duzelis|tesdiq|saxla",
 "duzelisler":[{"tarix":"...","istek":"...","status":"edildi"}],"tehvil":"YYYY-MM-DD","qeyd":"..."}
```
Status cədvəli: `python3 .claude/skills/ayra-studio-manager/status.py [müştəri]`.

## Mərhələlər
`növbədə → yüklənib → montaj → redaktor oxunuşu + kəsim hesabatı → QC (qc_sheet bax) → göndərildi → düzəliş ↺ → TƏSDİQ` · `saxla` = istifadəçi dayandırıb.

## Qaydalar (agentlik)
- Hazır olduqca **bir-bir** göndər; hər video üçün redaktor oxunuşu, kəsim hesabatı, QC məcburidir.
- Təsdiqlənmiş video dəyişdirilmir.
- Bir videoya düzəliş yalnız o videoya aiddir.
- Drive-dan yalnız istifadəçi deyəndə yüklə; növbədəki linklər `novbeli_qovluqlar.md`-də.
- "Neçə dəqiqə qaldı" sualına saat yox, dəqiqə ilə cavab ver (ölçülmüş sürət: ~2.6 dəq / 1 dəq hazır video, `ENGINE.md`).
- Silmə yalnız istifadəçi deyəndə.

## Çəkiliş planı
Ekspert 1–2 saatda 5–10 video çəkir: hər video üçün tam danışıq mətni (`ig-reel`), kadr/işıq qeydi, geyim dəyişikliyi nöqtələri. Çəkilişdən sonra materialı `istehsal.json`-a əlavə et.

## Əməkdaşlıq
Montaj: `reels-pro`, `engine.py`; motion: `ayra-motion-designer`; cover: `ayra-professional-cover-designer`; yoxlama: `ayra-design-critic`; caption: `ig-caption`.
