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
- **Yoxlama.** ffprobe ilə müddəti, ölçünü, kodeki, fps-i və HDR-i yoxla.
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

Analiz bu formada verilir:

```
Video növü: …
Əsas fikir və ya məqsəd: …
Seçilən montaj: M.. (+ M..)
Təxmini yekun müddət: …
```

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

### 6. Yekun yoxlama və təhvil

İxrac edilmiş faylda bunları yoxla:

- təsdiqlənmiş plana uyğunluq;
- danışığın mənası və vacib şərtlər;
- kəsimlər, səs və görüntünün sinxronu, səs səviyyəsi (−16 LUFS);
- altyazı, adlar, terminlər və rəqəmlər;
- mətnlərin yeri, fokus, rəng və görüntü problemləri (kadrlar çıxarılıb baxılır).

Baxılmayan və ya yoxlanmayan hissə yoxlanmış kimi göstərilmir.

Təhvildə yalnız bunlar verilir: SendUserFile ilə hazır MP4 (`*_ig.mp4`, 4K HEVC
~44 MB, telefona yüklənir), yekun müddət və varsa vacib məhdudiyyət.

Sonra yanaşma (M..) və əsas vizual qərarlar ekspert profilindəki `history`
bölməsinə yazılır.

## Sabit texniki qaydalar

- Altyazı Montserrat şrifti ilə yazılır. Mətn Instagram interfeysi zonasının
  üstündə qalır, vurğular altyazının üstünə düşmür.
- Son sözdən sonra 1 saniyə saxlanılır (`cut_takes.py` bunu edir).
- Görüntünün öz səsi və musiqisi saxlanılır. İstifadəçi musiqini CapCut-da özü
  əlavə edir; xahiş olmadan musiqi əlavə edilmir.
- Arxa fon xahiş olmadan bulanıqlaşdırılmır.
