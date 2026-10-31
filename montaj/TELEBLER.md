# Montaj paneli — tələblər siyahısı (izlənən)

Status açarları:
- ✅ **hazır + yoxlanılıb**: avtomatik test və ya brauzer testi ilə yoxlanılıb (sintetik materialla)
- 🟡 **hazır, real cihaz/material ilə yoxlanılmayıb**
- ⛔ **çatışmır / maneə var**: səbəbi yazılıb

Son yeniləmə: v2 (telefon axını). Hər commit-də bu fayl yenilənir.

Yoxlama əsası: `tests/montaj/` (Node 12, pytest 19) və brauzer testləri `e2e_flow.mjs`, `e2e_browser.mjs` (Chromium + iPhone ölçüsü emulyasiyası — real Safari deyil).

## 0. Büdcə və telefon yolu (v3)
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 0.1 | Əlavə ödənişli xidmət aktivləşdirilmir (VPS, API, hosting, saxlama) | ✅ | Heç biri aktiv deyil |
| 0.2 | Yalnız iPhone ilə bir videonu başdan sona hazırlamaq | 🟡 | Seçilən yol: Claude Code sessiyası + `montaj.session` CLI (`BUDCE_YOLU.md`). Real iPhone və real video ilə yoxlanılmayıb |
| 0.3 | Drive linkindən orijinal fayl (sessiyada) | 🟡 | Drive serverinə çıxış var; real paylaşımlı fayl ilə yoxlanılmayıb |
| 0.4 | Sessiyada hazırlanmış plan panel layihə faylı kimi | ✅ | `export` panelin öz `montaj.json` formatını verir (test) |
| 0.5 | Brauzerdə tam montaj paneli telefondan | ⛔ | Pulsuz daimi server yoxdur. Yerinə: telefon redaktoru (0.6) |
| 0.6 | Telefonda interaktiv redaktor (claude.ai artifact, sessiyadan dərc olunur) | 🟡 | Dərc olundu, önizləmə videosu artifact-ın şəxsi asset yerində; səhifənin db-yə yazdığı düzəliş sessiyada oxunub tətbiq olundu (cihaz məlum deyil). Real iPhone Safari/Claude tətbiqində təsdiqlənməyib |
| 0.7 | Yazını barmaqla başqa yerə çəkmək; yalnız o yazı dəyişir; render-də eyni yer | ✅ | Emulyasiya + render testi |
| 0.8 | Klipin başlanğıc/sonunu uzadıb kəsilmiş hissəni qaytarmaq; öz səsi sinxron; sonrakı kliplər, bağlı yazı və subtitrlər uyğunlaşır | ✅ | Emulyasiya + render sinxron testi (0 ms) |
| 0.9 | Düzəlişlər sabit ID və layihə versiyası ilə; köhnə/yanlış layihə aşkarlanır; undo/redo; qaralama saxlanılır | ✅ | |
| 0.10 | Düzəlişi Claude sessiyasına qaytarmaq | ✅ | Avtomatik (artifact db) və ya “Düzəlişi kopyala” |
| 0.11 | Analiz keşi (mənbə + parametrlər dəyişməyibsə təkrar transkripsiya yoxdur) | ✅ | |
| 0.13 | Müştəri profili (expert-reels `experts/*.json`) montaja tətbiq olunur | ✅ | Yalnız seçilən müştərinin faylı oxunur; törəmə rənglər “təsdiqlənməyib” kimi qeyd olunur |
| 0.14 | Redaktor: başlıq/altyazının mətni, şrifti (Montserrat, Caveat — OFL), ölçüsü, rəngi, fonu, yeri, vaxtı; bütün altyazıların ümumi üslubu | ✅ | Real layihədə emulyasiya + render müqayisəsi |
| 0.15 | Redaktor: klipi bölmək, uzatmaq, silmək, sırasını dəyişmək; öz səsi və altyazılar uyğunlaşır | ✅ | Altyazı ID-ləri bölmədən sonra sabit qalır (sərhəddəki biri istisna) |
| 0.16 | Redaktor: musiqi/səs effekti faylı əlavə etmək, yeri, hissəsi, səsi; danışıq/musiqi/effekt səviyyələri; danışıqda musiqinin azalması | 🟡 | Real səhifədə asset yükləmə sınaq əvəzi ilə yoxlanılıb; iPhone-da fayl seçimi yoxlanılmayıb. Lisenziyalı musiqi kitabxanası ⛔ |
| 0.17 | Redaktor: kadr, yaxınlaşma, güzgü (yazıları çevirmir), işıq, kontrast, doyumluluq, temperatur, filtr şablonları | ✅ | Rəng önizləməsi təxminidir |
| 0.18 | Yüngül yumşaltma (bütün kadr, kənarları qoruyur) | ✅ | Üzü ayrıca seçən retuş ⛔ — düymə qoyulmayıb |
| 0.19 | Altyazı sətri kadra sığır, cümlə/vergüldən keçmir | ✅ | ffmpeg mətni bölmədiyi üçün simvol limiti |
| 0.12 | Token istifadəsinin ölçülməsi | ⛔ | Bu sessiyadan token sayğacına giriş yoxdur — ölçülmür |

