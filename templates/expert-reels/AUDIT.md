# Montaj imkanlarının auditi — 2026-10-26

Hər bənd bu sessiyada faktiki yoxlanılıb. "Yoxlanılıb işləyir" yalnız həqiqətən icra edilib nəticəsi ölçülən işlərə verilib.

## 1. İş mühiti

| Sual | Faktiki vəziyyət |
|---|---|
| Hansı mühit | Claude Code, uzaq bulud sessiyası (claude.ai/code). Linux konteyner, 4 CPU, 15 GB RAM, GPU yoxdur. Konteyner müvəqqətidir: sessiya bitəndə `projects/` silinir, yalnız git-ə göndərilənlər qalır. |
| Video oxumaq və emal etmək | Bəli. ffprobe ilə oxunur, ffmpeg, Remotion və Python ilə emal olunur. Kadrları şəkil kimi açıb gözlə yoxlaya bilirəm. Səsi **qulaqla dinləyə bilmirəm**, yalnız ölçürəm (LUFS, dB, transkripsiya). |
| Lokal fayllar | Yalnız bu konteynerin faylları. Sizin kompüterinizə və telefonunuza çıxışım yoxdur. Fayllar Google Drive linki və ya Google Drive bağlantısı ilə gəlir; çata yükləmə limiti 30 MB-dır. |
| Kod və terminal | Bəli: bash, Python 3.13, Node 22. |
| Cihaz açıq olmalıdırmı | Yox. Bütün iş buludda gedir, cihazınız bağlı ola bilər. Yalnız nəticəni endirmək üçün telefon və ya kompüter lazımdır. |
| Şəbəkə | Açıqdır: Google Drive, Google API, Hugging Face, npm, PyPI. Bloklanıb (yoxlanılıb, cavab 000): Pexels, Pixabay, Freesound, api.elevenlabs.io, capcut.com. |

## 2. Alətlər

| Alət | Status | Mən işlədirəm? | Nə edir | Nə etmir | Xərc və bağlantı |
|---|---|---|---|---|---|
| FFmpeg 6.1.1 + ffprobe | Yoxlanılıb işləyir | Bəli | Kəsim, birləşdirmə, kodlama (H.264, HEVC, AV1, ProRes), loudnorm, afftdn/arnndn, sidechain, eq/colorbalance/lut3d, zscale, xfade, subtitr | Qrafik dizayn | Pulsuz, lokal |
| faster-whisper large-v3 | Yoxlanılıb işləyir | Bəli | Azərbaycan dilində transkripsiya, söz-söz zaman kodları | Xüsusi adları və terminləri səhv yaza bilir, insan yoxlaması lazımdır | Pulsuz, lokal (model Hugging Face-dən yüklənir) |
| Remotion 4.0.484 + Chromium | Yoxlanılıb işləyir | Bəli | Animasiyalı altyazı, yazılar, ara kadr, zoom, 4K render | Real kadrda obyekt izləmə | Lisenziya: fərdlər və ≤3 işçili şirkətlər üçün pulsuzdur, daha böyük şirkətlər üçün ödənişli şirkət lisenziyası lazımdır (remotion.dev/license — vəziyyətinizə görə yoxlayın) |
| expert-reels şablonu (bu repo) | Yoxlanılıb işləyir | Bəli | Brend profili, spec → MP4, retake kəsimi, fon bulanıqlığı | — | Pulsuz |
| MODNet (onnxruntime) | Yoxlanılıb işləyir | Bəli | Fonu bulanıqlaşdırmaq (insanı ayırmaq) | Sürətli deyil (1 dəq video ≈ 19 dəq) | Apache-2.0, pulsuz |
| OpenCV 5 | Əlçatandır, sınaq lazımdır | Bəli | Üz aşkarlanması üçün YuNet (model faylı lazımdır) | Haar kaskadı bu buildda yoxdur | Pulsuz |
| MediaPipe | Əlavə quraşdırma lazımdır | — | Üz izləmə (avtomatik reframe) | — | PyPI-da var (1.1.1), sınanmayıb |
| HyperFrames | Qeydiyyatda "mövcud" | Sınanmayıb | HTML/GSAP animasiya | Talking-head prosesində dəstəklənmir | — |
| ElevenLabs (bağlantı) | Bağlıdır, hesab işləyir | Bağlantı ilə | TTS (Azərbaycan səsləri, klonlanmış "Aynur" səsi daxil), SFX, musiqi, transkripsiya | Montaj etmir | Kreditlərlə ödənişlidir |
| OpusClip (bağlantı) | Bağlıdır (TRIAL plan, API açıq) | Bağlantı ilə | Uzun videodan klip çıxarmaq, altyazı | Sizin brend sisteminizə tam nəzarət vermir | Trial plan; sonra ödənişli |
| AI Producer by OpusClip | Bağlıdır, sınaq lazımdır | Bağlantı ilə | Transkripsiya, altyazı, b-roll axtarışı, SFX, MP4 ixracı, redaktə olunan layihə (onların redaktorunda) | Bu sandboxdan fayl yükləmə hələ sınanmayıb | Hazırda "müvəqqəti pulsuz", ölçülür (metered) |
| Tella (bağlantı) | Bağlıdır (iş sahəsi boşdur) | Bağlantı ilə | Ekran yazısı videoları | Talking-head montajı üçün əsas alət deyil | Tella hesabı |
| Google Drive (bağlantı) | Yoxlanılıb işləyir | Bəli | Faylların metadatası; yükləmə HTTPS ilə | Böyük faylları bağlantı ilə yükləmək mümkün deyil (base64) | Pulsuz |
| Adobe / Canva / Figma plaginləri | Qoşulma xətası (proxy 403) | Xeyr | — | — | Bağlantı düzəlməlidir |
| CapCut | Bu mühitdə mümkün deyil | Xeyr | — | Proqram, plagin və bağlantı yoxdur, sayt bloklanıb | — |
| Veo / Gemini (GEMINI_API_KEY) | Əlçatandır, sınaq lazımdır | Bəli | AI video və şəkil yaratmaq | Real insanı əvəz etmir | API açarının sahibinə ödənişlidir |

