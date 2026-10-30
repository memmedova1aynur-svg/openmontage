# Expert Reels Director

## When to Use

Use this when the user sends a Google Drive link to footage of an expert (coach,
trainer, consultant) and wants an Instagram Reel.

- **Classification and edit approaches:**
  `templates/expert-reels/VIDEO_TYPES.md` holds the 14 video types, the M01-M13
  approaches and the type → approach map. Read it before planning.
- **Talking edits:** `templates/expert-reels/README.md` is the operating manual
  for the talking edits that the template renders (M01-M05 and M13).

This skill does not replace the talking-head stage directors. It replaces their
scene_plan, assets, edit and compose stages with the template's flow:
spec → `build_edit.py` → `render.sh`.

The rules below are written in Azerbaijani because the user works in it.

## İş axını

### 1. Drive linki gələndə

Hər link yeni montaj tapşırığıdır.

- **Yükləmə.** `drive.usercontent.google.com/download?id=…&confirm=t` ilə faylı
  `projects/<id>/assets/source/` qovluğuna endir.
- **Yoxlama.** ffprobe ilə bunları yoxla: müddət, ölçü, istiqamət (fırlanma metadatası daxil), fps, kodek, HDR, səs (kanallar, tezlik). Çəkiliş tətbiqinin adına görə yox, faylın öz xüsusiyyətlərinə görə işlə. Orijinal fayl dəyişdirilmir.
- **Transkripsiya.** Danışıq varsa, `transcriber` aləti ilə et
  (`large-v3`, `az`). Mənbə timecode-larını saxla.
- **Əvvəlki təhlil.** `projects/<id>/artifacts/` qovluğunda transkripsiya və
  ya qeyd varsa, yenidən istifadə et.
- **Təhlil.** Video növünü (`VIDEO_TYPES.md`), əsas fikri və məqsədi müəyyənləşdir.
  Kitabxanadan bir əsas montaj yanaşması seç; lazım olsa, bir əlavə yanaşma qoş.
- **Müştəri profili.** Müştərinin saxlanmış profili varsa
  (`templates/expert-reels/experts/<id>.json`), onu tətbiq et. Kim olduğundan
  əmin deyilsənsə, təxmin etmə, neytral üslub seç.
- **Tarixçə.** Profildəki `history` bölməsinə bax. Eyni girişi, yazı qutusunu,
  düzülüşü və effekt ardıcıllığını avtomatik təkrarlama. Eyni məkan və geyimdə
  çəkilmiş ardıcıl videolarda altyazı və vurğu üslubunu dəyiş.
- **Bir linkdə bir neçə fayl.** Hər faylı ayrıca təsnif et. Onların bir video
  üçün material olduğu aydın deyilsə, birləşdirməzdən əvvəl soruş.

### 2. Qısa analiz və storyboard

Montaj seçimi belə qurulur: müştərinin vizual dili (`experts/<id>.json`) + video növü + danışığın
mövzusu + mövcud material. Storyboard **yazılı və şəkillidir**: əsas anlar üçün nümunə kadrlar
(`STILL=<frame> render.sh`) göstərilir. Profildə rəng `derived` kimi qeyd olunubsa, seçilən çalarlar
storyboardda "təklif olunan çalar" kimi yazılır, müştərinin kodu kimi yox. Profilin `cautions`
bölməsi standart qaydalardan üstündür.

Analiz bu formada verilir:

```
Video növü: …
Əsas fikir və ya məqsəd: …
Seçilən montaj: M.. (+ M..)
Təxmini yekun müddət: …
Mənbə → çıxış: 1080×1920 30fps → 1080×1920 (və ya başqa format, səbəbi ilə)
```

Səs effekti planlaşdırılırsa, storyboardda göstərilir; təsdiqlənməyən səs effekti işlədilmir.

Sonra qısa storyboard gəlir. Sütunlar:
mənbə aralığı → yekun hissə → görüntü qərarı → dəqiq mətn/qrafika → səs.

- Yalnız həmin video üçün lazım olan sütunları saxla.
- Eyni davranışı olan ardıcıl hissələri bir sətirdə qruplaşdır.
- Esse yazma, texniki əmrləri göstərmə.
- Lazım olsa, nümunə kadrlar çıxarıb göstərmək olar.