## 1. Telefondan açılan panel
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 1.1 | HTTPS ünvanından açılır | ⛔ | Server (VPS) hesabı lazımdır. `deploy/` hazırdır (Docker + Caddy, avtomatik sertifikat). Docker image bu sessiyada qurula bilmədi (sandbox-da DNS yoxdur, Docker Hub 429) — ilk quruluş serverdə yoxlanmalıdır. Ödənişli resurs təsdiqsiz aktivləşdirilmir |
| 1.2 | Video emalı və render serverdə | ✅ | Bütün emal server işləridir |
| 1.3 | Layihə və media daimi saxlanılır | ✅ | `MONTAJ_DATA_DIR` (Docker volume) |
| 1.4 | Giriş qorunur | ✅ | Parol + HMAC imzalı HttpOnly/Secure cookie; bütün API və media qorunur |
| 1.5 | Müştəri videoları və açarlar açıq yayımlanmır | ✅ | Media yalnız girişlə; açarlar yalnız mühit dəyişəni; status yalnız “var/yox” göstərir |
| 1.6 | Telefon kilidlənsə iş davam edir; yenidən açanda vəziyyət bərpa olunur | ✅ | İş diskdə (test: restart təqlidi); storyboard düzəlişi səhifəni yenidən açanda qalır (brauzer testi). Real iPhone kilidi ilə yoxlanılmayıb. İşlər diskdə saxlanılır, panel açılanda aktiv işləri göstərir. Server restartında yarımçıq iş “dayandı — yenidən başlat” kimi görünür |
| 1.7 | Hesab/ödəniş maneəsi, xidmət və xərc göstərilir | 🟡 | `deploy/README.md` (VPS — hazırkı büdcəyə daxil deyil, aktivləşdirilməyib). Əlavə xərcsiz yol: `BUDCE_YOLU.md` |

## 2. Sadə istifadə axını
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 2.1 | Drive linki daxil etmək | 🟡 | “Linki olan hər kəs” paylaşımlı fayl; orijinal baytlar saxta Drive serveri ilə yoxlanılıb, real Drive faylı ilə yox. Qovluq linki və şəxsi fayl üçün Google OAuth lazımdır (⛔) |
| 2.2 | Telefondan video və şəkil yükləmək | ✅ | Bir neçə fayl; şəkillər 4 s-lik klip olur |
| 2.3 | Bir neçə fayldan layihə | ✅ | |
| 2.4 | Ardıcıl “indi bunu edirəm” mətnləri yoxdur; sadə göstərici | ✅ | Proses zolağı |
| 2.5 | Xətada səbəb + istifadəçi addımı | ✅ | |
| 2.6 | Texniki loglar ayrıca diaqnostika bölməsində | ✅ | |

