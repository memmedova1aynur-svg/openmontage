# Əlavə xərcsiz, yalnız iPhone ilə video hazırlamaq — variantların yoxlanması

Şərtlər: mövcud Claude və ChatGPT abunəlikləri, Google Drive. Ödənişli VPS, API,
hosting və saxlama yoxdur. ElevenLabs hələ alınmayıb. Abunəliklər API krediti sayılmır.

## Qısa qərar

**Seçilən yol: variant 3 — istifadəçinin iPhone-dakı Claude tətbiqindən başlatdığı
Claude Code sessiyası “montaj otağı” kimi.** Bu yol panelin mövcud kodunu (Drive
yükləmə, transkripsiya, söz sərhədli kəsim, kadraj, render) dəyişmədən işlədir; yeni
yazılan yalnız `montaj/session.py` (komanda sətri) və storyboard şəkli yaradıcısıdır.

Məhdudiyyəti: bu, **daimi və ya avtomatik AI bağlantısı deyil**. Hər video üçün
sessiyanı siz başladırsınız; konteyner müvəqqətidir; brauzer paneli telefondan açılmır,
düzəlişlər söhbətlə verilir.

## Müqayisə

| | 1. Yalnız iPhone/Safari | 2. Pulsuz server | 3. Claude Code sessiyası (seçilən) |
|---|---|---|---|
| Telefonda əl əməliyyatı (1 video) | ~10, amma render zamanı ekran açıq qalmalı | ~12–15 + bir dəfəlik hesab/qurulum | ~12–18 (aşağıda) |
| Emal və render harada | Telefonun brauzerində (ffmpeg.wasm) | HF Space / Oracle VM / GitHub Actions | Sessiyanın bulud konteyneri (4 CPU, 16 GB RAM) |
| Brauzer açıq qalmalıdır? | **Bəli** — iOS fon tabını dondurur | Xeyr | Xeyr — iş bulud sessiyasında gedir |
| Layihə və media harada | Telefon yaddaşı | Server diski (pulsuz variantlarda müvəqqəti) | Orijinal: sizin Drive-ınız. İş zamanı: müvəqqəti konteyner. Nəticə: telefona fayl kimi |
| Pulsuz limit | Yoxdur, amma iOS yaddaş limiti (≈ yüzlərlə MB-dan sonra tab çöküşü) | Aşağıdakı cədvəl | Claude abunəliyinin istifadə limiti; konteyner diski |
| Kodda dəyişiklik | Böyük: render və transkripsiyanı brauzerə köçürmək (yenidən yazmaq) | Orta: deploy + yaddaş (media itməsin deyə Drive OAuth) | Kiçik: CLI + storyboard şəkli (edildi) |
| Nəticə | Rədd: 1080p H.264 render və Whisper telefonda çox yavaş/qeyri-sabit, ekran açıq qalmalıdır | Hazırda rədd: hər birində ciddi şərt var (aşağıda) | **Qəbul** |

### Variant 1 — iPhone/Safari-də nə işləyə bilər
- Hazırda işləyən: yalnız UI (panel), amma o, serverə bağlıdır (API, media, render).
- `timeline.js` (kəsim, undo/redo, storyboard tətbiqi) brauzerdə müstəqil işləyir.
- Render (ffmpeg.wasm) və Whisper brauzerdə: iOS Safari WebAssembly yaddaşını sərt
  məhdudlaşdırır, böyük faylda tab xəbərdarlıqsız bağlanır, gizli tabda iş dayanır.
  Bu, “brauzer açıq qalmasın” tələbinə ziddir və böyük yenidənyazma tələb edir.
- Yalnız statik səhifə yerləşdirmək montaj sistemi deyil — ona görə rədd edildi.