Video növünə görə storyboardda nə göstərilir:

| Növ | Storyboardda nə olmalıdır |
|---|---|
| Hazır mətnli reklam (3) | Təsdiqlənmiş ardıcıllıq olduğu kimi qalır; ayrıca hook seçilmir. Vizual vurğular, əlavə material və son ekran göstərilir. |
| Ekspert danışığı (1) | Uyğun giriş varsa, saxlanılır. Yoxdursa, materialdan hook mənbə timecode-u ilə təklif olunur. |
| Sual-cavab (2) | Sualın giriş kimi kifayət edib-etmədiyi yazılır. Sualın necə veriləcəyi və cavabın necə qısaldılacağı göstərilir. |
| Uzun seminar (4) | Müstəqil anlaşılan çıxarışlar qısa seçim siyahısı kimi verilir. Hamısı avtomatik render edilmir. |
| Praktik nümayiş (4/6) | Qorunacaq addımlar, intonasiya, jest və pauzalar göstərilir. |
| Tədbir icmalı (5/7) | Kadr ardıcıllığı, musiqi, real səslər və mümkün yavaşlatmalar göstərilir. |
| Yumorlu video (10) | Zarafat anları, komedik pauzalar və seçilmiş effektlər göstərilir. |
| Səsləndirməli video (8) | Hər səs hissəsinə uyğun görüntü bağlanır. |
| Nağıl və animasiya (9) | Səhnələr, obraz və vizual üslub nümunəsi təsdiqə daxil edilir. |
| Hərəkətli kartlar (12) | Hər səhifənin dəqiq mətni, ardıcıllığı və oxuma müddəti göstərilir. |
| Modul təlim dərsi (15) | Aşağıdakı "Uzun təlim dərsi" bölməsinə bax. |

Məqsəd aydın deyilsə və seçim nəticəni ciddi dəyişəcəksə, bir qısa sual ver.
Adi montaj seçimlərini istifadəçiyə həvalə etmə.

### 3. Storyboard təsdiqi (məcburi qapı)

- **Başlamazdan əvvəl.** "Təsdiq", "başla" və ya eyni mənalı cavab gəlməyincə
  yekun montaja və renderə başlama. Bu müddətdə təhlil, fayl hazırlığı, kəsim
  və nümunə kadrlar olar.
- **Düzəliş istənərsə.** Planın yalnız dəyişən hissəsini qısa yenilə. İstifadəçi
  düzəlişlə birlikdə "başla" demirsə, yeni təsdiqi gözlə.
- **Əvvəlki qaydalarla ziddiyyət.** Bu qapı əvvəlki "heç nə soruşma, bitir və
  göndər" göstərişindən və köhnə transkripsiya təsdiqi qaydasından üstündür.
  Transkripsiya mətni storyboardun bir hissəsi kimi təsdiqlənir.

### 4. Təsdiqdən sonra icra

- Təsdiqlənmiş məna, ardıcıllıq və vizual yanaşma əsasdır. Xırda texniki
  qərarlar üçün yenidən sual vermə.
- Mövcud skriptlərdən və komponentlərdən istifadə et: `cut_takes.py`,
  `align_words.py`, `setup_workspace.sh`, `build_edit.py`, `render.sh`, `src/scenes`.
- Yeni modulu yalnız çatışmayan və təkrar istifadə ediləcək ehtiyac üçün yaz.
  Onu şablonda saxla və git-ə yüklə.
- Transkripsiyanı, təhlili və işləyən komponentləri səbəbsiz yenidən yaratma.
- Yeni ödəniş, hesab bağlantısı və ya əlavə giriş avtomatik edilmir.
- Planın əsas yaradıcı qərarı dəyişməli olsa, qısa bildir və təsdiq al.
- **Pauzalar.** Danışıqda qalan pauzalar ~0.25 s-ə qədər qısaldılır: `denoise.sh`-dan sonra `tighten.py projects/<id>` (spec və söz vaxtlarını özü yeni kəsimə köçürür), sonra `cut_takes.py`, `setup_workspace.sh`, `build_edit.py`, `render.sh`, `denoise.sh`. Sondakı 1 s saxlama toxunulmur.