## 3. Müştəri seçimi
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 3.1 | “Kimin videosudur?” pəncərəsi, axtarış | ✅ | |
| 3.2 | 17 ilkin ad | ✅ | Brend məlumatı boşdur — uydurulmayıb |
| 3.3 | Yeni müştəri / birdəfəlik layihə | ✅ | |
| 3.4 | Ad, sahə, rəng kodları, şrift, loqo, montaj üstünlükləri | ✅ | Şrift adı saxlanılır və göstərilir; render hələ standart şriftlə (DejaVu Sans) — şrift faylı yükləmə yoxdur (🟡) |
| 3.5 | Seçəndə rəng nümunələri, şrift, loqo görünür | ✅ | |
| 3.6 | “Yalnız bu layihəyə” / “Müştəri profilində saxla” | ✅ | |

## 4. Montaj seçimləri
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 4.1 | Bütün formatlar hamı üçün açıq | ✅ | |
| 4.2 | Format / Məqsəd / Üslub / Əlavələr qrupları, çoxlu seçim | ✅ | |
| 4.3 | Hər qrupda “Sistem təklif etsin” | ✅ | |
| 4.4 | Müddət ayrıca, məcburi 30/60 yoxdur | ✅ | |

## 5. Kəsim qaydaları
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 5.1 | Kəsim rejimi: olduğu kimi / təklif et (standart) / avtomatik təmizlə | ✅ | |
| 5.2 | Pauza, nəfəs, vurğu səssizliyi səhv sayılmır | 🟡 | Yalnız uzun (≥1,2 s) sükut namizəddir, 0,25 s nəfəs payı saxlanılır. Real danışıqla yoxlanılmayıb |
| 5.3 | Söz və hecaların yarıda kəsilməməsi (hədəf) | 🟡 | ZƏMANƏT DEYİL: kəsim nöqtəsi Whisper-in söz vaxtlarına və səssizlik ölçüsünə görə seçilir. Whisper sözlərin sərhədini səhv verə və ya səssizlikdə söz uydura bilir (sintetik testdə görüldü). Real Azərbaycan danışığı ilə yoxlanılmayıb |
| 5.4 | Avtomatik təmizləmə də storyboard təsdiqindən sonra | ✅ | |
| 5.5 | Mənbə silinmir; kənarı uzadaraq geri qaytarmaq | ✅ | |
| 5.6 | Video + öz səsi birlikdə | ✅ | |
| 5.7 | Əl ilə düzəlişləri AI əvəz etmir | ✅ | |

## 6. Kadraj
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 6.1 | Avtomatik 9:16 təklifi | 🟡 | Kadraj məntiqi testlə, MediaPipe işləyir; real insan üzü olan video ilə yoxlanılmayıb |
| 6.2 | Əyriliyin düzəldilməsi | 🟡 | Yalnız əl ilə fırlatma sürgüsü; avtomatik əyrilik aşkarlanması ⛔ yoxdur |
| 6.3 | Baş üstü boşluq / kənarların azaldılması, baş-çənə kəsilmir | 🟡 | MediaPipe üz aşkarlanması; real insan videosu ilə yoxlanılmayıb |
| 6.4 | Məhsul/geyim/iki nəfər/tədbir — vacib obyektlər qorunur | 🟡 | Bir neçə üz varsa hamısı kadra salınır; obyekt (məhsul) aşkarlanması ⛔ yoxdur — bu növlərdə kadraj “əl ilə” rejimdə təklif edilir |
| 6.5 | Hər videonu üzə yaxınlaşdırmır | ✅ | Ölçü dəyişmir, yalnız 9:16 pəncərənin yeri |
| 6.6 | Yumşaq izləmə | ✅ | Hamarlanmış açar kadrlar |
| 6.7 | Orijinal / təklif müqayisəsi, əl ilə dəyişmək, sıfırlamaq | ✅ | |
| 6.8 | Həddindən artıq crop xəbərdarlığı, uydurma doldurma yoxdur | ✅ | |