## 3. Əməliyyatların imkan cədvəli

| Əməliyyat | Status | Sübut |
|---|---|---|
| Texniki məlumat oxumaq | Yoxlanılıb işləyir | ffprobe: kodek, ölçü, fps, rəng (bt709/HDR), səs |
| Azərbaycan dilində transkripsiya | Yoxlanılıb işləyir | 4 video, etibarlılıq 91,7–95,4%; adlar insan yoxlaması ilə düzəldildi |
| Azərbaycan hərfləri ilə subtitr | Yoxlanılıb işləyir | Montserrat latin-ext; ə, ğ, ş, ı, ç 4K-da kadrda yoxlanıldı |
| Söz və cümlə üzrə zamanlama | Yoxlanılıb işləyir | Sınaqda çıxış videosu yenidən transkripsiya edildi: altyazı ilə səs fərqi orta hesabla 44 ms, ən çox 110 ms |
| Pauzaların müəyyənləşdirilməsi | Yoxlanılıb işləyir | silencedetect + söz zaman kodları |
| Təkrarların müəyyənləşdirilməsi | Yarı-avtomatik | Transkripti mən oxuyub qərar verirəm; avtomatik aşkarlama alqoritmi yoxdur |
| Məna qorunmaqla kəsim | Yoxlanılıb işləyir (texniki) | cut_takes.py: 1,5 s silindi, altyazı vaxtları avtomatik yeniləndi. Real çox-takeli videoda hələ sınanmayıb |
| Şaquli kadr | Yoxlanılıb işləyir | 1080×1920 və 2160×3840 çıxış |
| Üzün kadrda saxlanması (16:9 → 9:16) | Əlavə quraşdırma lazımdır | Haar yoxdur; YuNet modeli və ya MediaPipe lazımdır |
| Yumşaq yaxınlaşdırma | Yoxlanılıb işləyir | push, punch, slow drift |
| Başlıq və açar söz vurğuları | Yoxlanılıb işləyir | kart, pop (yuxarı/sol/sağ), marker vurğusu |
| B-roll (öz animasiyalarımız) | Yoxlanılıb işləyir | timeline, phone, checklist, chat, questions, stat |
| B-roll (müştərinin real videoları) | Əlçatandır, sınaq lazımdır | Texniki olaraq eyni yol; real faylla sınanmayıb |
| B-roll (stok) | Əlavə bağlantı lazımdır | Pexels/Pixabay bloklanıb və API açarı yoxdur |
| Şəkil, ekran görüntüsü, qrafika | Qrafika yoxlanılıb; şəkil üçün sınaq lazımdır | — |
| Səs səviyyəsinin tənzimlənməsi | Yoxlanılıb işləyir | −16 LUFS (tam videolar −16,0 / −16,4); peak ≤ −0,5 dBFS |
| Fon səsinin azaldılması | Yoxlanılıb (ölçü ilə) | afftdn: səs-küy səviyyəsi −49 → −78 dB. Qulaqla yoxlamanı siz etməlisiniz |
| Musiqi ilə nitqin balansı | Yoxlanılıb işləyir | Sidechain: danışıq zamanı musiqi 15–19 dB aşağı düşür |
| Sadə rəng korreksiyası | Yoxlanılıb (texniki) | eq və colorbalance kadra tətbiq olundu |
| Keçidlər və səs effektləri | Yoxlanılıb işləyir | Sintez edilmiş SFX (whoosh, pop, hit, tick, ding), müəllif hüququ problemi yoxdur |
| Şablonu başqa videoya tətbiq etmək | Yoxlanılıb işləyir | 3 müxtəlif video eyni şablonla, fərqli üslublarla |
| Toplu emal | Yoxlanılıb işləyir (ardıcıl) | Növbəli render; 4K-da 1 dəqiqə video ≈ 15–20 dəqiqə |
| Paylaşılmağa hazır ixrac | Yoxlanılıb işləyir | 4K H.264 master (CRF 14) + 4K HEVC ~44 MB (iPhone-uyğun hvc1) |
| Redaktə olunan layihə | Qismən | Remotion layihəsi + spec.json (mən redaktə edirəm). FCPXML/EDL (Premiere/Resolve) yaratmaq mümkündür, sınaq lazımdır. CapCut layihəsi: bu mühitdə mümkün deyil |