### Mənbə keyfiyyəti və ixrac

- **Çıxış ölçüsü mənbədən asılıdır.**
  - Şaquli 1080×1920 mənbə 1080×1920 kimi ixrac olunur.
  - Şaquli 4K mənbə 2160×3840 kimi ixrac olunur.
  - Aşağı ölçülü görüntü heç vaxt 4K-ya böyüdülmür.
  - `setup_workspace.sh` ölçünü `public/render.json` faylına yazır, `render.sh` ona əməl edir.
- **Ölçü və fps** səbəbsiz dəyişdirilmir. Mənbə 30 fps deyilsə, storyboardda qeyd edilir; şablon 30 fps ilə render edir.
- **Üfüqi dərs** üfüqi qalır, avtomatik şaquli Reels-a çevrilmir.
- **Yaxınlaşdırma və yenidən çərçivələmə** mənbənin ehtiyatına görə seçilir: 1080p mənbədə ~1.10-dan çox zoom kəskinliyi azaldır.
- **İstiqamət.** Görüntü avtomatik güzgülənmir və çevrilmir. Fırlanma metadatasını ffmpeg özü tətbiq edir. İstiqamətdə şübhə varsa, storyboardda qeyd edilir.
- **Güzgü görüntü.** Ön kamera / Edit tətbiqi ilə çəkilmiş video tərs ola bilər. Əvvəl "indiki / çevrilmiş" yan-yana kadr göstərilir, təsdiqdən sonra `hflip` ilə çevrilir (`assets/source/flipped.mp4`).
- **Test hissəsi.** İstifadəçi "X saniyəyə qədər test" deyirsə, o hissə tam çıxarılır; ən son tam variant saxlanılır.
- **Təhvil faylı** (`*_ig.mp4`) mənbə ilə eyni ölçüdədir, HEVC kodekindədir və ~44 MB ilə məhdudlaşır. 1080p videoda bu, keyfiyyət itkisi demək deyil.
- **Başqa format** yalnız istifadəçi istəsə və ya növ tələb etsə seçilir. Seçim storyboardda yazılır.

### Musiqi və səs

- **Fon musiqisi əlavə edilmir.** Lazım olsa, istifadəçi CapCut-da özü əlavə edir.
- **Səs effekti** yalnız storyboardda göstərilib təsdiqlənsə işlədilir. `build_edit.py`-də standart `sfx_level` dəyəri "none"-dur.
- **Əvvəlcədən kəsilmiş hissələr.** Faylda əvvəlcədən kəsilmiş hissələr ola bilər; birləşmə yerlərini yoxla.
- **Danışıq səsi** aydın və təbii saxlanılır, səviyyə −16 LUFS-ə bərabərləşdirilir.
- **Arxa fon səsi** (kafe, çəngəl-bıçaq, musiqi) olanda və ya istifadəçi istəyəndə `denoise.sh <id>` işlədilir: DeepFilterNet3 (`deep-filter` binary, GitHub release) səsi təmizləyir, şəkil yenidən render edilmədən səs dəyişdirilir.

### Uzun təlim dərsi (növ 15, M14)

**Storyboardda** qısa şəkildə bunlar olur:
- dərsin əsas mövzusu və təxmini yekun müddəti;
- çıxarılması təklif olunan hissələr, mənbə vaxtları ilə;
- şübhəli və mənaya təsir edə biləcək kəsimlər (tibbi və texniki ifadələr təsdiqsiz seçilmir);
- altyazı: videoya yazılan və ya ayrıca SRT/VTT, ya da hər ikisi;
- izahlı elementlərin dəqiq mətni və vizualı (varsa);
- ad–peşə yazısı: yalnız istifadəçi ad, soyad və peşəni verəndə. Storyboardda 2–3 vizual variant şəkil kimi göstərilir, seçilən variant dərsin əvvəlində çıxır və sonra yox olur;
- mənbə və çıxış ölçüsü (üfüqi qalır);
- montaj və render üçün real müddət.