## 7. Vizual storyboard və AI
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 7.1 | Faktiki AI bağlantısı | 🟡 | Claude API kodu hazırdır, amma API büdcəyə daxil deyil — açar yoxdur, aktivləşdirilməyəcək. Əlavə xərcsiz yolda plan istifadəçinin başlatdığı Claude Code sessiyasında hazırlanır (avtomatik/daimi bağlantı deyil) |
| 7.2 | Səssizlik/doldurucu söz AI kimi təqdim edilmir | ✅ | Açar olmadan “qaydalara əsaslanan təklif” kimi işarələnir |
| 7.3 | Real kadrlarla şəkilli storyboard: hissələr, açılış, mətn, qrafika/B-roll, musiqi, keçid | ✅ | |
| 7.4 | Qısa hərəkətli önizləmə | 🟡 | “▶ Önizlə” kartın hissəsini oynadır; avtomatik testlə yoxlanılmayıb |
| 7.5 | Təsdiqlə / Bu hissəni dəyiş / Alternativ göstər; tək kart | ✅ | Açarsız rejimdə alternativ — qonşu söz sərhədləri |
| 7.6 | Təsdiqsiz tətbiq yoxdur | ✅ | |
| 7.7 | Paneldaxili AI bağlantısı sessiyadakı Claude-dan ayrıdır; xidmət, açar, xərc | ✅ | Açar yoxlaması yalnız “var/işləyir” göstərir |

## 8. Əl ilə görüntü düzəlişləri
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 8.1 | Avtomatik filtr/retuş tətbiq edilmir | ✅ | |
| 8.2 | Güzgü (klip / bütün çəkiliş), mətn və loqo çevrilmir | ✅ | |
| 8.3 | Dəri yumşaltma, üzün işığı | ⛔ | Hərəkət boyunca izlənən üz maskası ilə kadr-kadr emal hələ yazılmayıb — düymə qoyulmayıb |
| 8.4 | Paltarı tündləşdirmə/ton | ⛔ | Paltar seqmentasiya modeli yoxdur — düymə qoyulmayıb |
| 8.5 | Arxa fon bulanıqlığı | ⛔ | Seqmentasiya ilə kadr-kadr render keçidi yazılmayıb — düymə qoyulmayıb |
| 8.6 | Parlaqlıq, kontrast, temperatur, doyumluluq | ✅ | Render-də FFmpeg; önizləmədə CSS (temperatur önizləmədə təxminidir) |
| 8.7 | Əvvəl/sonra, sıfırlama | ✅ | |

## 9. Musiqi, effektlər, qrafika, sonluq
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 9.1 | Mövzuya uyğun musiqi təklifi, hüququ məlum mənbə | ⛔ | Repoda lisenziyası təsdiqlənmiş musiqi yoxdur; Pixabay/Freesound açarı yoxdur. Öz musiqini yükləmək ✅ |
| 9.2 | Danışıq/musiqi/səsləndirmə/effekt səviyyələri ayrıca | ✅ | |
| 9.3 | Musiqinin hissəsi və vaxtı | ✅ | Klip kənarları və yeri |
| 9.4 | Danışıq zamanı musiqinin azalması — ayrıca seçim | 🟡 | Render-də sidechain işləyir (test), azalmanın səviyyəsi ölçülməyib; önizləmədə təxmini |
| 9.5 | Subtitr/keçid/motion/B-roll yalnız uyğun olduqda | 🟡 | Storyboard-da təklif; subtitr transkriptdən; keçid/motion/B-roll render-də ⛔ |
| 9.6 | Qrafika və SFX alternativ kitabxanası | ⛔ | Lisenziyası məlum material yoxdur |
| 9.7 | Loqo: yükləmə, yer, ölçü | ✅ | |
| 9.8 | Animasiyalı sonluq, loqolu bitiş, əlaqə, CTA — söndürülə bilir | ✅ | Sadə fade animasiyası |
| 9.9 | Səsləndirmə (kişi/qadın, Azərbaycan dili) | ⛔ | Azure TTS (az-AZ) kodu yoxdur/açar yoxdur — hazır sayılmır |

