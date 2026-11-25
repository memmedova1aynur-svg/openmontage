# Görünüş qaydaları — müştəri üzrə "imza" (fərqlənmək üçün)

Məqsəd: hər müştərinin videosu başqa müştəridən və hazır-şablon videolardan dərhal seçilsin.
Rəng, şrift, musiqi, kart və qadağalar müştərinin profilindən gəlir
(`templates/expert-reels/experts/<müştəri>.json`, `cautions`); bu sənəd həmin qaydaların üstünə **imza elementi** əlavə edir.
Profil və bu sənəd ziddiyyət təşkil edərsə, profil (istifadəçinin son sözü) üstündür.

## Ümumi qaydalar (bütün müştərilər)
1. **Bir imza hərəkət.** Hər müştəri üçün yalnız bir təkrarlanan hərəkət/keçid (aşağıda). Hər kartı ayrı animasiya etmə.
2. **Kart az, kadr çox.** Kart yalnız mənanı daşıyanda (açar anlayış, rəqəm, CTA). Danışan üz və real kadr əsasdır.
3. **Ritmi poz.** Bir yerdə uzun plan, sonra sıx kəsim; hər 2 s kəsmə yoxdur (`KINO_DILI.md` §1, §4).
4. **Musiqi trenddən kənar.** Müştərinin tonuna uyğun, sözsüz, danışıqda aşağı; hər videoda eyni trend səs olmasın.
5. **Test sualı.** Təhvildən əvvəl: "Bu video başqa müştəri üçün də ola bilərdimi?" Bəlidirsə, imza elementini gücləndir.
6. **Pozma.** Qadağalar (rəng, kadraj, üzə kart qoymamaq, fonu bulanıqlaşdırmamaq) profildə qalır və heç vaxt imza naminə pozulmur.

## Xəyyam Həsənov
**Mənbə:** `xeyyam-huseynov.json` (rəng/kadraj qaydaları orada; laym QADAĞANDIR).

| Element | Qayda |
|---|---|
| Rəng | tünd meşə yaşılı `#0F3B2E`, vurğu yarpaq yaşılı `#6CC57E`, ağ kartlar; sarı/narıncı/mavi/bənövşəyi yox |
| Şrift | Montserrat qalın başlıq; vurğu sözü üçün bəzən italik serif |
| **İmza hərəkət** (təklif) | Vurğu sözü "marker" effekti ilə yaşıl işıqlanır (soldan sağa 0.4 s). Başqa heç nə hərəkət etmir. |
| Kart dili | Ağ yuvarlaq künclü kart + yaşıl "pill" etiket. Tam ekran kartlar 3–5 s, səs davam edir |
| Yazı | İri, qalın, sola düzlənmiş, aşağıda; altında qısa yaşıl xətt. Üzə/ağıza/başa/ələ heç vaxt |
| Ritm | Danışan hissə 6 s-dən uzun deyil; ortada bir "nəfəs" kadrı (detal/B-roll, sakit) |
| Musiqi | Sözsüz, sakit, premium; yalnız CC0; ən sonda seçilir; piano/yavaş yox (ümumi qayda) |
| Səs | Tipoqrafiyada çox yüngül tick; whoosh az; səsə artıq emal yox |
| Axın | hook sual → tam ekran tipoqrafiya → açar anlayış (krem/ağ kart) → ziddiyyət → həll → CTA |
| Fərq testi | Yaşıl marker + ağ yuvarlaq kart olmadan video tanınırmı? Tanınmırsa, markeri gücləndir |

## Ay Gün
**Mənbə:** repoda `Ay Gün` üçün profil faylı yoxdur. İstifadəçidən aşağıdakıları alıb doldurmaq lazımdır:

| Element | Qayda |
|---|---|
| Rəng | _(istifadəçi deyəcək: əsas rəng, vurğu, fon, qadağan rənglər)_ |
| Şrift | _(...)_ |
| **İmza hərəkət** | _(bir hərəkət seç: məs. söz altından xətt çəkilir / kart yuxarıdan süzülür / fade-blur keçid)_ |
| Kart dili | _(...)_ |
| Yazı | _(yer, ölçü, düzlənmə)_ |
| Ritm | _(...)_ |
| Musiqi | _(janr, qadağalar, mənbə/lisenziya)_ |
| Fərq testi | _(Xəyyamdan və başqa müştərilərdən nə ilə seçilir?)_ |

Doldurduqdan sonra `templates/expert-reels/experts/` altında profil faylı yaradılmalıdır ki, sistem `--client` ilə oxusun.

## Yeni imza əlavə etmə qaydası
Bir müştəri üçün yalnız bir həftədə bir element dəyiş (rəng, ritm, musiqi və s.), nəticəni profilin `history`/`cautions` hissəsinə yaz ki, nəyin işlədiyi bilinsin.
