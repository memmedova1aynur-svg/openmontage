# Referans öyrənməsi

Məqsəd: referans videonun ARXASINDAKI qərarları öyrən, kopyalama. Alət: `python -m montaj.refstyle` (yerli, pulsuz, ffmpeg).

1. `analyze <video> --name <ad> --sheet-dir <qovluq>` → ritm ölçüləri (kəsim sayı, orta/median plan, ilk 3 s tempi, 1 s-dən qısa planların payı, üçdə bir üzrə kəsim),
   səs (səs səviyyəsi, sükut) və kontakt şəkli. Şəkil repoya yazılmır.
2. Kontakt şəklinə bax və `decide <ad> --set hook_method="..." --set typography="..."` ilə qərarları yaz:
   hook_method, typography, transitions, broll_use, composition, sound, retention, ad_principles. Yalnız gördüyünü yaz; təxmini "?" ilə işarələ.
3. İstifadəçiyə qısa göstər; **o təsdiq edəndən sonra** `approve <ad>`. Təsdiqsiz qərar qayda deyil; `decide` hər dəyişiklikdə təsdiqi sıfırlayır.
4. Planlaşdırmada yalnız təsdiqlənənlər (`approved_targets()`) istifadə olunur: ritm hədəfi (məs. orta plan) və qərarlar — **fərqli mövzuya fərqli icra** ilə, kopya yox.
5. Referans video, kadrları və transkripti repoya yüklənmir; yalnız `montaj/references/<ad>.json` (ölçülər və qərarlar).
