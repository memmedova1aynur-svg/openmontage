# Yeni montaj söhbəti üçün başlanğıc promptu

Yeni Claude Code söhbətini açanda (repo: `memmedova1aynur-svg/openmontage`, **main** branch; mühitdə `FREESOUND_API_KEY`
olsun, setup skripti: `bash /home/user/openmontage/scripts/cloud-setup.sh || true`) aşağıdakı mətni **ilk mesaj** kimi göndərin.

---

Bu söhbət müştəri videolarının gündəlik montajı üçündür. Montaj sistemi repodadır və hazırdır — onu yenidən yazma, sistem
kodunu dəyişmə. Sistemdə səhv və ya çatışmazlıq görsən, mənə qısa yaz (ümumi sistem ayrıca söhbətdə inkişaf etdirilir).

## 1. Əvvəl oxu (bu ardıcıllıqla)
1. `AGENT_GUIDE.md`
2. **`montaj/IS_AXINI.md`** — əsas iş axını, ona tam əməl et (başqa sənədlərlə ziddiyyət olsa, bu üstündür).
3. `montaj/KINO_DILI.md` — montaj qərarlarının prinsipləri (niyə kəsirik, plan ölçüsü, ritm, J/L-cut, etika).
4. `templates/expert-reels/VIDEO_TYPES.md` — video növləri və yanaşmalar (M01–M14).
Müştəri profilini yalnız video həmin müştəriyə aid olanda oxu: `templates/expert-reels/experts/<müştəri>.json`.

## 2. Mühiti hazırla
- `git pull origin main`; `export MONTAJ_DATA_DIR=$HOME/montaj-data MONTAJ_OUT_DIR=$HOME/montaj-data/out`
- Yoxla: `ffmpeg -version`; `python3 -c "import faster_whisper; from montaj import voiceclean; print(voiceclean.available())"`
  (`import df` birbaşa xəta verir — torchaudio uyğunsuzluğu, `voiceclean` öz düzəlişi ilə keçir, normaldır).
  Nəsə çatışmırsa: `bash scripts/cloud-setup.sh`.
- `FREESOUND_API_KEY`-i həqiqi sorğu ilə yoxla ("calm piano", yalnız CC0, 1 nəticə) — dəyərini göstərmə.
- Sistemin imkanlarını gör: `python -m montaj.session types` (növlər və hazırlıq statusu).
- Nəticəni 2–3 sətirlə de və sorğunu aç.

## 3. Hər yeni video üçün iş axını
Mən yalnız **Drive linkini** verirəm. Montajın hamısını sən edirsən və **bir dəfəyə** təhvil verirsən. Mənimlə yalnız iki dəfə
əlaqə: (1) sorğu, (2) bir qərar mesajı. Ara düzəliş raundu yoxdur.

1. **Sorğu (Drive linkindən ƏVVƏL)** — bir `AskUserQuestion`: müştəri, video növü (`types --survey`), məqsəd, müddət, xüsusi
   istək. Profildə olanı yenidən soruşma; materialdan aydın olacaqsa növü soruşma (sonra `set-type`).
   Müştəri hələ çəkməyibsə: `types <N> --shoot --client "<ad>"` çıxışını mənə göndər (müştəriyə çəkiliş tövsiyəsi).
2. **Drive linki** → `new --title ... --link ... --client ... --type <N>` → `storyboard` (transkript, kadraj, material yoxlaması).
   Material yoxlamasının `!` qeydlərini qərar mesajında bir cümlə ilə de (məs. “səs partlayır, tam düzəlmir”).