**Qaydalar:**
- Kursun bütün bölümləri eyni üslubdadır: altyazı və elementlər. Seçilən üslub ekspert profilinə yazılır.
- Hər bölüm ayrıca MP4 kimi təhvil verilir. SRT/VTT faylı varsa, onunla birlikdə verilir.
- Reels üçün olan 10 dəqiqəlik hədəf burada tətbiq edilmir. Real müddət storyboardda bildirilir.

### 5. Vaxt hədəfləri (zəmanət deyil)

- **Linkdən storyboarda:** ~5 dəqiqə.
- **Təsdiqdən yoxlanmış fayla:** ~10 dəqiqə.

Endirmə, uzun transkripsiya, animasiya və ya 4K render hədəfə sığmırsa, real
müddəti storyboardda yaz. Vaxta çatmaq üçün məna və keyfiyyəti səssizcə azaltma.

Bu konteynerdə ölçülmüş müddətlər (4 CPU, GPU yoxdur):

| İş | Müddət |
|---|---|
| ~1 dəq. materialın transkripsiyası (`large-v3`) | 1-2 dəq. |
| ~1 dəq. videonun 4K render + təhvil faylı | ~15-20 dəq. |
| ~1 dəq. videonun 1080×1920 render + təhvil faylı | təxminən 4 dəfə tez (ölçülməyib) |

### 6. Yekun yoxlama və təhvil

İxrac edilmiş faylda bunları yoxla:

- təsdiqlənmiş plana uyğunluq;
- danışığın mənası və vacib şərtlər;
- kəsimlər, səs və görüntünün sinxronu, səs səviyyəsi (−16 LUFS);
- altyazı, adlar, terminlər və rəqəmlər;
- mətnlərin yeri, fokus, rəng və görüntü problemləri (kadrlar çıxarılıb baxılır).

Baxılmayan və ya yoxlanmayan hissə yoxlanmış kimi göstərilmir.

Təhvildə yalnız bunlar verilir: SendUserFile ilə hazır MP4 (`*_ig.mp4`, mənbə
ölçüsündə HEVC, ≤ ~44 MB, telefona yüklənir), yekun müddət və varsa vacib məhdudiyyət.
Dərslərdə SRT/VTT faylı varsa, o da verilir.

Sonra yanaşma (M..) və əsas vizual qərarlar ekspert profilindəki `history`
bölməsinə yazılır.

## Sabit texniki qaydalar

- Videolarda müştərinin adı, loqosu və Instagram adı yazılmır (2026-10-27). İstisna: istifadəçi təlim dərsi üçün ad, soyad və peşəni verərsə, ad–peşə yazısı (yuxarıdakı qayda).
- Şrift: hər müştəri üçün Montserrat (300–900; mövzuya görə nazik, medium və ya qalın).
  Bəzən vurğu üçün əl yazısı şrifti Caveat (`FONT_HAND`) istifadə olunur; Azərbaycan
  hərflərini dəstəkləyir. Başqa şrift yalnız ə, ğ, ı, ş, ç, ö, ü yoxlanandan sonra əlavə olunur.
- Rəng kodu olmayan müştərilər üçün rəng ailəsindən çalar seçmək kifayətdir; dəqiq kod tələb olunmur.
- Altyazı Montserrat şrifti ilə yazılır. Mətn Instagram interfeysi zonasının
  üstündə qalır, vurğular altyazının üstünə düşmür.
- Son sözdən sonra 1 saniyə saxlanılır (`cut_takes.py` bunu edir).
- Görüntünün öz səsi saxlanılır. Musiqi və təsdiqlənməmiş səs effekti əlavə
  edilmir.
- Arxa fon xahiş olmadan bulanıqlaşdırılmır.


## Placement guard (before every final render)

`python3 templates/expert-reels/scripts/guard.py <project-id> --fix` finds the speaker's head and hands
(MediaPipe pose) and renders every overlay alone to get its real box. Any box that touches the head,
face or hands is reported and must be moved (higher, narrower, one line, or into the side column next
to the head: note `col` + `maxw`, bubble `maxw`). `--fix` also writes `caption_shift` into spec.json so the
captions step off the hands (one stable spot per stretch, not page-by-page hopping). Re-run build_edit
afterwards. Wide bottom panels (plate captions) cover the hands of a standing speaker - avoid them there.
