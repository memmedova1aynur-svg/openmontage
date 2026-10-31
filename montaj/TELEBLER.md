# Montaj paneli — tələblər siyahısı (izlənən)

Status açarları:
- ✅ **hazır + yoxlanılıb**: avtomatik test və ya brauzer testi ilə yoxlanılıb (sintetik materialla)
- 🟡 **hazır, real cihaz/material ilə yoxlanılmayıb**
- ⛔ **çatışmır / maneə var**: səbəbi yazılıb

Son yeniləmə: hər commit-də bu fayl yenilənir.

## 1. Telefondan açılan panel
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 1.1 | HTTPS ünvanından açılır | ⛔ | Server (VPS) və domen/HTTPS üçün hesab lazımdır. `deploy/` hazırdır (Docker + Caddy, avtomatik sertifikat). Ödənişli resurs təsdiqsiz aktivləşdirilmir |
| 1.2 | Video emalı və render serverdə | ✅ | Bütün emal server işləridir |
| 1.3 | Layihə və media daimi saxlanılır | ✅ | `MONTAJ_DATA_DIR` (Docker volume) |
| 1.4 | Giriş qorunur | ✅ | Parol + HMAC imzalı HttpOnly/Secure cookie; bütün API və media qorunur |
| 1.5 | Müştəri videoları və açarlar açıq yayımlanmır | ✅ | Media yalnız girişlə; açarlar yalnız mühit dəyişəni; status yalnız “var/yox” göstərir |
| 1.6 | Telefon kilidlənsə iş davam edir; yenidən açanda vəziyyət bərpa olunur | ✅ | İşlər diskdə saxlanılır, panel açılanda aktiv işləri göstərir. Server restartında yarımçıq iş “dayandı — yenidən başlat” kimi görünür |
| 1.7 | Hesab/ödəniş maneəsi, xidmət və xərc göstərilir | 🟡 | `deploy/README.md`; qiymətlər rəsmi səhifədən yoxlanmalıdır (bu sessiyada hetzner.com bağlı idi) |

## 2. Sadə istifadə axını
| # | Tələb | Status | Qeyd |
|---|---|---|---|
| 2.1 | Drive linki daxil etmək | 🟡 | “Linki olan hər kəs” paylaşımlı fayl. Real Drive faylı ilə yoxlanılmayıb. Qovluq linki və şəxsi fayl üçün Google OAuth lazımdır (⛔) |
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
| 3.4 | Ad, sahə, rəng kodları, şrift, loqo, montaj üstünlükləri | ✅ | |
| 3.5 | Seçəndə rəng nümunələri, şrift, loqo görünür | ✅ | |
| 3.6 | “Yalnız bu layihəyə” / “Müştəri profilində saxla” | ✅ | |

## 4. Montaj seçimləri
| 4.1 | Bütün formatlar hamı üçün açıq | ✅ | |
| 4.2 | Format / Məqsəd / Üslub / Əlavələr qrupları, çoxlu seçim | ✅ | |
| 4.3 | Hər qrupda “Sistem təklif etsin” | ✅ | |
| 4.4 | Müddət ayrıca, məcburi 30/60 yoxdur | ✅ | |

## 5. Kəsim qaydaları
| 5.1 | Kəsim rejimi: olduğu kimi / təklif et (standart) / avtomatik təmizlə | ✅ | |
| 5.2 | Pauza, nəfəs, vurğu səssizliyi səhv sayılmır | 🟡 | Yalnız uzun (≥1,2 s) sükut namizəddir, 0,25 s nəfəs payı saxlanılır. Real danışıqla yoxlanılmayıb |
| 5.3 | Söz və hecalar yarıda kəsilmir | 🟡 | Kəsim nöqtələri transkriptdəki söz sərhədlərinə çəkilir. Azərbaycan dilində real video ilə yoxlanılmayıb |
| 5.4 | Avtomatik təmizləmə də storyboard təsdiqindən sonra | ✅ | |
| 5.5 | Mənbə silinmir; kənarı uzadaraq geri qaytarmaq | ✅ | |
| 5.6 | Video + öz səsi birlikdə | ✅ | |
| 5.7 | Əl ilə düzəlişləri AI əvəz etmir | ✅ | |

## 6. Kadraj
| 6.1 | Avtomatik 9:16 təklifi | ✅ | Sintetik materialla |
| 6.2 | Əyriliyin düzəldilməsi | 🟡 | Yalnız əl ilə fırlatma sürgüsü; avtomatik əyrilik aşkarlanması ⛔ yoxdur |
| 6.3 | Baş üstü boşluq / kənarların azaldılması, baş-çənə kəsilmir | 🟡 | MediaPipe üz aşkarlanması; real insan videosu ilə yoxlanılmayıb |
| 6.4 | Məhsul/geyim/iki nəfər/tədbir — vacib obyektlər qorunur | 🟡 | Bir neçə üz varsa hamısı kadra salınır; obyekt (məhsul) aşkarlanması ⛔ yoxdur — bu növlərdə kadraj “əl ilə” rejimdə təklif edilir |
| 6.5 | Hər videonu üzə yaxınlaşdırmır | ✅ | Ölçü dəyişmir, yalnız 9:16 pəncərənin yeri |
| 6.6 | Yumşaq izləmə | ✅ | Hamarlanmış açar kadrlar |
| 6.7 | Orijinal / təklif müqayisəsi, əl ilə dəyişmək, sıfırlamaq | ✅ | |
| 6.8 | Həddindən artıq crop xəbərdarlığı, uydurma doldurma yoxdur | ✅ | |

