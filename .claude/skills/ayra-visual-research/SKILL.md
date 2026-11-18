---
name: ayra-visual-research
description: AYRA Real Visual Asset System — cover, post, karusel, poster, reklam, storyboard, vizual konsept və video montaj tapşırıqlarında AVTOMATİK işə düşür. Mövzunun real foto/obyekt (oyuncaq, çanta, kitab, uşaq otağı, tədris materialı, məişət əşyası) tələb edib-etmədiyini müəyyən edir; tələb edirsə əvvəl lokal kitabxanada, sonra Openverse (Wikimedia Commons, Flickr, StockSnap, Rawpixel) üzərindən kommersiya+dəyişdirmə icazəli real şəkil tapır, contact sheet-ə baxıb seçir, yükləyir, fonunu silir (rembg), metadata/lisenziya yazır və dizayna yerləşdirir. İstifadə et: 'real şəkil', 'oyuncaq', 'foto tap', 'fonu sil', 'stok', 'mockup', və istənilən dizayn/montaj işindən əvvəl.
---

# AYRA Visual Research

Dizayn sırf tipoqrafiya + formalarla «şablon/AI havası» verirsə, səbəb çox vaxt real materialın olmamasıdır. Bu skill həmin boşluğu doldurur. İstifadəçi hər dəfə «şəkil tap» deməməlidir.

## 0. Qərar: real material lazımdırmı?
- Mövzu konkret obyekt/məkan/fəaliyyət haqqındadırsa (oyuncaq, çanta, qida, kitab, otaq) → **BƏLİ**.
- Mövzu emosiya, sitat, mif, sual, sırf rəqəm üzərində qurulubsa və tipoqrafik həll daha güclüdürsə → foto əlavə etmə. Səbəbini bir cümlə ilə qeyd et.

## 1. Protokol (hər dizayndan əvvəl)
1. Mövzu + auditoriya + vizual ideya (bir cümlə).
2. Lazım olan real obyektlər siyahısı.
3. İngiliscə 3–6 sorğu (Openverse ingiliscə indeksləyir; azərbaycanca sorğu nəticə vermir).
4. Axtarış (əvvəl lokal kitabxana avtomatik yoxlanır):
   ```bash
   S=.claude/skills/ayra-visual-research/scripts
   python3 $S/vr_search.py "wooden toy" "toy blocks" --source rawpixel --out <scratch>/vr/<mövzu> --n 12 --min-width 600
   python3 $S/vr_search.py "backpack" "water bottle" --source stocksnap --out <scratch>/vr/<mövzu2>
   ```
   Ən yaxşı mənbələr (praktikada): `rawpixel` və `stocksnap` (CC0, təmiz məhsul fotoları), `flickr` (çox, keyfiyyət qarışıq), `wikimedia` (yalnız 960/1280 px thumbnail-lar yüklənir).
5. **`sheet.jpg`-ə BAX.** Fayl adına/başlığa güvənmə — başlıq «toys», şəkil Toys“R”Us mağazası ola bilər. Ən az 3 alternativ müqayisə et.
6. Seç + yüklə + (lazımsa) fonu sil:
   ```bash
   python3 $S/vr_fetch.py <scratch>/vr/<mövzu> 4 25 13 --folder montessori --topic "taxta oyuncaqlar 2 yaş" --cutout
   ```
   → `assets/ayra-library/<folder>/<id>.jpg`, `product-cutouts/<id>_cut.png`, `licenses/<id>.json`, `index.json`.
7. Kəsilmiş PNG-ni dizayna yerləşdir (HTML `<img>` + `filter:drop-shadow`), render et (`templates/ayra/engine/ayra_design.py render`), nəticəyə BAX.
8. Kəsimi yoxla: kənarlarda fon qalığı, kəsilmiş hissə, bulanıq kənar → başqa namizəd seç və ya foto kimi (fonlu) çərçivədə istifadə et.
9. CC BY / BY-SA şəkillərdə `attribution` sətrini caption-a və ya ilk şərhə yaz; BY-SA dəyişdirilmiş şəkil eyni lisenziya ilə paylaşılır — mümkünsə CC0/PDM seç.

Tək şəkil üçün: `python3 $S/vr_cutout.py giriş.jpg çıxış.png` (obyekt: `isnet-general-use`; insan: `--model birefnet-portrait`).

## 2. Lisenziya qaydaları
- Yalnız `cc0`, `pdm`, `by`, `by-sa` (kommersiya + dəyişdirmə icazəli). `vr_lib.OK_LICENSES` bunu məcburi edir.
- Google Images / Pinterest — yalnız ilham; oradan şəkil yekun dizayna girmir.
- Pexels / Unsplash / Pixabay API-ləri açar tələb edir (401/400) — açar yalnız istifadəçi təsdiqi ilə, `request_credential` vasitəsilə. Brauzerlə əl ilə yüklənən fayl gəlsə, mənbə və lisenziyanı `licenses/`-ə əl ilə yaz.
- Kaboompics serverdən bloklanır (403). Poly Haven (CC0 tekstura/HDRI), SVG Repo, Mockup World, Unblast saytları açılır — lisenziyanı hər faylda ayrıca yoxla.
- Görünən brend loqosu olan məhsul (məs. çanta üzərində marka) — mümkünsə başqa namizəd seç və ya loqonu kadrdan çıxar.

