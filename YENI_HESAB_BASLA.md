# Yeni hesabda davam — Montaj paneli (OpenMontage üzərində)

Bu fayl repoda saxlanılan **ümumi** təlimatdır. Müştəri mediası, layihə ixracı, Drive linkləri və artifact
bazasındakı düzəlişlər burada **yoxdur** — onlar ayrıca, şəxsi endirilən paketdədir (`montaj_sexsi_paket.tar.gz`,
içində `DAVAM_QEYDI.md`). Repo **public**-dir: ora heç vaxt müştəri faylı, açar, token, cookie qoyma.

- Repo: `https://github.com/memmedova1aynur-svg/openmontage`
- İş branch-ı: `claude/montaj-paneli-az` (main-ə avtomatik merge edilməyib)

## 1. Məqsəd və iş axını

Azərbaycan dilində danışıq videoları (Reels/Shorts, 9:16) üçün telefondan (iPhone) idarə olunan montaj sistemi.
Pullu VPS/API/hosting yoxdur: emal Claude Code bulud sessiyasında, redaktə isə claude.ai **şəxsi artifact** redaktorunda.

1. İstifadəçi videonu verir (Drive linki / fayl) → sessiya `session new` ilə layihə yaradır, transkripsiya (yerli faster-whisper) və analiz edir.
2. Sessiya müştəri profilinə görə **storyboard** təklif edir (şəkil) → **istifadəçi təsdiqləyənə qədər montaj qərarı tətbiq edilmir.**
3. Təsdiqdən sonra `plan.json` yazılır və `session plan` ilə tətbiq olunur (altyazı üslubu, başlıq/bölmə/vurğu/siyahı/kart, zoom, SFX).
4. `session editor --assets` redaktoru qurur → artifact kimi dərc edilir → istifadəçi iPhone-da hər elementi əl ilə düzəldir.
5. Düzəlişlər artifact bazasına (`edits/<layihə-id>`) avtomatik saxlanır (və ya "Düzəlişi kopyala" ilə söhbətə yapışdırılır).
6. Sessiya `ArtifactData` ilə düzəlişi oxuyur → `session apply-edits` → `session render` → yekun MP4 **orijinaldan** hazırlanır.

## 2. Əsas fayllar

| Fayl | Nə edir |
|---|---|
| `montaj/session.py` | Sessiya CLI: new, storyboard, edit, apply, plan, set-client, editor, apply-edits, render, export |
| `montaj/ui/timeline.js` | Vahid model (klip, altyazı, qrafika, undo/redo, editorState/applyEditorState). Brauzer, redaktor və sessiya eyni kodu işlədir |
| `montaj/editor/editor.html` | Artifact redaktorunun şablonu (timeline.js və graphics.js içinə yerləşdirilir) |
| `montaj/editor/graphics.js` | Altyazı/başlıq/kart çəkilişi — önizləmə və render üçün **eyni** kod |
| `montaj/editor/raster.mjs`, `montaj/graphics.py` | Render: Chromium ilə şəffaf PNG → ffmpeg overlay (animasiya formulları önizləmə ilə eyni) |
| `montaj/render.py`, `montaj/fonts.py` | Yekun MP4 (orijinal fayldan, H.264 CRF 18), şriftlər (Montserrat, Caveat — OFL) |
| `montaj/analysis.py`, `montaj/transcribe.py` | Transkripsiya, söz vaxtları, sükut; nəticə keşlənir |
| `montaj/SESSIYA_TELIMATI.md` | Sessiyadakı Claude üçün iş qaydaları |
| `montaj/TELEBLER.md` | Tələblər və status cədvəli (✅/🟡/⛔) |
| `montaj/BUDCE_YOLU.md` | Pulsuz iş yolu əsaslandırması |
| `templates/expert-reels/experts/*.json` | Müştəri profilləri (rənglər, şriftlər, üslub) |
| `templates/expert-reels/` (README, AUDIT, VIDEO_TYPES, scripts/build_edit.py) | Uğurlu montaj şablonları: söz-söz altyazı, kartlar, punch-in zoom, sintez SFX |
| `brand_profiles/` | Brend profili şablonu (müştəri qovluqları gitignore-dadır) |
| `tests/montaj/` | Node + pytest + brauzer E2E testləri |

## 3. Əmrlər

```bash
export MONTAJ_DATA_DIR=/path/data  MONTAJ_OUT_DIR=/path/data/out   # layihə məlumatı repodan KƏNARDA
python -m montaj.session new --title "Ad" --link <Drive-linki> [--client <profil>]   # və ya --file <video>; layihə + analiz
python -m montaj.session set-client --client <profil-adı> <pid>
python -m montaj.session storyboard <pid>                 # təklif → istifadəçi təsdiqi
python -m montaj.session plan <pid> plan.json             # yalnız təsdiqdən sonra
python -m montaj.session editor <pid> --assets assets.json   # artifact üçün (blob URL-lərlə)
python -m montaj.session editor <pid> --local                # yerli sınaq (file://)
python -m montaj.session apply-edits <pid> edits.json [--assets-dir DIR]
python -m montaj.session render <pid>                     # yekun MP4: $MONTAJ_OUT_DIR/<pid>/<pid>_r<versiya>.mp4
```

Testlər:
```bash
node --test tests/montaj/timeline.test.mjs
python -m pytest -q tests/montaj
node tests/montaj/e2e_editor_gfx.mjs <editor/index.html> out.json shots/   # və digər e2e_editor_*.mjs
```