Qeyd: master faylda piksel formatı `yuvj420p` (tam diapazon) çıxır. Instagram üçün həmişə `_ig.mp4` (yuv420p) faylını istifadə edin.

## 4. Material mənbələri və hüquqlar

| Mənbə | Vəziyyət | Hüquq qaydası |
|---|---|---|
| Müştərinin video və foto arxivi | Drive ilə qəbul edirəm | Müştəri yazılı razılıq versin; yalnız onun öz materialı |
| Komandanın çəkdiyi B-roll | Drive ilə | Komandanın əsəri; müştəri ilə müqavilədə qeyd edilsin |
| Stok videolar | Hazırda əlçatan deyil | Pexels/Pixabay lisenziyaları kommersiya üçün icazə verir, amma bu mühitdə bloklanıb. Hər faylın mənbəyi və lisenziyası qeyd olunsun |
| Musiqi | Ekspertin öz musiqisi saxlanılır; əlavə musiqini CapCut və ya Instagram kitabxanasından siz qoyursunuz | İnternetdə tapılan mahnı istifadə icazəsi demək deyil |
| Səs effektləri | Kodla sintez edilir | Müəllif hüququ problemi yoxdur |
| Şriftlər | Montserrat (SIL OFL), repo-da lisenziyası ilə | Kommersiya istifadəsi sərbəstdir |
| İkon və qrafika | Kodla çəkilir; emoji sistem şriftindən | Üçüncü tərəf ikon dəstləri əlavə ediləndə lisenziyası yoxlansın |
| Loqo və brend materialları | Müştəridən alınmalıdır | Yalnız müştərinin verdiyi fayllar |

Başqa müəllifin videosu icazəsiz götürülmür.

## 5. Kiçik texniki sınaq

Mənbə: "Ucuz təlimçi imici" videosunun ilk 10 saniyəsi. Orijinal fayla toxunulmadı (SHA-256 əvvəl və sonra eynidir: 9957f17d2112fa26).

| Addım | Nəticə |
|---|---|
| Azərbaycan dilində subtitr, Montserrat | "dərk" → "dərs", "imci" → "imici" düzəldildi; hərflər düzgün görünür |
| Yumşaq yaxınlaşdırma | 5,6 s-də 1,0 → 1,1 |
| Açar ifadə vurğusu | "Peşəkarlıq **deyil**" yuxarıda |
| Səs | −17,2 LUFS, LRA 4,2, peak −3,3 dBFS. Qısa klipdə tək keçidli loudnorm hədəfdən 1,2 dB aşağı qaldı |
| İxrac | test.mp4: 2160×3840 H.264 High, 30 fps, 54,5 MB; test_ig.mp4: 2160×3840 HEVC, 11,0 MB |
| Yenidən açıb yoxlama | Kadrlar 1,0 / 6,6 / 9,2 s-də yoxlandı. 20/20 söz sinxrondur, orta fərq 44 ms, ən çox 110 ms |

## 6. Tövsiyə olunan iş axını

Video (Drive, orijinal) → ffprobe → faster-whisper large-v3 → mətnin düzəldilməsi → mənanın təhlili və montaj rejimi → spec.json (brend profili + rejim) → retake kəsimi → Remotion 4K → HEVC ~44 MB → keyfiyyət yoxlaması (kadrlar, LUFS, sinxron) → çatdırılma.

Niyə bu yol: başdan-sona sınaqdan keçmiş yeganə yoldur. Azərbaycan hərflərini, brendi və 4K-nı tam idarə edir, pulsuzdur və hər addımı ölçülə bilir.

## 7. Məhdudiyyətlər

- Render sürəti: 4K-da 1 dəqiqə video ≈ 15–20 dəqiqə. Fon bulanıqlığı əlavə olaraq ≈ 19 dəqiqə.
- Səsi qulaqla dinləyə bilmirəm. Musiqi zövqü və səs təmizliyi barədə son qərar sizindir.
- Transkripsiya xüsusi adlarda səhv edir. Hər müştəri üçün terminlər lüğəti lazımdır.
- Konteyner müvəqqətidir. Şablonlar git-də qalır, layihə faylları sessiya bitəndə silinir.
- Telefona böyük fayl (200 MB+) çatdan yüklənmir, ona görə ~44 MB-lıq HEVC versiya göndərilir.
- CapCut layihəsi verə bilmirəm. Redaktəni mən spec ilə edirəm, ya da yekun MP4-ü CapCut-da açırsınız.
