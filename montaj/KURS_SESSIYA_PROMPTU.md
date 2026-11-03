# Onlayn kurs (təlim dərsləri) montajı üçün başlanğıc promptu

Yeni Claude Code söhbətini açanda (repo: `memmedova1aynur-svg/openmontage`, **main**; setup:
`bash /home/user/openmontage/scripts/cloud-setup.sh || true`; mühitdə `FREESOUND_API_KEY`, məhsul şəkilləri üçün pulsuz
`PIXABAY_API_KEY`) aşağıdakı mətni ilk mesaj kimi göndərin.

---

Bu söhbət Sura Malikin onlayn kursu üçün təlim dərslərinin montajıdır (mövzu: laktasiya — ana südü ilə qidalandırma). Dərslər
saytda yerləşdiriləcək və satışa çıxarılacaq. Montaj sistemi repodadır və hazırdır — onu yenidən yazma, sistem kodunu dəyişmə.
Sistemdə səhv və ya çatışmazlıq görsən, mənə qısa yaz (sistem ayrıca söhbətdə inkişaf etdirilir).

## 1. Əvvəl oxu
1. `AGENT_GUIDE.md`
2. `montaj/IS_AXINI.md` — xüsusilə **2k “Təlim dərsləri / onlayn kurs”** bölməsi (bu iş üçün əsas qaydalar), sonra 3–6-cı addımlar.
3. `montaj/KINO_DILI.md`, `templates/expert-reels/VIDEO_TYPES.md` (növ 15, M14).
4. `templates/expert-reels/experts/sura-malik.json` — rəng ailəsi (çəhrayı, krem), sahə, qeydlər. Diqqət: profildəki Reels
   qaydaları (ikon animasiyaları, hər video fərqli quruluş və s.) bu kursa aid deyil — kursda bütün bölümlər eyni görünür.

## 2. Mühit
`git pull origin main`; `export MONTAJ_DATA_DIR=$HOME/montaj-data MONTAJ_OUT_DIR=$HOME/montaj-data/out`; ffmpeg, faster-whisper,
voiceclean-i yoxla (nəsə çatışmırsa `bash scripts/cloud-setup.sh`). `PIXABAY_API_KEY` varmı — yoxla (dəyərini göstərmə); yoxdursa
de: məhsul şəkilləri (biberon və s.) üçün lazımdır, Mixkit videoları və Wikimedia şəkilləri onsuz da işləyir. Nəticəni 2–3 sətirlə
de və mənə hazır olduğunu yaz — sonra Drive papkasının linkini göndərəcəm.

## 3. Mərhələ 1 — xəritə (montajdan ƏVVƏL, mənimlə razılaşırıq)
Papkada bir neçə bölümün xam videoları var (hər bölüm 5–15 dəq). Bəzi bölümlərdə salamlaşma (giriş) ayrıca bir neçə saniyəlik
video kimi çəkilib, əsas hissə ayrıca.
1. Bütün faylları endir və transkript et (`new --type 15 --link ...` — `--size` VERMƏ, `storyboard`), material yoxlamasına bax
   (ölçü/4K, fps, səs, işıq).
2. Hansı fayl hansı bölümə aiddir, giriş hansıdır, bölümlərin sırası, hər bölümün mövzuları (vaxt kodları ilə), təkrar və alınmayan
   cəhdlər, lazımsız kadrlar — hamısını tap.
3. Mənə **bir xəritə** göndər (`kurs_xeritesi.md`): bölüm → fayllar → giriş → mövzular → çıxarılacaq hissələr → harada nə
   göstəriləcək (siyahı, əsas fikir kartı, seçim kartı, hazır görüntü). Qeyri-müəyyən yerləri sual kimi yaz. Mən təsdiqləyirəm.

## 4. Mərhələ 2 — üslub (ilk bölümdə bir dəfə, bir qərar mesajında)
Videolar üfüqi (YouTube ölçüsü) çəkilib — kadr və ölçü olduğu kimi qalır, keyfiyyət dəyişmir (4K-dırsa 4K təhvil verilir,
kiçildilmir; layout lazım deyil). İlk bölüm üçün 2–3 variant göstər (`variants`): ad-titul lövhəsi, sadə altyazı, kadrın boş
tərəfində qrafika nümunəsi (Suranın üzünü örtməsin), **rəng korreksiyası** (`looks` — məcburidir, video solğun qalmasın; kliplər
arası işıq bərabərləşsin), səs təmizləmə əvvəl/sonra. Mən bir sətirlə seçirəm. Seçilən planı `kurs_sablon.json` kimi saxla — bütün
bölümlər ondan başlayır, kurs boyu eyni görünüş.

## 5. Mərhələ 3 — hər bölümün montajı (ara sual yoxdur)
- Bölüm girişi əvvəldə (ayrıca fayldırsa — `edit --order`), təkrar/lazımsız hissələr çıxır, söz kəsilmir.
- Bölüm açılışında: Suranın adı və titulu (`lower`): “Sura Malik” / “Laktasiya və uşaq inkişafı üzrə mütəxəssis” (titulu profildən və
  ya məndən dəqiqləşdir — uydurma).
- Altyazı: sadə ağ (`"captions": {"style": {"preset": "lesson"}}`) + sayt üçün `captions-file` (SRT/VTT).
- Sakit canlandırma, mövzuya uyğun (~hər 30–90 s bir element, danışığa bağlı): addımlar üçün `list`, əsas fikir üçün `card`,
  seçimlər üçün `choice` (məs. biberon seçimləri: 2–3 variant, uyğunu yaşıl yanır + “ding”), mövzu üzrə hazır görüntü (`stock` →
  `add-broll`, qısa insert və ya kənarda). Sıfırdan qrafik dizayn yox — hazır, pulsuz və müəllif qeydi tələb etməyən material.
  Mətn yalnız Suranın danışığından; tibbi məlumatı danışıqdakından daha qəti etmə.
- Reels effekti yoxdur: zoom, tez-tez kəsim, whoosh/pop, hook, rəng/üslub dəyişkənliyi yoxdur. Musiqi — istəsəm, yalnız açılış/
  bağlanışda çox yumşaq.
- `render` → `verify` → `words`; `!` olanları düzəlt.

## 6. Təhvil
Hər bölüm: MP4 (mənbənin ölçüsündə — 4K-dırsa 3840x2160, “Bölüm N — Mövzu”) + SRT + VTT + işlədilən hazır görüntülərin mənbə/lisenziya siyahısı (qısa).
Bölümləri hazır olduqca göndər; hər biri bir dəfəyə, ara düzəliş raundu yoxdur.

## 7. Qaydalar
- Ödənişli xidmət qoşma; musiqi yalnız CC0; hazır görüntü yalnız qeyd tələb etməyən pulsuz lisenziya (Mixkit, Pixabay, Wikimedia CC0/PD).
- Müştəri mediası, transkript və layihə fayllarını repoya commit etmə; açarları göstərmə.
- Redaktor panelini təklif etmə. Render-ləri tək-tək et. DeepFilterNet icazə istəsə — icazə verirəm.
- Uzun texniki hesabat yazma: seçimlər, vacib suallar, real maneələr, hazır nəticə.

İndi mühiti hazırla və hazır olduğunu yaz.
