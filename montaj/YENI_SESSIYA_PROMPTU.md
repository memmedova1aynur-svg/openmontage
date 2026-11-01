# Yeni montaj söhbəti üçün başlanğıc promptu

Yeni Claude Code söhbətini açanda (repo: montaj sistemi olan repo, main branch; mühitdə `FREESOUND_API_KEY` olsun)
aşağıdakı mətni **ilk mesaj** kimi göndərin, sonra Drive linklərini əlavə edin.

---

Bu söhbət müştəri videolarının gündəlik montajı üçündür. Montaj sistemi repodadır — onu yenidən yazma, kod əlavə etmə.

1. Əvvəlcə `AGENT_GUIDE.md`-ni, sonra **`montaj/IS_AXINI.md`**-ni oxu və ona tam əməl et.
2. Mühiti yoxla (setup skripti sessiyadan əvvəl işləyib):
   - `python3 -c "import faster_whisper; from montaj import voiceclean; print(voiceclean.available())"` və `ffmpeg -version`;
     (`import df` birbaşa xəta verir — torchaudio uyğunsuzluğu; `voiceclean` bunu öz düzəlişi ilə keçir, bu normaldır);
   - nəsə çatışmırsa: `bash scripts/cloud-setup.sh`;
   - `export MONTAJ_DATA_DIR=$HOME/montaj-data MONTAJ_OUT_DIR=$HOME/montaj-data/out`;
   - `FREESOUND_API_KEY`-i həqiqi sorğu ilə yoxla ("calm piano", yalnız CC0, 1 nəticə); dəyərini göstərmə. Nəticəni bir sətirlə de.
3. Hər yeni video üçün iş axını:
   - əvvəl bir qısa sorğu (müştəri, video növü — `types --survey`, məqsəd, müddət, xüsusi istək), sonra Drive linki;
   - analiz, təkrar və alınmayan cümlələrin təmizlənməsi (söz kəsilmir), kadraj düzəlişi (`framefix`),
     arxa səs təmizləmə (`voice-clean`);
   - B-roll-u özün hazırla (`session scenes`, planda `broll[].make`); səhnə mətni yalnız danışıqdan;
   - **bir qərar mesajı**: 3 storyboard + kadraj əvvəl/sonra + rəng variantları + 2–3 musiqi nümunəsi
     (Freesound, yalnız CC0) + səs əvvəl/sonra. Mən bir cavabla seçirəm;
   - sonra yalnız **yekun MP4**: `render` + `verify` + şübhəli sözlər siyahısı. Ara düzəliş raundu yoxdur.
   - müştəri hələ çəkməyibsə: `types <N> --shoot --client "<ad>"` (çəkiliş tövsiyəsi); `storyboard`-dakı material
     yoxlamasının `!` qeydlərini qərar mesajında qısa de.
   - növə görə alətlər (`types <N>`): reklam `ad-plan`, seminar `highlights`/`extract`, tədbir `event-scan`/`event-plan`,
     sual-cavab `qa-plan`, iki nəfər `duo`, karusel `carousel-plan`/`carousel`, nağıl `tale-plan`, motion graphics `mg-scan`;
     ümumi: virtual multikamera (`multicam`), arxa fon (`bg`, kitabxana `montaj/backgrounds`), yavaşlatma (`slowmo`, 60 fps),
     J/L-cut (planda `"jl"`). Montaj prinsipləri: `montaj/KINO_DILI.md`.
4. Qaydalar:
   - müştəri üslubu onun profilindən (`templates/expert-reels/experts/`); brend rəngi rəng ailəsidir;
   - ödənişli xidmət qoşma;
   - müştəri mediası, transkript və layihə fayllarını repoya commit etmə;
   - redaktor panelinin linkini yalnız istəsəm göndər;
   - DeepFilterNet modeli ilk dəfə işə düşəndə icazə soruşularsa — icazə verirəm.
5. Uzun texniki hesabat yazma: yalnız seçimlər, vacib suallar, real maneələr və hazır nəticə.
6. Sistemdə səhv və ya çatışmazlıq görsən, burada kodu dəyişmə — mənə qısa yaz, ümumi sistem ayrıca söhbətdə inkişaf etdirilir.

İndi mühiti hazırla və hazır olanda sorğunu aç.
