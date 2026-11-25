# Edit Director — Rejissor qaydası (bütün müştərilər, bütün video növləri)

**Nə vaxt:** hər yeni video / reklam / referans linki üçün montajdan ƏVVƏL. Məqsəd: hər videoya mövzusuna uyğun edit konsepti seçmək — "oturub danışır, düz edit" avtomatizmi olmasın.

## Axın (qısa, token az)
1. `python -m montaj.doctor` (sessiya başında bir dəfə; çatışan varsa `--fix`). Soruşma, "yoxdur" demə — özün qur.
2. Brif: `python -m montaj.director brief --pid <layihə> --client <profil> [--goal ...]` (siqnallar + müştəri + B-roll uyğunları). Referans video/linkdirsə əvvəl `skills/meta/video-reference-analyst.md`.
3. **Konsepti 5–8 sətirdə yaz:** məqsəd → edit ailəsi (niyə) → səhnə/ritm planı → hansı elementlər (kart, kinetik tipoqrafiya, B-roll, qrafik, marker) və hansı mənada → müştəri qaydaları (palitra, musiqi). Uzun hesabat, alternativ variantlar, storyboard göndərmə (profil istəyənə qədər).
4. Qur: Crystal Clear rəng (avtomatik), `framefix` kadraj, montaj, texniki + vizual yoxlama (`aligned_check`, `delivery_qc`), təqdim et.

## Edit ailələri → alətlər
| Ailə | Nə vaxt | Alətlər |
|---|---|---|
| Təmiz danışıq | ifa özü güclüdür, mövzu sadə, emosiya/etibar vacibdir | altyazı (yüngül), nadir vurğu; B-roll yox |
| Info kartları | rəqəm, termin, siyahı, addım | `fx.html`: tag/marker/ring/checklist/graph; altyazı kartı |
| B-roll | mücərrəd/vizual anlayış, hekayə, atmosfer | `montaj.library` (musiqi/B-roll), `add-broll`; yalnız məzmunu gücləndirəndə |
| Kinetik tipoqrafiya | hook, açar anlayış, reklam vurğusu | `talk.py` `cards`, `fx.html` marker/tag |
| Qarışıq | əksər videolar | yuxarıdakıların yığımı; eyni ardıcıllığı təkrarlama |
Düz edit yalnız əsaslandırılıb seçilir ("niyə bu video üçün daha güclüdür"). Hər video fərqli konsept ola bilər; seriyada vizual bağlılıq qalır, kopya olmasın.

## Standartlar (ümumi)
- **Rəng:** Adaptive Crystal Clear (`UMUMI_QAYDALAR.md`) — filtr deyil; yüngül kəskinlik/canlılıq, dəri təbii, ağ ağ, qara qara.
- **Kadraj:** `framefix` — əyrilik düzəlir; oturduğu xəttdən kəsilir (ayaq/diz görünürsə omba+6%); omba masa ilə örtülürsə kəsmə yoxdur, masa aşağıda görünə bilər; başın üstündə ~10% boşluq (artıq boşluq yox; kart üçün yer lazım olan müştəri profili artıra bilər).
- **Musiqi:** yalnız müştəri profilindəki `music_policy` ilə. Qayda yoxdursa — musiqisiz, soruşma. Seçim: `python -m montaj.library search "<əhval>" --kind music`.
- **Təhlükəsiz sahə:** `UMUMI_QAYDALAR.md` (Instagram).
- **Məzmun:** danışılanın mənasını dəyişmə; elmi məlumat/statistika uydurma.
