---
name: openverse-sfx
description: Openverse-dən pulsuz, lisenziyalı REAL səs effekti tap və yüklə (bul). Creative Commons (CC0/BY/BY-SA) audio, açarsız API, müəllif qeydi avtomatik CREDITS.md-yə yazılır. Videoya whoosh, klik, pop, zərbə, qapı, ayaq səsi kimi real yazılmış səs lazım olanda, "səs effekti tap", "sfx bul", "openverse", "free sound effect", "find a real recording" deyəndə işlət. Yerləşdirmək üçün real-sfx, sıfırdan yaratmaq üçün earshot skill-i.
---

# Openverse SFX — bul

Üç addımlı səs zəncirinin 1-cisi: **bul (openverse-sfx) → yerləşdir (real-sfx) → üret (earshot)**.
Openverse ~1M+ açıq lisenziyalı audio indeksləyir (Freesound, Wikimedia Commons, Jamendo). API açarı lazım deyil.

## Addımlar
1. Axtar (ingiliscə sözlər daha yaxşı işləyir; default: yalnız `sound_effect`, kommersiya üçün icazəli, ≤5 s):
   ```bash
   python3 .claude/skills/openverse-sfx/scripts/openverse_sfx.py search "whoosh" --n 10
   ```
   Seçimlər: `--license commercial|modification|all`, `--max-sec 0` (limitsiz), `--source freesound`, `--any-category`, `--json`.
2. Bəyəndiyini kitabxanaya yüklə — **tip** qovluğu real-sfx-in onu tapması üçündür:
   ```bash
   python3 .claude/skills/openverse-sfx/scripts/openverse_sfx.py get --id <ID> --type whoosh --lib assets/sfx
   # və ya ilk N nəticəni birbaşa:
   python3 .claude/skills/openverse-sfx/scripts/openverse_sfx.py get "camera shutter" --type click --n 3
   ```
   Nəticə: `assets/sfx/<tip>/<ad>__<id>.ext`, `assets/sfx/CREDITS.md`, `assets/sfx/openverse_manifest.json`.

## Qaydalar
- **Lisenziya:** default olaraq NC/ND (qeyri-kommersiya, dəyişdirilməz) çıxarılır. CC0/PDM — qeyd lazım deyil; **BY / BY-SA — müəllifi caption/description-da qeyd et** (`CREDITS.md`-dən götür). Müştəri işində `--license all` işlətmə.
- Tip adları: `whoosh, swipe, hit, impact, click, pop, ding, riser, typing, camera, door, footsteps ...` — real-sfx bu qovluq adlarına görə axtarır.
- Eyni effektdən 2–3 variant yüklə ki, təkrarlanan yerlərdə eyni səs eşidilməsin (real-sfx onları növbə ilə işlədir).
- Dinləmədən təhvil vermə: `ffprobe`/qısa dinləmə və ya earshot `describe` (listen extra) ilə yoxla.
- `OPENVERSE_TOKEN` env (istəyə bağlı) — yüksək limit üçün.

## Əgər bağlıdırsa
`api.openverse.org` şəbəkədə bloklanıbsa skript `openverse error ... 403` qaytarır (rc=2). Onda:
mühitin şəbəkə ayarlarına `api.openverse.org` (+ fayl hostları, məs. `cdn.freesound.org`) əlavə etməyi təklif et,
və ya həmin səsi **earshot** skill-i ilə yarat. Nəticə uydurma.