## 10. Keyfiyyət
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 10.1 | Drive-dan orijinal fayl | 🟡 | Yükləmə birbaşa orijinal faylı götürür; real Drive ilə yoxlanılmayıb |
| 10.2 | Orijinal dəyişmir; render orijinaldan | ✅ | |
| 10.3 | Ölçü/fps/rəng səbəbsiz dəyişmir; çevrilmələr göstərilir | ✅ | İxrac pəncərəsində siyahı |
| 10.4 | HDR/SDR, iPhone HEVC | 🟡 | HDR (PQ/HLG) → SDR tonemap; sintetik HEVC/HLG ilə yoxlanılıb, real iPhone faylı ilə yox |
| 10.5 | “Sıfır sıxılma” vədi yoxdur, keyfiyyətli ixrac | ✅ | CRF 18 |
| 10.6 | Hər dəfə orijinaldan render | ✅ | |

## 11. Caption və paylaşma
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 11.1 | Azərbaycan dilində caption təklifi (real məzmun + üslub) | 🟡 | Claude API ilə; açar yoxdur → düymə söndürülüb |
| 11.2 | Redaktə və kopyalama | ✅ | |
| 11.3 | Son ekran: önizləmə, cover, caption, Paylaş, Instagram-ı aç, MP4 endir | ✅ | |
| 11.4 | “Paylaş” iPhone paylaşma menyusuna MP4 ötürür | 🟡 | Web Share API (fayl). Real iPhone-da yoxlanılmayıb |
| 11.5 | Instagram/TikTok-un videonu qəbul etməsi | ⛔ | Real cihaz lazımdır |
| 11.6 | Instagram keçidi ötürmə kimi təqdim edilmir; hesab iddiası yoxdur | ✅ | |
| 11.7 | İstifadəçinin son əməliyyatı olmadan paylaşım yoxdur | ✅ | |

## 12. Real material ilə təsdiq tələb edən yoxlamalar (hamısı ⛔ — material yoxdur)
Azərbaycan dilində transkripsiya, yarımçıq sözlər, real üz kadrajı, real iPhone HEVC/HDR,
real danışıqda səs sinxronu və görünən keyfiyyət, iPhone Safari, Instagram/TikTok qəbulu.

## 13. Peşəkar montaj qatı (istinad layihələrdən: expert-reels profilləri)
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 13.1 | Söz-söz altyazı, aktiv söz vurğu rəngində | ✅ | `graphics.js` (önizləmə) = Chromium rasterizasiya (render) |
| 13.2 | Hook başlıq, bölmə, vurğu, siyahı (maddələr vaxtla), məlumat kartı | ✅ | Hər biri ayrıca redaktə: mətn, şrift, ölçü, rəng, fon, yer, vaxt, animasiya |
| 13.3 | Ölçülü zoom, sintez SFX (whoosh/pop), musiqi/SFX fade | ✅ | `session plan`; B-roll yoxdur (material yoxdur) |
| 13.4 | Altyazı: söz düzəlişi, layihədə hər yerdə dəyiş, böl, birləşdir | ✅ | Səs/video dəyişmir; manual mətn avtomatik analizlə yazılmır |
| 13.5 | Redaktordakı dəyişiklik MP4-ə keçir, qalan montaj saxlanır | ✅ | `e2e_editor_gfx.mjs` + render yoxlanıldı (Chromium emulyasiyası, real Safari deyil) |
| 13.6 | Telefondan musiqi | 🟡 | Yalnız .m4a/.mp4 (artifakt mp3/wav qəbul etmir) |
| 13.7 | “Dataclone 3” motion qrafikası | ⛔ | Repoda tapılmadı |
| 13.8 | Üz/məhsul üçün avtomatik yer qoruyucusu, smooth push-zoom, PIP | ⛔ | Hələ köçürülməyib |
