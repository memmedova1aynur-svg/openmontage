---
name: colorblock-office
description: «Color Blocking + Office Style» — moda/dizayn ekspertinin (müştəri kodu «U», moda layihəsi) təsdiqlənmiş Reels montaj stili. İki təsdiqlənmiş format — A) «Pinterest → Bento» reklam (seminar/kurs elanı) və B) «Moda jurnalı + color blocking» (səhifə çevrilən jurnal). İstifadə et: «color blocking», «office style», «ofis stili», «U stili», «jurnal səhifəsi stili», «Pinterest bento», «moda dizayneri üçün reels», bu müştəri üçün yeni video istənəndə.
---

# Color Blocking + Office Style (müştəri «U»)

Bu stil iki müştəri videosunda (U01C «Moodboard sənəti» reklamı, U02 «Təbiətdən ilham al» reklamı) qurulub və agentlik tərəfindən **təsdiqlənib**. Yeni videoda eyni səviyyə tutulur, amma əvvəlkinin kopyası olmur (palitra/obrazlar mövzuya görə dəyişə bilər).

Müştəri adı repoda yazılmır (açıq fork). Müştəri qovluğu: `instagram-clients/<müştəri>/` (gitignore). Yeni sessiyada qovluq yoxdursa, xam çəkilişlər Drive-dan endirilir.

## 1. Vizual dil

**Color blocking palitrası (U01 bazası):**
ultramarin `#2515C9` · NEON YAŞIL `#C6FF00` (əsas vurğu) · lavanda `#D6B9F8` · mürəkkəb `#100C1C` · krem `#F6F1E8` · çəhrayı `#FF249B`.
- Palitra hər videoda eyni olmaq məcburiyyətində deyil. U02-də müştərinin öz lövhəsindən: zeytun yaşılı `#5F6A14`, tünd bənövşəyi `#582147`, püstə `#C9DB73`, açıq yaşıl `#B9D3BE`, vurğu `#6B2553`. Tünd yaşıl üstündür; çəhrayı/mavi/neon dominant olmasın.

**Ofis detalları:** qovluq + `///ad` qulaqcığı, sənəd, sancaq, yapışqan qeyd, kağız sıxacı, siçan kursoru + klik səsi, `///etiket` mono yazılar.

**Şriftlər:** Archivo 900, font-stretch 108% (başlıq/altyazı) · Space Mono Bold (`///etiket`) · Playfair Display Italic/700 (vurğu, ad). Archivo Black İŞLƏTMƏ (Ə hərfi yoxdur). Böyük hərf: i→İ, ı→I.

**Altyazı:** söz-söz, iri Archivo, ağ + qalın mürəkkəb kontur; aktiv söz neon blokda. **Durğu işarələri tam və düzgün** (sual «?», sadalamada vergül, «:» izahdan əvvəl, cümlə sonu nöqtə; «-ıb/-ib» feli bağlamasından sonra vergül QOYULMUR). İngiliscə söz yazılmır (danışanın öz sözü «moodboard» qalır).

## 2. Kompozisiya qaydaları (müştəri düzəlişləri)
- Video ekranın əsas hissəsini tutur; rəng nazik kənarda və kiçik vurğularda. **ÜZƏ HEÇ NƏ GƏLMİR.** Sadə, peşəkar, abartısız.
- Ekranı ikiyə bölmə; stikerlər spikerin sağ-solunda/yuxarı-aşağısında.
- Spikerin arxa fonu dəyişdirilmir (maska ilə studiya fonu peşəkar görünmür).
- Pəncərə/çərçivə içində baş yuxarıda, üstündə artıq boşluq yox; kadraj çox yaxın olmasın (~1.12–1.19×).
- Vizual element yalnız söz deyiləndə çıxır, təkrarlanmır (məs. bəbir yalnız «bəbir» deyiləndə).
- Foto elementlər düzbucaqlı yox, **stiker** (ağ kənarlı kəsim). Uşaqsayağı cizgi fon, real «muzey» fotosu yox.
- Spiker donub qalmasın — yeni səhifə/plan açılanda artıq danışır.

