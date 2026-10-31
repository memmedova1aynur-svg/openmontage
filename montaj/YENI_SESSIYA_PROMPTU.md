# Yeni montaj söhbəti üçün başlanğıc promptu

Yeni Claude Code söhbətini açanda (repo: montaj sistemi olan repo, main branch; mühitdə `FREESOUND_API_KEY` olsun)
aşağıdakı mətni **ilk mesaj** kimi göndərin, sonra Drive linklərini əlavə edin.

---

Bu söhbət müştəri videolarının gündəlik montajı üçündür. Montaj sistemi repodadır — onu yenidən yazma, kod əlavə etmə.

1. Əvvəlcə `AGENT_GUIDE.md`-ni, sonra **`montaj/IS_AXINI.md`**-ni oxu və ona tam əməl et.
2. Mühiti hazırla: `bash scripts/cloud-setup.sh`, sonra
   `export MONTAJ_DATA_DIR=$HOME/montaj-data MONTAJ_OUT_DIR=$HOME/montaj-data/out`.
   `FREESOUND_API_KEY`-in olub-olmadığını yoxla (dəyərini göstərmə). Yoxdursa bunu mənə qısa de.
3. Hər yeni video üçün iş axını:
   - əvvəl bir qısa sorğu (müştəri, məqsəd, format, müddət, xüsusi istək), sonra Drive linki;
   - analiz, təkrar və alınmayan cümlələrin təmizlənməsi (söz kəsilmir), kadraj düzəlişi (`framefix`),
     arxa səs təmizləmə (`voice-clean`);
   - **bir qərar mesajı**: 3 storyboard + kadraj əvvəl/sonra + rəng variantları + 2–3 musiqi nümunəsi
     (Freesound, yalnız CC0) + səs əvvəl/sonra. Mən bir cavabla seçirəm;
   - sonra yalnız **yekun MP4**: `render` + `verify` + şübhəli sözlər siyahısı. Ara düzəliş raundu yoxdur.
4. Qaydalar:
   - müştəri üslubu onun profilindən (`templates/expert-reels/experts/`); brend rəngi rəng ailəsidir;
   - ödənişli xidmət qoşma;
   - müştəri mediası, transkript və layihə fayllarını repoya commit etmə;
   - redaktor panelinin linkini yalnız istəsəm göndər;
   - DeepFilterNet modeli ilk dəfə işə düşəndə icazə soruşularsa — icazə verirəm.
5. Uzun texniki hesabat yazma: yalnız seçimlər, vacib suallar, real maneələr və hazır nəticə.
6. Sistemdə səhv və ya çatışmazlıq görsən, burada kodu dəyişmə — mənə qısa yaz, ümumi sistem ayrıca söhbətdə inkişaf etdirilir.

İndi mühiti hazırla və hazır olanda sorğunu aç.
