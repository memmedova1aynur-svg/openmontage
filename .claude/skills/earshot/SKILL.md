---
name: earshot
description: earshot ilə sıfırdan səs effekti yarat (üret) — 922 dizayn, CPU-da, modelsiz və şəbəkəsiz render; whoosh-un pik anını millisaniyə ilə təyin edir, UI/game/film dəstləri, video kitləri. Çıxış pulsuzdur (kommersiya daxil, qeyd tələb olunmur). Openverse-də uyğun səs tapılmayanda, "səs yarat", "sfx üret", "earshot", "whoosh düzəlt", "generate a sound effect" deyəndə işlət. Yerləşdirmək üçün real-sfx.
---

# earshot — üret

Zəncirin 3-cüsü: **bul (openverse-sfx) → yerləşdir (real-sfx) → üret (earshot)**.
earshot (MIT, github.com/Leonxlnx/earshot) — sözdən səs effekti düzəldən CLI. PyPI-dakı `earshot` başqa layihədir —
**yalnız GitHub-dan qur.** Python ≥3.10; mp3/ogg və video oxumaq üçün ffmpeg.

## Quraşdırma (bir dəfə)
```bash
E=$(bash .claude/skills/earshot/scripts/install.sh)   # -> .venv-earshot/bin/earshot
```
`install.sh listen` — dinləmə əmrləri (`describe`, `match`, `rank`, `critique`) üçün; ilk istifadədə ~1.1 GB model yükləyir,
yalnız lazım olanda qur.

## Yaratmaq
```bash
$E sounds --search whoosh                                  # kataloq (922 səs, 384 ailə)
$E make "a soft pop" -o assets/sfx/pop/soft.wav            # sözdən
$E make "a deep impact hit" -o assets/sfx/impact/a.wav --seed 7 --n 3   # 3 variant
$E sfx render whoosh_fast/crisp -o assets/sfx/whoosh/w1.wav --dur 0.8 --apex 0.32   # pik 0.32 s-də
$E make --set ui -o assets/sfx/ui                          # bütöv dəst: ui | game | arcade | film
$E kit init --preset launch -o audio/kit.json && $E kit render audio/kit.json --out audio/kit   # calm|crisp|minimal|launch
```
Faydalı seçimlər: `--dur`, `--lufs`, `--pitch`, `--seed`, `--format webm,mp3`, `--mono`.

## Qaydalar
- Faylları `assets/sfx/<tip>/` altına yaz — real-sfx onları tip adına görə tapır. Hər tip üçün 2–3 variant (`--seed`).
- real-sfx `place ... --earshot` kitabxanada olmayan tipi avtomatik earshot ilə yaradır (`EARSHOT_BIN=$E`).
- **Hədlər:** danışıq, mahnı, melodiya yaratmır. Çox spesifik real səslər (konkret maşın, insan reaksiyası) üçün
  əvvəlcə openverse-sfx ilə real yazı axtar.
- Nəticəni dinləmədən "hazırdır" demə; listen extra varsa `$E critique fayl.wav` / `$E match fayl.wav "a fast whoosh"`.
- MCP (istəyə görə): `claude mcp add earshot --scope user -e EARSHOT_THREADS=3 -- $E mcp`.