## 3. Rəng və səs
- iPhone HLG → SDR (zscale + tonemap hable), sonra **təbii, neytral** rəng (color_auto ölçülü). Yüksək doyma/«jurnal qreydi» RƏDD edilib. Üzdə sarılıq/qırmızılıq olmasın; canlı, kəskin «peşəkar kamera» görünüşü (yüngül cas/unsharp).
- Səs: DeepFilterNet (DFN 12), −14 LUFS. Cümlələr tam; söz ortasında kəsim yox; yapışıq yerlərə qısa nəfəs pauzası.
- Musiqi mütləq var (musiqisiz variant YALNIZ istəniləndə). U01: midnight-funk. U02: təbiət mövzusunda quş/meşə səsi (≈6 s, aydın eşidilən).
- SFX: klik (kursor), whoosh (keçid), pop (stiker).

## 4. Format A — «Pinterest → Bento» reklam (U01C)
1. Hook: yuxarıda sonsuz Pinterest skrolu (masonry, 4 sütun) + `ŞƏKİL: 12…999+` sayğacı; «yorulmusan?» anında **«DAYAN»** (ultramarin fon, neon yazı, `///skrolinq_bitdi`).
2. Spiker + laptop B-roll növbələşir; ad lövhəsi `SPİKER · Ad Soyad` (Playfair 700, kursiv YOX).
3. «…lazımdır:» deyiləndə ekran 2×2 rəng bloklarına (bento) bölünür; hər xana bir söz: İLHAM MƏNBƏYİ / TEKSTURA / RƏNGLƏR / TARAZLIQ (moodboard foto kəsikləri ilə).
4. CTA: çəhrayı düymə «SEMİNARA QOŞUL ↗» + kursor klik + `///linkə_keçid`.
5. Son kart: bento-kolaj (neon blok «MOODBOARD SƏNƏTİ», foto xanalar, çəhrayı ad kartı + tarix/format), sonra brend loqo animasiyası.
Skriptlər: `templates/styles/colorblock-office/scripts/` → `base_u01.py` (baza kəsim, B-roll əvəzləmə, nəfəs pauzaları), `u01_common.py` (söz vaxtları, altyazı, FIX durğu lüğəti), `gen_u01_C.py` (HyperFrames səhnə), `rqBC_fast.sh` + `u01C_nobase.sh` (render → loqo sona → QC).

## 5. Format B — «Moda jurnalı + color blocking» (U02)
1. Hər plan dəyişəndə jurnal səhifəsi **sol kənardan bütöv** çevrilir (ortadan yox — üz bölünməsin); 3–4 səhifə kifayətdir, çox tez fırlanmasın.
2. Səhifələr: editorial başlıq + color-block xanalar + moda kolajı; ağ yerlərə yazı; kiçik real paltar fotosu (fonu silinmiş stiker).
3. Mövzu obrazları sözə bağlı: yarpaq/meşə (+ meşə səsi), püstə stikeri, bəbir (yalnız deyiləndə), girişdə yeriyən qırmızı cizgi xərçəng (sevilib); son kartda xərçəng cizgiləri YOX.
4. Son kart: tarix/saat (məs. «SAAT 15:00»), «YARADICI №02» kimi ifadə yox.
Skriptlər: `base_u02.py`, `cb_u02.py` (color-block fonlar — hamısı None, fon dəyişmir), `gen_u02j.py` (jurnal səhnələri, `U02_VAR` palitra variantı, ghost səhifə çevrilməsi), `rq_u02j.sh` (render + QC).

## 6. İş qaydası
- Montaj darvazası (`montaj/IS_AXINI.md`) qüvvədədir: `python -m montaj.gate start <müştəri> <video> --type 3` → concept.md → cut_report.md → render → `qc_render.py` + gözlə baxış → `gate deliver`.
- Skriptlərdəki `{MÜŞTƏRİ}`, `{SPİKER_ADI}`, `{BREND}`, `{musteri}` yer tutucularını yeni işin real dəyərləri ilə əvəz et; `/tmp/claude-0/...` yollarını təzə skretç qovluğuna yönəlt.
- Assets: Archivo / Space Mono Bold / Playfair (`/root/.fonts/` yoxdursa Google Fonts-dan endir), moodboard foto kəsikləri müştərinin öz şəkillərindən.
- Hər yeni video əvvəlkinin kopyası olmur; format seçilir, palitra və obrazlar mövzuya uyğunlaşdırılır.