## 4. Mühitin qurulması

- Claude Code bulud mühiti (claude.ai/code) və ya öz kompüter: Python 3.11+, Node 20+, ffmpeg 6+, Chromium + Playwright
  (bulud mühitində hazırdır; `playwright install` etmə).
- `pip install -r montaj/requirements.txt` (faster-whisper, mediapipe, Pillow, fonttools, brotli …).
  mediapipe üçün sistem paketləri: `libegl1 libgles2`.
- Whisper modeli ilk istifadədə endirilir (`MONTAJ_WHISPER_MODEL`, standart `small`) — şəbəkə siyasəti Hugging Face-ə icazə verməlidir.
- `.env` faylı gizli qalır; `.env.example`-a bax. **Heç bir açar repoya yazılmır.**

## 5. İşləyənlər və məhdudiyyətlər

İşləyir (sessiyada və Chromium iPhone emulyasiyasında yoxlanılıb):
- non-destruktiv klip (split/trim/uzatma/sıra/sil/bərpa), bağlı səs, undo/redo, avtosaxlama;
- söz-söz altyazı (aktiv söz rəngli), söz düzəlişi, "layihədə hər yerdə dəyiş", böl/birləşdir, vaxt;
- başlıq, bölmə, vurğu, siyahı (maddələr vaxtla), məlumat kartı — hər birinin şrift/ölçü/rəng/fon/yer/vaxt/animasiyası;
- zoom/kadr/güzgü, parlaqlıq/kontrast/temperatur/doyma/yumşaltma, "orijinala bax";
- musiqi/SFX, səviyyələr, fade, ducking; sintez SFX (whoosh/pop);
- redaktordakı düzəliş → yekun MP4 (sınaqla təsdiqlənib).

Məhdudiyyətlər:
- Real iPhone/Safari-də tam test edilməyib (istifadəçi redaktorun açıldığını təsdiqləyib); emulyasiya real yoxlama sayılmır.
- Artifact asset anbarı audio növü qəbul etmir: musiqi yalnız .m4a/.mp4 (mp4 kimi yüklənir), .mp3/.wav olmaz.
- Whisper Azərbaycan dilində səhv sözlər verir — düzəliş paneldə əl ilə.
- "Söz yarıda kəsilmir" zəmanət deyil.
- B-roll, PIP, üz/məhsul üçün avtomatik yer qoruyucusu, rəvan push-zoom yoxdur. "Dataclone 3" motion qrafikası repoda tapılmayıb.
- Sessiya konteyneri daimi hosting deyil: məlumat qovluğu sessiya bitəndə itə bilər → vacib layihələri paket kimi ixrac et.

## 6. Qaydalar

- **Storyboard təsdiqi:** təsdiqsiz montaj qərarı tətbiq edilmir. Konkret düzəliş istəyində yalnız həmin element dəyişir.
- **Keyfiyyət:** yekun MP4 həmişə orijinal mediadan; şrift, Azərbaycan hərfləri, yer, rəng, animasiya vaxtı önizləmə ilə eyni.
  Effektləri yükləmə; üzü, jesti, məhsulu örtmə; bir müştərinin rəngini başqasına köçürmə; mənanı dəyişmə, fakt uydurma.
- **Token qənaəti:** redaktor kodunu yenidən yaratma (şablon + `session editor`); yalnız seçilmiş müştəri profilini oxu;
  analiz keşini işlət; əl əməliyyatları üçün AI çağırma; element səviyyəsində düzəliş; deterministik render.
- **Təhlükəsizlik:** müştəri mediası/Drive linkləri/layihə ixracları public repoya və açıq saytlara qoyulmur;
  açarlar göstərilmir və yazılmır; pullu resurs istifadəçi təsdiqi olmadan aktivləşdirilmir.
  Qeyd: `templates/expert-reels/experts/*.json` müştəri profilləri (ad, rəng) əvvəlki işlərdən public repoda var —
  saxlanmasını istifadəçi qərar verməlidir.

## 7. Yeni hesabda qoşulmalı xidmətlər

| Xidmət | Niyə | Məcburi? |
|---|---|---|
| GitHub (claude.ai → Settings → Connectors / Claude GitHub App bu repoya) | Kod, branch, push | Bəli |
| Claude Code on the web (bulud mühiti, şəbəkə: GitHub, PyPI, Hugging Face, npm) | Emal, render | Bəli |
| claude.ai Artifacts (db + assets + user imkanları) | iPhone redaktoru | Bəli |
| Google Drive konnektoru | Videonu Drive-dan almaq (yoxdursa — linki "hər kəs baxa bilər" edib vermək) | İstəyə bağlı |
| ElevenLabs | Səs/musiqi (hazırda istifadə olunmur, ödənişli ola bilər) | Xeyr |
| Claude API açarı (panel daxili AI) | İstifadə olunmur — sessiyadakı Claude kifayətdir | Xeyr |

## 8. Növbəti addım

Şəxsi paketdəki `DAVAM_QEYDI.md`-də cari layihənin (ID, versiya, saxlanmış düzəliş) dəqiq vəziyyəti və növbəti addım var.
Qısa: paketi bərpa et → saxlanmış son əl düzəlişini `apply-edits` ilə tətbiq et → render → istifadəçi MP4-də öz düzəlişlərini yoxlasın.
