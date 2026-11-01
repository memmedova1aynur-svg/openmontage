# Montaj dili — qərar prinsipləri (Claude üçün)

İstifadəçinin verdiyi "Videoqrafiya: çəkiliş və montaj" bələdçisinin öz sözlərimizlə qısa xülasəsi və sistemdəki qarşılığı.
Qaydalar mütləq deyil: kontekst, səhnənin məqsədi və nəticə həlledicidir. Hər montaj qərarında bu suallara qayıt.

## 1. Niyə kəsirik?
- Kəsimin səbəbi olsun: yeni məlumat, reaksiya, diqqətin dəyişməsi, hərəkət, zaman/məkan keçidi. Cümlə bitdi deyə avtomatik
  kəsmə — bəzən danışanın üzündə qalmaq daha çox deyir.
- Sistemdə: `cut` (səsin ən sakit yerinə), `retakes` (təkrar cəhdlər), M07 (çıxış ritmi — pauza və jest qorunur).

## 2. Plan ölçüsü və rakurs
- Ümumi plan məkanı, orta plan hərəkəti, yaxın plan emosiyanı, detal vacib məlumatı göstərir — təsir zəmanəti deyil, seçimdir.
- Eyni ölçülü oxşar iki plan dalbadal — jump cut; qəsdən üslub ola bilər, yoxsa ölçünü dəyiş və ya əlavə kadrla ört.
- Rakurs (bucaq) montajda yaranmır; bir kameradan yalnız plan ölçüsü dəyişir — "fərqli rakurs" kimi təqdim etmə.
- Sistemdə: virtual multikamera (`multicam`, keyfiyyət ehtiyatına görə), M09 plan ölçüsü təsnifatı, B-roll `insert`/`cover`.

## 3. Uyğunluq və davamlılıq
- Hərəkət iki plan arasında davam etsin (match on action), baxış istiqaməti və ekran tərəfi qorunsun (180° qaydası).
- İki nəfərlik söhbətdə kadr danışana onun sözündən bir az əvvəl keçir — tamaşaçı onu "gözləyir".
- Sistemdə: `duo --mode switch` (J-cut üslubunda keçid), `duo --mode split`.

## 4. Zaman və ritm
- Sürətli kəsim həmişə sürətli hekayə deyil; uzun plan gərginlik, qısa planlar monotonluq yarada bilər.
- Ritm kadr, söz, hərəkət, səs və pauzaların birlikdə quruluşudur. Musiqi ritmi ilə kəsim yalnız musiqi əsas olanda (M09).
- Sistemdə: M09 vuruşa kəsim, M10 sürətli sual-cavab, M14 sakit dərs (Reels ritmi yoxdur).

## 5. Keçidlər və səs
- Cut əsasdır; dissolve/fade mənasız bəzək deyil. J-cut (növbəti səs əvvəl), L-cut (əvvəlki səs davam edir) söhbətə axıcılıq verir.
- Səs hər zaman görüntü ilə eyni anda dəyişməməlidir; danışıq kəsimində fon qırılmasın.
- Sistemdə: plan açarı `"jl": {"auto": true, "lead": 0.25}` (fərqli kameralar arasında J-cut; `"cuts"` ilə əl ilə J/L),
  danışıq kəsimində avtomatik 12 ms səs keçidi, musiqi ducking, `voice-clean`, −14 LUFS.

## 6. Rəng, qrafika, effekt
- Rəng düzəlişi (işıq, ağ balansı, planların uyğunluğu) yaradıcı görünüşdən əvvəldir. Dəri tonu təbii qalsın.
- Yazı: oxunaqlı, iyerarxiyalı, kifayət qədər ekranda (~3 söz/s). Effekt zəif quruluşu xilas etmir.
- Sistemdə: `looks` (A–D, işıq bərabərləşdirmə), qrafika qatı, `verify` oxunma müddəti yoxlaması, təbii fon (`bg`).

## 7. Etik montaj
- Danışığı qısaldanda fikri dəyişmə; reaksiyanı başqa hadisəyə bağlama; demədiyi nəticəni yaratma.
- Qiymət, tarix, rəqəm, nəticə, çağırış uydurulmur; ekspertin olmadığı real məkan həqiqi kimi göstərilmir.
- Sistemdə: növ qaydaları (`verify`: danışıqda olmayan rəqəm, mətnin ardıcıllığı), `_review` siyahıları.

## 8. Təhvil və yoxlama
- İxrac edilmiş fayl ayrıca yoxlanır: qara/donmuş kadr, sinxron, səs sıçrayışı, mətn, rəng. Telefonda baxılır.
- Sistemdə: `intake` (material), `verify` (yekun), `words`, `_ig.mp4` yüngül nüsxə, `save`/`restore` arxiv.

## 9. Çəkiliş montajdan başlayır
- Yaxşı material: ümumi + orta + detal + reaksiya (coverage), hər hərəkətdən əvvəl/sonra ehtiyat, 10 s otaq sükutu, 4K, sabit işıq.
- Sistemdə: `types <N> --shoot` — müştəriyə çəkilişdən əvvəl tövsiyə.