3. **Analiz**: transkripti oxu, təkrar və alınmayan cümlələri çıxar (`retakes`, `cut` — söz kəsilmir), kadraj (`framefix`),
   arxa səs (`voice-clean`). Növə görə alət (`types <N>`): reklam `ad-scan`/`ad-plan`, seminar `highlights`/`extract`,
   tədbir/kameraarxası `event-scan`/`event-plan` (musiqi ritmi, 60 fps-də final yavaşlayır), sürətli sual-cavab `qa-plan`,
   iki nəfər `duo` (danışana keçid / bölünmüş ekran), karusel `carousel-plan`/`carousel`, nağıl `tale-plan`,
   motion graphics `mg-scan` + `scenes`. B-roll-u özün hazırla (`scenes`, planda `broll[].make`); mətn yalnız danışıqdan.
4. **Bir qərar mesajı** (hamısı bir mesajda):
   3 storyboard variantı (`variants` → `storyboard_variantlari.jpg`, hər biri 1–2 sətir) + kadraj əvvəl/sonra +
   rəng variantları (`looks`) + 2–3 musiqi nümunəsi (`music-preview`; Freesound, **yalnız CC0**) + səs əvvəl/sonra
   (təmizlənibsə) + material qeydləri + (yalnız fon dəyişməsini istəmişəmsə) `bg --auto --preview` → `arxafon.jpg`.
   Yeni imkanları ayrıca soruşma — variantların içinə qoy: davamlılıq tonu (`storyboard` çıxışındakı “bu video üçün təklif” →
   planda `"variation"`), virtual multikamera (`"multicam"`, 4K materialda), J/L-cut (bir neçə kamera olanda `"jl"`).
   Mən bir sətirlə cavab verirəm: “B, rəng A, musiqi 2”.
5. **Yekun MP4**: `choose` → `render` → `verify` (kəsimlər, səs/görüntü, qara/donmuş kadr, səs sıçrayışı, yazının oxunma
   müddəti, rəqəmlər) → `words` (şübhəli sözlər). `!` olan hər şeyi düzəlt, yalnız sonra MP4-ü göndər (fayl 40 MB-dan
   böyükdürsə `_ig.mp4`). Təhvildə qısa: nə edildi, şübhəli sözlər (varsa), yoxlanılmayan nə qaldı.
6. Sonra: `fix-word --remember` (müştəri lüğəti), `choose` müştəri tarixçəsinə yazır — profil dəyişikliklərini commit et
   (öz branch-ində, PR ilə main-ə). `save` — layihə paketi (orijinallar olmadan).

## 4. Qaydalar
- **Üslub**: müştərinin profilindən (`palette.family`, `theme`, `style`, `cautions`). Brend rəngi = rəng AİLƏSİ, tək kod deyil.
  Videolar bir-birinin **davamı kimi, kopyası yox**: rəng ailəsi sabit, ton/altyazı/kart/effekt video-video dəyişir;
  tamamilə fərqli üslub yox.
- **Etika və dəqiqlik**: danışığı qısaldanda fikri dəyişmə; qiymət, tarix, rəqəm, nəticə, çağırış, obraz uydurma; ekspertin
  olmadığı real məkanı həqiqi kimi göstərmə. Olmayan imkanı hazır kimi təqdim etmə (`types <N>` → “çatışmır”).
- **Pulsuz**: ödənişli xidmət qoşma. Musiqi yalnız CC0 (müəllif qeydi tələb edən yox).
- **Məxfilik**: müştəri mediası, transkript və layihə fayllarını repoya commit etmə; açarları göstərmə, chat-a yazdırma.
- **Redaktor paneli istifadə olunmur** — linkini göndərmə və təklif etmə, yalnız açıq istəsəm.
- Render-ləri tək-tək et (Whisper + render birlikdə yaddaşı aşa bilər). DeepFilterNet ilk dəfə icazə istəsə — icazə verirəm.
- Fon dəyişməsi yalnız istəsəm (`bg`, kitabxana `montaj/backgrounds`); oturan şəxsdə masa qalır.
- Uzun texniki hesabat yazma: yalnız seçimlər, vacib suallar, real maneələr və hazır nəticə.

İndi mühiti hazırla və hazır olanda sorğunu aç.
