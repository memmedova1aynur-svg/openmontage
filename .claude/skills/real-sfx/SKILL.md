---
name: real-sfx
description: Videoya REAL səs effektlərini dəqiq kadra yerləşdir (yerləşdir). Videonu analiz edir (kəsimlər + hər an üçün kadr), whoosh/klik/pop/zərbəni lazım olan ana qoyur — whoosh-un ən güclü nöqtəsi kəsimə düşür, səs danışığın altında ducking ilə qalır, musiqi toxunulmur. Çıxış: yeni MP4 + ayrıca SFX WAV stem (Premiere/CapCut/After Effects üçün). "səs effekti əlavə et", "sfx yerləşdir", "videoya whoosh qoy", "real sfx", "add sound effects to this video" deyəndə işlət.
---

# Real SFX — yerləşdir

Zəncirin 2-cisi: **bul (openverse-sfx) → yerləşdir (real-sfx) → üret (earshot)**.
Yalnız stdlib + ffmpeg. Səs kitabxanası: `assets/sfx/<tip>/*.wav|mp3|ogg|flac` (openverse-sfx və earshot ora yazır;
istifadəçinin öz qovluğu da `--lib` ilə verilə bilər).

## Addımlar
1. **Analiz** — kəsimləri tap, hər an üçün kadr çıxar:
   ```bash
   python3 .claude/skills/real-sfx/scripts/real_sfx.py analyze video.mp4 -o cues.json --frames cue_frames
   ```
   `--threshold 0.35` (aşağı = daha çox kəsim), `--min-gap 0.5`.
2. **Qərar (Claude)** — `cue_frames/*.jpg` kadrlarına bax, transkript varsa oxu, `cues.json`-u redaktə et:
   lazımsız whoosh-ları sil, tipləri dəyiş, kəsim olmayan anları əlavə et (yazı çıxışı → `pop`, klik → `click`,
   rəqəm/nəticə → `ding`, böyük açılış → `riser` + `impact`).
   ```json
   {"t": 1.20, "type": "whoosh", "gain_db": -16, "anchor": "peak"}
   {"t": 3.05, "type": "pop", "gain_db": -18}
   {"t": 7.40, "file": "assets/sfx/camera/shutter.wav"}
   ```
   `anchor`: `peak` — səsin ən güclü anı `t`-yə düşür (whoosh/swipe/riser/impact üçün default);
   `onset` — səs `t`-dən 10 ms əvvəl başlayır (qalanları üçün default). `dur` — uzun səsi (gurultu, fon) bu qədər saniyəyə kəsir, yumşaq sönmə ilə.
3. **Yerləşdir:**
   ```bash
   python3 .claude/skills/real-sfx/scripts/real_sfx.py library            # nə var?
   python3 .claude/skills/real-sfx/scripts/real_sfx.py place video.mp4 cues.json -o video_sfx.mp4 [--earshot]
   ```
   Çıxış: `video_sfx.mp4` (video kopyalanır, yenidən kodlanmır), `video_sfx_sfx.wav` (ayrıca SFX stem),
   `video_sfx_sfx_cues.json` (hər səsin mənbəyi — lisenziya izi üçün).
   `--earshot` — kitabxanada olmayan tipi earshot ilə yaradır (`EARSHOT_BIN` və ya PATH). `--sfx-gain -3` bütün qatı
   azaldır, `--no-duck` ducking-i söndürür.

## Peşəkar qaydalar (`skills/creative/sound-design.md`)
- SFX səviyyəsi danışıqdan ən azı 6 dB aşağı: default −14…−18 dB. Danışıq zamanı avtomatik ducking var.
- **Danışıq yoxdursa (trailer, musiqili montaj) `--no-duck` işlət** — əks halda ducking musiqiyə reaksiya verir və
  effektlər itir. Sonra cue anlarında ölç (orijinal vs nəticə, 1.2 s ebur128): trailerdə SFX musiqidən 0–5 dB aşağı
  olmalıdır; lazım olsa `--sfx-gain +3…+6`.
- Analiz həm sərt kəsimləri, həm də yumşaq keçidləri (crossfade, qaranlıqdan keçid) tapır; yenə də kadrlara bax —
  detektor hərəkətli kadrı keçid sanmamalıdır.
- Sosial media üçün son faylı −14 LUFS / −1.5 dBTP-yə normallaşdır (`loudnorm`, iki keçidli) və `delivery_qc` işlət.
- **Az çoxdur:** hər kəsimə whoosh qoyma. 30 s reel üçün təxminən 4–8 effekt; hər effektin səbəbi olsun.
- Eyni tipin bir neçə variantı olsun — skript növbə ilə işlədir.
- Videoda artıq sintetik/köhnə SFX varsa, ikiqat səs olmasın: həmin anları cue-lardan çıxar.
- Təhvildən əvvəl çıxışa qulaq as / `editor-qc` (`delivery_qc`) işlət; `MISSING` sətirləri qalıbsa istifadəçiyə de.
- BY lisenziyalı səs işlənibsə `assets/sfx/CREDITS.md`-dən müəllifi caption-a əlavə et.

Qeyd: bu, Clipwing-in "Real SFX" skill-inin ideyası əsasında OpenMontage üçün yazılmış öz implementasiyadır
(orijinal mənbə bu mühitdən əlçatan deyildi).