## 7. Vizual storyboard və AI
| 7.1 | Faktiki AI bağlantısı | 🟡 | Claude API (`claude-opus-5-5`) kodu hazırdır; `ANTHROPIC_API_KEY` yoxdur → real çağırış yoxlanılmayıb |
| 7.2 | Səssizlik/doldurucu söz AI kimi təqdim edilmir | ✅ | Açar olmadan “qaydalara əsaslanan təklif” kimi işarələnir |
| 7.3 | Real kadrlarla şəkilli storyboard: hissələr, açılış, mətn, qrafika/B-roll, musiqi, keçid | ✅ | |
| 7.4 | Qısa hərəkətli önizləmə | ✅ | Kartın hissəsini oynatmaq |
| 7.5 | Təsdiqlə / Bu hissəni dəyiş / Alternativ göstər; tək kart | ✅ | Açarsız rejimdə alternativ — qonşu söz sərhədləri |
| 7.6 | Təsdiqsiz tətbiq yoxdur | ✅ | |
| 7.7 | Paneldaxili AI bağlantısı sessiyadakı Claude-dan ayrıdır; xidmət, açar, xərc | ✅ | Açar yoxlaması yalnız “var/işləyir” göstərir |

## 8. Əl ilə görüntü düzəlişləri
| 8.1 | Avtomatik filtr/retuş tətbiq edilmir | ✅ | |
| 8.2 | Güzgü (klip / bütün çəkiliş), mətn və loqo çevrilmir | ✅ | |
| 8.3 | Dəri yumşaltma, üzün işığı | ⛔ | Hərəkət boyunca izlənən üz maskası ilə kadr-kadr emal hələ yazılmayıb — düymə qoyulmayıb |
| 8.4 | Paltarı tündləşdirmə/ton | ⛔ | Paltar seqmentasiya modeli yoxdur — düymə qoyulmayıb |
| 8.5 | Arxa fon bulanıqlığı | ⛔ | Seqmentasiya ilə kadr-kadr render keçidi yazılmayıb — düymə qoyulmayıb |
| 8.6 | Parlaqlıq, kontrast, temperatur, doyumluluq | ✅ | Render-də FFmpeg; önizləmədə CSS (temperatur önizləmədə təxminidir) |
| 8.7 | Əvvəl/sonra, sıfırlama | ✅ | |

## 9. Musiqi, effektlər, qrafika, sonluq
| 9.1 | Mövzuya uyğun musiqi təklifi, hüququ məlum mənbə | ⛔ | Repoda lisenziyası təsdiqlənmiş musiqi yoxdur; Pixabay/Freesound açarı yoxdur. Öz musiqini yükləmək ✅ |
| 9.2 | Danışıq/musiqi/səsləndirmə/effekt səviyyələri ayrıca | ✅ | |
| 9.3 | Musiqinin hissəsi və vaxtı | ✅ | Klip kənarları və yeri |
| 9.4 | Danışıq zamanı musiqinin azalması — ayrıca seçim | ✅ | Render-də sidechain; önizləmədə təxmini |
| 9.5 | Subtitr/keçid/motion/B-roll yalnız uyğun olduqda | 🟡 | Storyboard-da təklif; subtitr transkriptdən; keçid/motion/B-roll render-də ⛔ |
| 9.6 | Qrafika və SFX alternativ kitabxanası | ⛔ | Lisenziyası məlum material yoxdur |
| 9.7 | Loqo: yükləmə, yer, ölçü | ✅ | |
| 9.8 | Animasiyalı sonluq, loqolu bitiş, əlaqə, CTA — söndürülə bilir | ✅ | Sadə fade animasiyası |
| 9.9 | Səsləndirmə (kişi/qadın, Azərbaycan dili) | ⛔ | Azure TTS (az-AZ) kodu yoxdur/açar yoxdur — hazır sayılmır |

## 10. Keyfiyyət
| 10.1 | Drive-dan orijinal fayl | 🟡 | Yükləmə birbaşa orijinal faylı götürür; real Drive ilə yoxlanılmayıb |
| 10.2 | Orijinal dəyişmir; render orijinaldan | ✅ | |
| 10.3 | Ölçü/fps/rəng səbəbsiz dəyişmir; çevrilmələr göstərilir | ✅ | İxrac pəncərəsində siyahı |
| 10.4 | HDR/SDR, iPhone HEVC | 🟡 | HDR (PQ/HLG) → SDR tonemap; sintetik HEVC/HLG ilə yoxlanılıb, real iPhone faylı ilə yox |
| 10.5 | “Sıfır sıxılma” vədi yoxdur, keyfiyyətli ixrac | ✅ | CRF 18 |
| 10.6 | Hər dəfə orijinaldan render | ✅ | |

## 11. Caption və paylaşma
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