## 3. Kitabxana
`assets/ayra-library/` — `real-photos, product-cutouts, education, montessori, toys, motherhood, books, mockups, textures, icons, licenses` (+ `index.json`).
- Yalnız açıq lisenziyalı stok. **Müştəri portretləri buraya düşmür** (`vr_fetch.py` `client-portraits`-i rədd edir) — onlar `instagram-clients/<müştəri>/`-dədir (gitignored).
- Hər yeni işdə əvvəl kitabxana axtarılır (`vr_search.py` bunu avtomatik edir).

## 4. Qadağalar
- Müştərinin üzünü/bədənini dəyişmək, AI ilə müştəri şəkli yaratmaq.
- Uydurma məhsul vizualı, icazəsiz şəkil.
- Uyğun şəkil tapılmadısa gizlətmə: alternativ (tipoqrafik/ikonlu) kompozisiya qur və çatışmayan materialı istifadəçiyə yaz.
- Real şəkillər tipoqrafiyanı əvəz etmir: editorial tipoqrafiya + real obyekt + brend rəngi birlikdə.

## 5. Test vəziyyəti (16.11.2026, bu mühit)
| Alət/mənbə | Vəziyyət |
|---|---|
| Openverse API (açarsız) | işləyir — axtarış + metadata |
| Rawpixel / StockSnap / Flickr şəkil yükləmə | işləyir |
| Wikimedia Commons | API 429 (rate-limit); şəkillər yalnız 960/1280 px thumbnail ilə yüklənir |
| Pexels / Unsplash / Pixabay API | açar tələb edir |
| Kaboompics | 403 |
| rembg (isnet-general-use, birefnet-portrait) | lokal işləyir |
| Pillow | işləyir |
| Playwright + Chromium | işləyir (render, ekran görüntüsü) |
| Sharp (Node) | quraşdırılır, amma əlavə dəyər vermir — Pillow istifadə olunur |
| Playwright MCP | quraşdırılmayıb (Playwright Python artıq eyni işi görür) |

## Asset Curator meyarları (Creative Intelligence §6)
Adına uyğun ilk şəkil yox — vizual yoxla: forma/estetika · rəng və material · foto keyfiyyəti (kəskinlik, ≥ 600px obyekt) · işıq · rakurs (bir dizaynda eyni rakurs: ya hamısı üstdən, ya hamısı yandan) · fon (təmiz kəsilə bilirmi) · brend dili · digər obyektlərlə harmoniya.
Sahəyə görə:
- **Uşaq inkişafı / Montessori**: təbii material (taxta, parça, kağız), sakit rəng; parlaq plastik və turist/böyük çantası yox; uşaq üçün təhlükəli görünən əşya (yumurta, kiçik hissələr) yox.
- **Psixologiya**: insan jesti, əllər, gündəlik məkan; dramatik stok emosiya («başını tutan qadın») yox.
- **Pedaqogika / təlim**: real sinif materialı, dəftər, lövhə; korporativ stok yox.
- **Karyera / biznes**: iş masası, sənəd, real mühit; «əl sıxan kostyumlular» yox.
Ən az 3 alternativ müqayisə et. Keyfiyyətsiz şəkli fonundan ayırmaq onu keyfiyyətli etmir — uyğun tapılmırsa obyekti çıxar və ya kompozisiyanı dəyiş, istifadəçiyə yaz.
Ton uyğunlaşdırma icazəlidir (parlaqlıq, doyma ±30%, ağ balans) — obyektin formasını dəyişmək yox.

## Asset keyfiyyət alətləri (`scripts/asset_fx.py`)
- `qc cut.png` — maska yoxlaması (örtük, yarımşəffaf kənar, halo, kəskinlik, ölçü). **FAIL olan kəsim dizayna qoyulmur**: başqa namizəd seç, ya fotonu kəsmədən tam kadr/pəncərə kimi işlət, ya da ağ fonlu fotonu `mix-blend-mode:multiply` ilə açıq fona otur (maska lazım deyil).
- `tone` — brend rənginə yumşaq ton/doyma/kontrast uyğunlaşdırma (forma dəyişmir). `shadow` — kontakt + mühit kölgəsi (obyekt «yapışdırılmış» görünməsin). `grain` — yalnız konsept tələb edəndə. `subject` — «mətn subyektin arxasında» üçün ön qat (orijinalla eyni ölçü).
- Foto mətnlə ziddiyyət təşkil etməməlidir (dolu boşqab + «boşqabı silir» olmaz) — ya mətni, ya fotonu dəyiş.
- Tanınan uşaq/insan üzü olan stok foto: CC0 olsa da model razılığı məlum deyil — istifadəçiyə qeyd et.
