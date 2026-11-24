# Bir damcının səyahəti — hüceyrə səviyyəsində səyahət şablonu

25 saniyəlik, 1080x1920 (Reels) kinematik animasiya. **Tam pulsuz:** görüntü kodla yaradılan 3D-dir (Three.js),
musiqi earshot-un CC0 alət notlarından bəstələnir, səs effektləri earshot + real-sfx ilə yerləşdirilir.
API açarı və GPU lazım deyil.

**Təsdiqlənib:** Sura Malik üçün sınaq video, istifadəçi bəyəndi (2026-11-24): "çox qəşəngdi".

## Səhnələr (vaxtlar koddadır)
| # | Vaxt | Səhnə | Mətn yeri |
|---|---|---|---|
| 1 | 0–3.9 s | Krem fonda süd damcısı düşür, dalğalar | `scenes[0]` |
| 2 | 3.9–9.1 s | Kamera damcının içinə girir: çəhrayı damarda uçuş, süd hissəcikləri + qan hüceyrələri | `scenes[1]` (açıq rəngli yazı) |
| 3 | 9.1–14.1 s | Hissəciklər hüceyrə ətrafında kristal qalxana çevrilir, "yad" hissəciklər geri sıçrayır | `scenes[2]` |
| 4 | 14.1–20 s | Siqnal aşağıdan yuxarı: neyronlar bir-bir işıqlanır | `scenes[3]` |
| 5 | 20–25 s | Neyronlar ürəyə çevrilir, ürək döyünür; imza | `scenes[4]` |

## İstifadə
```bash
bash templates/cell-journey/build.sh stories/sura-ana-sudu.json          # -> projects/cell-journey-sura-ana-sudu/final_ig.mp4
```
Yeni mövzu üçün `stories/` altında yeni JSON yarat (məs. `stories/<müştəri>-<mövzu>.json`):
- `scenes`: 5 element, hər birində `title` (sətir keçidi `\n`) və istəyə görə `subtitle`.
- `theme` (istəyə görə): `primary`, `primaryDeep`, `accent`, `textDark`, `textLight` — müştərinin rəng ailəsindən
  (`templates/expert-reels/experts/<müştəri>.json` → `theme`).

Müddət: ~5–8 dəq kadrlar (750 kadr, CPU), ~4 dəq musiqi (ilk dəfə notlar render olunur, sonra keşdən).

## Qaydalar
- Tibbi/peşəkar mətn ekspertin dediyindən qəti olmasın; yayımdan əvvəl ekspert təsdiqləsin.
- Mətn 1250 px-dən aşağıda, yumşaq krem işıq fonunda — Reels interfeysinə və 3D obyektlərə düşmür.
- Danışıq yoxdur → SFX `--no-duck` ilə; son fayl −14 LUFS / −1.5 dBTP (`build.sh` özü edir). Təhvildən əvvəl `delivery_qc`.
- Musiqi profil qaydasına uyğundur: piano/yavaş yox (kalimba, arfa, selesta, pad, yumşaq nağara; 100 BPM).

## Fayllar
`index.html` (səhnə, `window.renderAt(t)` — deterministik), `render.mjs` (Playwright ilə kadr-kadr çəkir),
`music.py` (musiqi), `cues.json` (səs effektlərinin anları), `build.sh` (hamısı bir əmrlə).