### Variant 2 — pulsuz server variantları (2026-cı ilin sonu üçün mənbələrə görə, rəsmi səhifədə yoxlanmalıdır)
| Xidmət | Pulsuz limit | Problem |
|---|---|---|
| Hugging Face Spaces (CPU Basic) | 2 vCPU, 16 GB RAM, 50 GB **müvəqqəti** disk; 48 saat istifadəsiz qalanda yatır | Disk restartda silinir; daimi yaddaş ödənişlidir; 2026-da “hardware quota” şikayətləri var; müştəri videoları üçüncü tərəf serverində |
| Oracle Cloud Always Free (ARM) | 2026-da 4 OCPU/24 GB-dan 2 OCPU/12 GB-a endirilməsi bildirilir | Qeydiyyatda kart tələb olunur, boş VM geri alına bilir, tutum tapılmır |
| GitHub Actions (şəxsi repo) | 2 000 dəq/ay, 500 MB artefakt yeri | UI yoxdur; nəticə artefakt kimi; ictimai repoda artefaktları başqaları da yükləyə bilər |
| Render/Fly və s. | 512 MB RAM və ya yalnız sınaq krediti | Whisper + ffmpeg üçün kifayət deyil / daimi pulsuz deyil |

Bunlardan heç biri “əlavə xərcsiz + daimi + müştəri videosu məxfi” şərtlərinin hamısını
eyni anda qarşılamır.

### Variant 3 — Claude Code sessiyası (seçilən)
**Telefonda addımlar (təxmini 12–18 toxunuş):**
1. Drive tətbiqində videonu açın → “Paylaş” → giriş: “Linki olan hər kəs” → “Linki kopyala” (≈4).
2. Claude tətbiqi → Code → bu repo ilə yeni sessiya (≈3).
3. Linki yapışdırıb qısa yazın: “Lamiyə üçün reklam, 9:16, kəsimləri təklif et” (≈2).
4. Gələn storyboard şəklinə baxın, söhbətlə cavab verin: “təsdiq” və ya “2-ni çıxar, 1-ə mətn yaz …” (≈2–4).
5. Gələn MP4 faylını açın → Paylaş → “Videonu saxla” və ya Instagram (≈3–4).
6. İşdən sonra Drive-da paylaşımı yenidən “Məhdud” edin (≈3) — məxfilik üçün tövsiyə.

**Emal:** sessiyanın bulud konteynerində. **Telefonu kilidləmək olar** — iş davam edir.

**Saxlanma:** orijinal sizin Drive-ınızda qalır; konteynerdəki nüsxə sessiya bitəndə
silinir. Nəticələr (MP4, storyboard şəkli, `*.montaj.json` layihə faylı) telefona fayl
kimi göndərilir; onları Drive-a özünüz saxlaya bilərsiniz. Müştəri media faylı repoya
yazılmır.

**Limitlər:** iş Claude abunəliyinizin istifadə limitindən sərf edir (video emalı
konteyner CPU-sunda gedir, token sərf etmir; söhbət və planlaşdırma token sərf edir).
Bu sessiyada konteyner: 4 CPU, 16 GB RAM, ~26 GB boş disk. Bir neçə dəqiqəlik videolar
üçün kifayətdir. Telefona göndərilən faylın ölçü limiti bilinmir — real sınaqda yoxlanacaq.

**Hər yeni sessiya təmiz maşındır:** asılılıqlar (`faster-whisper`, `mediapipe`, `libegl1`)
quraşdırılmalıdır. Bunu mühitin **Setup script** sahəsinə `bash scripts/cloud-setup.sh`
yazmaqla bir dəfə avtomatlaşdırmaq olar (pulsuz).

**Məxfilik:** Drive linki “linki olan hər kəs” olduğu müddətdə faylı linki bilən hər kəs
yükləyə bilər. Ona görə paylaşımı yalnız iş müddətinə açın.

## ElevenLabs (alınarsa)
Yalnız səsləndirmə üçün lazımdır. Montajın qalan hissəsi ondan asılı deyil. Alınana
qədər səsləndirmə funksiyası “qoşulmayıb” kimi qalır.
