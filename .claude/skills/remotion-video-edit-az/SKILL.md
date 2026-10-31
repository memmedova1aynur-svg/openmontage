---
name: "remotion-video-edit-az"
description: "Remotion ilə Reels, TikTok və Shorts üçün dikey tanıtım videosu hazırlayır: kinetik tipografiya, keçidlər, vurğu anına sinxron səs və danışıq yazılarında boşluq və təkrar cümlə kəsimi."
---

# Remotion ilə video montajı

Bu skill Apple məhsul təqdimatı temposunda (sürətli, müasir, premium) 1080×1920 dikey videolar hazırlamaq üçündür. Bu üslub və kalıblar 15 saniyəlik "Claude ilə video edit" tanıtım reel-ində sınaqdan keçirilib və bəyənilib. Aşağıdakı üslub, keçid, səs və kod kalıblarını əsas götür; istifadəçinin mövzusuna, markasına və materiallarına uyğunlaşdır.

## 1. Başlamazdan əvvəl istifadəçidən soruş

Kod yazmazdan əvvəl aşağıdakıları **bir mesajda** soruş. İstifadəçi bir hissəsini artıq veribsə, onları yenidən soruşma.

1. **Mövzu və axın:** video nəyi danışır? Tövsiyə olunan axın: hook → problem → 3 xüsusiyyət → bağlanış. Süre necə olsun (standart 15 saniyə)? Ekrandakı mətnlər hansı dildə olsun? Marka rəngi və ya loqo varmı?
2. **Səs effektlərinin mənbəyi:** tövsiyə [Pixabay Sound Effects](https://pixabay.com/sound-effects/). Pulsuzdur, müəllif hüququ bildirişi tələb etmir; istifadə etməzdən əvvəl [Pixabay məzmun lisenziyası](https://pixabay.com/service/license-summary/)nı yoxla. İstifadəçiyə belə soruş: "Pixabay uyğundurmu, yoxsa istifadə etdiyin başqa sayt, alternativ təklifin və ya əlində hazır effektlər varmı?"
3. **Animasiya referansları:** tövsiyə [21st.dev](https://21st.dev). Bu üslub üç komponentdən alınıb:
   - [Shader Animation](https://21st.dev/@designali-in/components/shader-animation): RGB-yə ayrılan konsentrik halqalar.
   - [Horizon Hero Section](https://21st.dev/@lovesickfromthe6ix/components/horizon-hero-section): kosmik qradiyent, dağ silueti, işıq şüası, nəhəng wordmark.
   - [Scroll Morph Hero](https://21st.dev/@prashantsom75/components/scroll-morph-hero): kartların dağınıq vəziyyətdən çevrəyə, sonra qövsə morfu.

   İstifadəçiyə belə soruş: "Bu sayt və komponentlər uyğundurmu, yoxsa başqa sayt, referans video və ya alternativ təklifin varmı?"
4. **Fayl yolları:** hər kəsin qovluq quruluşu fərqlidir, təxmin etmə. Bunları soruş:
   - Səs effektləri hansı qovluqdadır?
   - Loqo, şəkil, ekran qeydi, video və ya font kimi digər asset-lər hansı qovluqdadır?
   - Remotion layihəsi harada qurulsun?
   - Arxa plan musiqisi varmı, varsa yolu hansıdır?
5. **Danışıq yazısı:** kəsiləcək danışıq yazısı varmı? Varsa bunları soruş:
   - boşluqlar mı, təkrar və ya səhv cümlələr mi, hər ikisi mi kəsilsin?
   - danışıq hansı dildədir?
   - mətn çevrilməsi üçün yerli AI quraşdırmasına icazə verirmi?
   - modeli hara yükləyim, ya da artıq yüklənmiş modeli varmı? (bax bölmə 5)

İstifadəçi səs effektlərini yükləməmi istəsə, yükləməzdən əvvəl hansı faylları hansı saytdan yükləyəcəyini deyib təsdiq al. Pixabay-dən yükləmə adətən giriş tələb edir; bu halda faylları istifadəçi özü yükləyib verdiyi qovluğa qoyur.

## 2. Mənbələri yoxla

- **Səs effektləri:** qovluqdakı hər faylın müddətini, sakit hissələrini və **vurğu anını** (səsin ən yüksək olduğu an) ölç. Effektləri bu ana görə yerləşdirəcəksən.
  ```bash
  ffprobe -v error -show_entries format=duration -of csv=p=0 "ses.mp3"
  ffmpeg -i "ses.mp3" -af "silencedetect=n=-40dB:d=0.05" -f null - 2>&1 | grep silence_
  ffmpeg -i "ses.mp3" -af "asetnsamples=2205,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.Peak_level" -f null - 2>&1 \
    | awk '/pts_time/{split($0,a,"pts_time:");t=a[2]} /Peak_level/{split($0,b,"=");if(b[2]>m||m==""){m=b[2];mt=t}} END{print mt}'
  ```
- **Arxa plan musiqisi:** varsa BPM-ni və beat zamanlarını çıxar, kəsimləri beat-ə oturt. Yoxdursa, kəsimləri 120 BPM grid-inə (0,5 saniyə = 30 fps-də 15 kadr) oturt; sonradan musiqi əlavə olunsa beat-ə düşəcək.
- **Referans saytlar:** səhifələri brauzerdə açıb ekran görüntüsü al. Rəng, tipoqrafiya və hərəkət dilini qeyd et. Komponentin mənbə kodu adətən giriş və ya API açarı tələb edir; kodu köçürməyə çalışma, vizual dili Remotion-a uyğunlaşdır.

## 3. Storyboard hazırla və təsdiq al

Hələ kod yazma və render alma. Səhnə-səhnə storyboard yaz. Hər səhnə üçün:
- müddət (başlanğıc–bitiş, saniyə ilə)
- ekranda nə olduğu
- hansı animasiya və kamera hərəkəti
- hansı səs effekti, hansı anda

Qaydalar:
- Hər səhnə ən çox 2–3 saniyə çəkməlidir; ekranda heç bir an statik qalmamalıdır.
- Yazılar böyük və oxunaqlı olsun, təhlükəsiz sahədən çıxmasın (bax Tipoqrafiya).
- Səhnənin vurğu sözü rəng və ya qradiyentlə seçilsin.

İstifadəçi təsdiq edəndə və ya düzəliş verəndə koda keç.

## 4. Layihəni qur

Layihəni istifadəçinin verdiyi qovluqda qur:

```bash
npm init -y
npm i remotion @remotion/cli @remotion/google-fonts react react-dom
npm i -D typescript @types/react
```

- Səs effektlərini `public/sfx/` altına **boşluqsuz adlarla** köçür (`whoosh 1.mp3` → `whoosh-1.mp3`); `staticFile()` boşluqlu adlarda problem yarada bilər.
- Fayl strukturu:
  - `src/index.ts`: `registerRoot` çağırışı.
  - `src/Root.tsx`: `<Composition width={1080} height={1920} fps={30} />`.
  - `src/theme.ts`: rənglər, fontlar, kəsim kadrları.
  - `src/components/kit.tsx`: ümumi köməkçilər.
  - `src/scenes/*.tsx`: səhnələr.
  - `src/Reel.tsx`: səhnələrin sıralanması və səs dizaynı.
- `remotion.config.ts`:
  ```ts
  import {Config} from '@remotion/cli/config';
  Config.setVideoImageFormat('jpeg');
  Config.setJpegQuality(95);
  Config.setChromiumOpenGlRenderer('angle'); // shader (WebGL) üçün vacibdir
  Config.setCodec('h264');
  Config.setCrf(16);
  ```
- Sınaqdan keçirilən versiya Remotion 4.0.539-dur (2026-10). `Audio` komponentində `trimBefore` istifadə olunur (köhnə adı `startFrom`). Daha yeni versiyada API-ni [Remotion sənədlərindən](https://www.remotion.dev/docs) yoxla.

## 5. Danışıq videosunda boşluq və təkrar cümlə kəsimi

İstifadəçi danışıq yazısı (izahat, vlog, ekran qeydi) verib boşluqların və ya təkrar və səhv cümlələrin kəsilməsini istəsə, kəsimi qrafiklərdən əvvəl et. Kəsim siyahısı Remotion-da `Series` ilə tətbiq olunur; ayrıca redaktor lazım deyil.

### Yerli və pulsuz AI quraşdırması

Danışığı mətnə çevirmək üçün pulsuz, internetə məlumat göndərməyən və kompüterdə işləyən [faster-whisper](https://github.com/SYSTRAN/faster-whisper) istifadə et. Model: `large-v3-turbo` (CPU, int8; türk dili daxil olmaqla çoxdilli). Daha sürətli, lakin daha az dəqiq ehtiyat variant kimi `small` istifadə oluna bilər.

**Quraşdırmadan əvvəl istifadəçidən soruş:**
- Python virtual mühiti haraya qurulsun?
- Model haraya yüklənsin? `large-v3-turbo` təxminən 1,6 GB, `small` təxminən 0,5 GB-dır.
- Əlində artıq yüklənmiş faster-whisper modeli varmı? Varsa yolunu soruş və onu istifadə et; eyni modeli ikinci dəfə yükləmə.

Təsdiq gələndə qur:

```bash
python3 -m venv <venv-yolu>
<venv-yolu>/bin/pip install faster-whisper
```

**Modeli yükləmək:**
- İstifadəçinin seçdiyi qovluğa `huggingface-cli download Systran/faster-whisper-large-v3-turbo --local-dir <model-qovluğu>` ilə yüklə; Hugging Face-ə giriş yoxdursa, istifadəçidən özünün yükləməsini xahiş et.
- Ya da `WhisperModel("large-v3-turbo")` ilə ilk işə salınmada yüklənməsinə icazə ver; bu halda model Hugging Face önbelleğinə (`~/.cache/huggingface`) düşəcək.

Metod hansı olursa olsun, `download_root` dəyərini mövcud model qovluğuna vermə. Faster-whisper oraya eyni modelin ikinci nüsxəsini yükləyər.

### Transkript (`transcribe.py`)

Əvvəlcə səsi mono 16 kHz WAV kimi çıxar:

```bash
ffmpeg -i video.mp4 -vn -ac 1 -ar 16000 ses.wav
```

Sonra transkripti al:

```bash
<venv-yolu>/bin/python -I transcribe.py ses.wav words.json tr <model-qovluğu-və-ya-adı>
```

Dil kodunu istifadəçinin danışdığı dilə sabitlə (türk dili üçün `tr`); avtomatik aşkarlamaya güvənmə.

```python
# Söz zamanlı transkript: python transcribe.py ses.wav words.json <dil> <model>
# Səs sakitliklərə görə parçalara bölünür və hər parça ayrıca həll olunur; uzun səsdə Whisper təkrar edən cəhdləri udur.
import json, sys, wave
import numpy as np
from faster_whisper import WhisperModel

audio_path, out, lang, model_ref = sys.argv[1:5]
w = wave.open(audio_path)
assert w.getframerate() == 16000 and w.getnchannels() == 1, "mono 16 kHz WAV ver"
# Səsi birbaşa massivə oxu: faster-whisper-in PyAV dekoderi bəzi versiyalarda xəta verir.
audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

# 10 ms enerji; səs-küy əsasından 12 dB yuxarısı danışıq sayılır, 0,35 saniyədən uzun sakitlikdə bölünür
hop = 160
frames = audio[: len(audio) // hop * hop].reshape(-1, hop)
db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
thr = max(-55.0, np.percentile(db, 10) + 12)
voiced = np.flatnonzero(db > thr)
chunks, start, prev = [], None, None
for i in voiced:
    if start is None:
        start = i
    elif i - prev > 35:
        chunks.append((start, prev + 1))
        start = i
    prev = i
if start is not None:
    chunks.append((start, prev + 1))

model = WhisperModel(model_ref, device="cpu", compute_type="int8")
words = []
for a, b in chunks:
    a0, b0 = max(0, a - 20), min(len(db), b + 20)  # 0,2 san pay
    segments, _ = model.transcribe(audio[a0 * hop : b0 * hop], language=lang, word_timestamps=True, condition_on_previous_text=False)
    off = a0 * hop / 16000
    words += [{"w": x.word.strip(), "s": round(x.start + off, 2), "e": round(x.end + off, 2)} for s in segments for x in s.words]
json.dump(words, open(out, "w"), ensure_ascii=False, indent=0)
print(len(chunks), "parça,", len(words), "söz")
```

Sürət: Apple Silicon CPU-da `large-v3-turbo` ilə parça-parça həll, 1 dəqiqəlik danışıqda təxminən 1 dəqiqə çəkir. Uzun yazıda işi fonda işlət. Transkripti mənbə fayla, modelə və dilə görə önbelleğə al; mənbə dəyişməyibsə yenidən həll etmə.

### Hansı sözlər çıxarılacaq (`remove.json`)

`words.json` faylını oxu və çıxarılacaq aralıqları mənbə saniyəsi ilə `remove.json` faylına yaz:

```json
[[11.10, 19.45, "təkrar: 'Məsələn Google Meet, Zoom və ya' ilk iki cəhd"],
 [56.40, 57.30, "kənar söz: 'Tamam.'"]]
```

Çıxarılacaqlar:
- **Təkrar olunan cümlə və ya başlanğıc:** **son, tam və təmiz** cəhd qalır, əvvəlkilər çıxır. Əvvəlki cəhd açıq-aydın daha yaxşıdırsa onu saxla və bunu istifadəçiyə de.
- **Yarımçıq qalmış cümlə, səhv başlanğıc və yalnız doldurucu sözlərdən ibarət parça** ("eee", "hə-hə", "yəni" kimi).
- **Yazıda özünə qeyd kimi deyilmiş sözlər** ("burada blur əlavə etmək lazımdır"): kəsilir, amma istifadəçiyə görüləcək iş kimi siyahıya salınır.

Diqqət ediləcəklər:
- Cümlələrin ardıcıllığını dəyişmə, mənanı pozma; yalnız bir dəfə deyilmiş məzmunu çıxar.
- Məhsul adlarını transkriptdə düzəlt (məsələn, ASR-nin "Cloud" yazdığını → "Claude"); sözlərin özünü dəyişmə.

### Kəsim siyahısı (`cuts.py`)

Kəsim sərhədlərini səs enerjisi, nəyin çıxarılacağını isə transkript müəyyən edir. Whisper-in söz zamanları sakitliyə doğru sürüşür; sərhəd üçün tək başına kifayət qədər dəqiq deyil.

```bash
python3 -I cuts.py ses.wav words.json remove.json cuts.json [hədd_dB]
```

Standart dəyərlər (istifadəçi başqa dəyər vermədikdə):

| Parametr | Dəyər |
| --- | --- |
| Kəsiləcək ən qısa sakitlik | 0,5 san; daha qısa fasilələr təbii ritm kimi qalır |
| Danışıqdan əvvəl / sonra saxlanılan pay | şaquli video 0,10 / 0,20 san; üfüqi video 0,12 / 0,15 san |
| Danışıq hüdduru | səs-küy əsasından 12 dB yuxarı (ən azı −55 dB). Səs-küylü yazıda hüdduru əl ilə ver |
| Sözsüz səs bloku (nəfəs, tıq, klaviatura) | danışıqdan ən azı 0,3 san uzaqdadırsa atılır |
| Sərhədlər | kadr şəbəkəsinə xaricə yuvarlanır; söz və ya hece kəsilmir |

```python
# Boşluq və səhv cümlə kəsim siyahısı: python cuts.py ses.wav words.json remove.json cuts.json [hədd_dB]
import array, json, math, sys, wave

wav, words_path, remove_path, out = sys.argv[1:5]
FPS = 30
MERGE_GAP = 0.10        # bundan qısa boşluqlar eyni səs bloku sayılır
MIN_SIL = 0.50          # yalnız bundan uzun sakitliklər kəsilir
PRE, POST = 0.10, 0.20  # danışıqdan əvvəl / sonra saxlanılan pay (şaquli video)
NOISE_DIST = 0.30       # sözsüz səs bloku danışıqdan bu qədər uzaqdırsa atılır

w = wave.open(wav)
sr, n = w.getframerate(), w.getnframes()
a = array.array("h", w.readframes(n))
hop = sr // 100
db = []
for i in range(0, len(a) - hop + 1, hop):
    r = math.sqrt(sum(v * v for v in a[i:i + hop]) / hop) / 32768
    db.append(20 * math.log10(r) if r > 0 else -120.0)
dur = len(db) / 100

sd = sorted(db)
floor = sd[int(0.10 * (len(sd) - 1))]
THR = float(sys.argv[5]) if len(sys.argv) > 5 else max(-55.0, floor + 12)
print(f"səs-küy əsası {floor:.1f} dB, median {sd[len(sd) // 2]:.1f} dB, hədd {THR:.1f} dB")

blobs, s, last = [], None, None
for i, v in enumerate(db):
    t = i / 100
    if v > THR:
        if s is None:
            s = t
        elif t - last > MERGE_GAP:
            blobs.append([s, last])
            s = t
        last = t + 0.01
if s is not None:
    blobs.append([s, last])

words = json.load(open(words_path))
remove = json.load(open(remove_path))
inside = lambda t: any(r[0] <= t <= r[1] for r in remove)

kept, removed_blobs, conflicts = [], [], []
for s, e in blobs:
    touching = [x for x in words if x["e"] > s - 0.05 and x["s"] < e + 0.05]
    if any(r[1] > s and r[0] < e for r in remove):
        keep_words = [x for x in touching if not inside((x["s"] + x["e"]) / 2)]
        if keep_words:  # çıxarılacaq söz, saxlanılacaq sözlə boşluqsuz bağlıdır: kəsmə, bildir
            conflicts.append([round(s, 2), round(e, 2), " ".join(x["w"] for x in touching)])
            kept.append([s, e])
        else:
            removed_blobs.append([s, e])
        continue
    if not touching:
        near = min((min(abs(x["s"] - e), abs(s - x["e"])) for x in words), default=99)
        if near >= NOISE_DIST:
            continue
    kept.append([s, e])

segs = []
for s, e in kept:
    a0, b0 = max(0.0, s - PRE), min(dur, e + POST)
    if segs:
        cut_between = any(rs >= segs[-1][2] - 0.01 and re <= s + 0.01 for rs, re in removed_blobs)
        if not cut_between and s - segs[-1][2] < MIN_SIL:
            segs[-1][1], segs[-1][2] = b0, e
            continue
        if cut_between:
            segs[-1][1] = min(segs[-1][1], max(rs for rs, re in removed_blobs if rs < s) - 0.02)
            a0 = max(a0, max(re for rs, re in removed_blobs if re <= s + 0.01) + 0.02)
        a0 = max(a0, segs[-1][1])
    segs.append([a0, b0, e])

cuts = []
for a0, b0, _ in segs:
    fa, fb = math.floor(a0 * FPS + 1e-6), math.ceil(b0 * FPS - 1e-6)
    if cuts and fa <= cuts[-1][1]:
        cuts[-1][1] = fb
    elif fb - fa >= 3:
        cuts.append([fa, fb])

total = sum(b - a for a, b in cuts)
json.dump({"fps": FPS, "cuts": cuts, "conflicts": conflicts}, open(out, "w"), ensure_ascii=False, indent=1)
print(f"{len(cuts)} parça, {dur:.1f} san → {total / FPS:.1f} san")
for c in conflicts:
    print("TOQQUŞMA (kəsilmədi):", c)
```

"TOQQUŞMA" sətirləri bunu göstərir: çıxarılacaq söz, saxlanılacaq sözlə arada sakitlik olmadan bağlıdır. Bunları sözün ortasından kəsmə; istifadəçiyə siyahı şəklində göstər.

### Yoxlama

Kəsilmiş səsi yenidən qur və yenidən transkript al. Heç bir söz yarımçıq qalmamalı, mətn səlis oxunmalıdır. Bu addım render deyil, yalnız səslə aparılan yoxlamadır.

```bash
F=$(python3 -c "import json;d=json.load(open('cuts.json'));print('+'.join(f'between(t,{a/30:.4f},{b/30:.4f})' for a,b in d['cuts']))")
ffmpeg -i ses.wav -af "aselect='$F',asetpts=N/SR/TB" yoxlama.wav
<venv-yolu>/bin/python -I transcribe.py yoxlama.wav yoxlama.json tr <model>
```

İstifadəçiyə bunları bildir:
- yeni süre
- çıxarılan hər parça: zamanı, sözləri və səbəbi
- toqquşmalar
- videoya özünə yazılmış qeydlər

İstifadəçinin öz səsinə kəsimdən başqa heç bir səs emalı (səviyyə, EQ, səs-küy azaltma, fade) tətbiq etmə.

### Remotion-da tətbiq et

Videonu `public/footage/` altına qoy (və ya simvolik keçid ver). Parçaları `Series` ilə ardıcıl düz. `trimBefore` və `trimAfter` kompozisiyanın fps-i ilə kadrdır; mənbə videonun fps-i fərqlidirsə `cuts.py` içindəki `FPS` dəyərini kompozisiya ilə eyni et. JSON-u import etmək üçün `tsconfig.json` içində `"resolveJsonModule": true` olmalıdır.

```tsx
import {OffthreadVideo, Series, staticFile} from 'remotion';
import data from './cuts.json';

export const TALK_FRAMES = data.cuts.reduce((t, [a, b]) => t + b - a, 0); // Composition durationInFrames

export const Talk: React.FC = () => (
  <Series>
    {data.cuts.map(([a, b], i) => (
      <Series.Sequence key={i} durationInFrames={b - a}>
        <OffthreadVideo src={staticFile('footage/kayit.mp4')} trimBefore={a} trimAfter={b} />
      </Series.Sequence>
    ))}
  </Series>
);
```

**Qrafik və altyazı:** kinetik yazıları, kartları və altyazını kəsimdən sonrakı zamana bağla. Sözün yeni zamanı belə hesablanır:

`yeni kadr = (sözün saniyəsi × fps − parçanın a dəyəri) + həmin parçadan əvvəlki parçaların ümumi uzunluğu`

## 6. Vizual dil

İstifadəçi öz marka palitrasını verərsə onu istifadə et; verməzsə aşağıdakı palitranı işlət.

### Palitra

| Ad | Dəyər | İstifadə |
| --- | --- | --- |
| black | `#000000` | shader / səs səhnələri |
| ink | `#0B0B10` | açıq fon üzərində başlıq, çatlaq xətti |
| cream | `#F5F2EE` | açıq səhnə fonu, tünd fonda başlıq |
| deep → indigo | `#05040C` → `#120E2E` → `#2A1F63` → `#43307F` | kosmik qradiyent (yuxarıdan aşağı) |
| violet | `#6B5BD2` | sələnmə, işıldama |
| coral | `#FF5A4E` | eyebrow, vurğu sözü, düymə |
| peach → coral → terracotta | `#FFB199` → `#FF5A4E` → `#D97757` | vurğu qradiyenti: `linear-gradient(180deg, #FFB199 0%, #FF5A4E 45%, #D97757 100%)`, sözə `background-clip: text` ilə |

### Fontlar

- **Başlıq:** [Inter Tight](https://fonts.google.com/specimen/Inter+Tight) 900 / 800 / 700.
- **Mətn:** [Inter](https://fonts.google.com/specimen/Inter) 400–600.
- **Mono:** `SF Mono, Menlo, ui-monospace, monospace` (eyebrow, sayğac, fayl adları).
- Yükləmə kodu:
  ```ts
  import {loadFont as loadTight} from '@remotion/google-fonts/InterTight';
  import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
  export const display = loadTight('normal', {weights: ['700', '800', '900'], subsets: ['latin', 'latin-ext']}).fontFamily;
  export const body = loadInter('normal', {weights: ['400', '500', '600'], subsets: ['latin', 'latin-ext']}).fontFamily;
  ```
  Türk və digər Latın olmayan simvollar üçün `latin-ext` alt çoxluğunu mütləq əlavə et.

### Tipoqrafiya (1080×1920)

- **Səhnə başlığı:** 150 px, Inter Tight 900, `letterSpacing: -0.045em`, `lineHeight: 0.95`. Sola düzləndirilmiş (`left: 90`), iki sətir, hər sətir ayrı maskadan keçərək gəlir.
- **Eyebrow:** başlığın üstündə. Mono 38 px, coral, `letterSpacing: 0.2em`, format `01 — PROMPT`.
- **Hook sözləri:** 170–190 px, ortalanmış.
- **Alt sətir:** Inter 600, 58 px, söz-söz; son söz coral.
- **Təhlükəsiz sahə** (Reels interfeysi üçün): yanlarda 90 px, yuxarı mətn y ≥ 300, aşağı məzmun y ≤ 1540.

## 7. Hərəkət kalıpları

`src/components/kit.tsx` içinə qoy:

```tsx
import React from 'react';
import {Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame} from 'remotion';

const FPS = 30;
// Hər səhnə kəsimdən OVER kadr əvvəl başlayır; yeni səhnə köhnəsinin üstünə təbəqə kimi düşür.
export const OVER = 8;
export const useCut = () => useCurrentFrame() - OVER; // keçid zamanı mənfi
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const spr = (f: number, delay = 0, config: Partial<{damping: number; stiffness: number; mass: number}> = {}) =>
  spring({frame: f - delay, fps: FPS, config: {damping: 14, stiffness: 170, mass: 0.7, ...config}});

// RGB split kölgəsi
export const chroma = (amt: number) =>
  amt < 0.3 ? 'none' : `${amt}px 0 rgba(255,50,90,0.85), ${-amt}px 0 rgba(40,200,255,0.85)`;

// Səsin vurğu anı (trim-dən `peak` saniyə sonra) dəqiq `at` kadrına düşür.
export const Sfx: React.FC<{name: string; at: number; peak?: number; trim?: number; dur?: number; vol?: number; fadeOut?: number}> = ({
  name, at, peak = 0, trim = 0, dur = 60, vol = 1, fadeOut = 0,
}) => {
  const from = at - Math.round(peak * FPS);
  const skip = from < 0 ? -from : 0;
  return (
    <Sequence from={Math.max(0, from)} durationInFrames={dur} layout="none">
      <Audio
        src={staticFile(`sfx/${name}.mp3`)}
        trimBefore={Math.round(trim * FPS) + skip}
        volume={(f) => (fadeOut ? vol * interpolate(f, [dur - fadeOut, dur], [1, 0], clamp) : vol)}
      />
    </Sequence>
  );
};

// Sətir, maskanın arxasından sürüşərək gəlir.
export const MaskUp: React.FC<{f: number; delay: number; children: React.ReactNode}> = ({f, delay, children}) => {
  const s = spr(f, delay, {damping: 16, stiffness: 150});
  return (
    <div style={{overflow: 'hidden', padding: '0.04em 0 0.1em'}}>
      <div style={{transform: `translateY(${(1 - s) * 115}%) rotate(${(1 - s) * 4}deg)`, transformOrigin: 'left bottom'}}>{children}</div>
    </div>
  );
};

// Söz böyükdən oturur: blur və RGB split sönür, 2–4. kadrlarda qısa glitch.
export const Pop: React.FC<{f: number; delay: number; from?: number; children: React.ReactNode}> = ({f, delay, from = 1.5, children}) => {
  const s = spr(f, delay, {damping: 12, stiffness: 190});
  const glitch = f - delay >= 2 && f - delay <= 4 ? 10 : 0;
  return (
    <div style={{
      transform: `scale(${interpolate(s, [0, 1], [from, 1])})`,
      opacity: interpolate(s, [0, 0.35], [0, 1], clamp),
      filter: `blur(${(1 - s) * 22}px)`,
      textShadow: chroma((1 - s) * 26 + glitch),
    }}>{children}</div>
  );
};
```

**Səhnə sıralaması (`Reel.tsx`):** hər səhnəni `<Sequence from={kəsim - OVER} durationInFrames={növbəti kəsim - kəsim + OVER}>` içinə qoy. İlk səhnə üçün `from` mənfi ola bilər. Səhnənin içində `const f = useCut()` istifadə et; `f < 0` keçid anıdır.

**Qaydalar:**
- **Spring ayarları:** sərt giriş üçün `stiffness 190–420`, yumşaq morf üçün `damping 20–22, stiffness 80–90`.
- **Kamera:** hər səhnədə davamlı zoom olsun. Məzmun `1 → 1.06–1.10`, arxa plan `1.12–1.25 → 1` (əks istiqamətdə parallax).
- **Ardıcıl gecikmə (stagger):** sətirlər arasında 4–5 kadr, kartlar arasında 1,2–2 kadr.

## 8. Keçidlər

Hamısı gələn səhnənin kök elementinə tətbiq olunur. `w` və `r`, `interpolate(f, [-OVER, 2], [0, 1], clamp)` ilə 0-dan 1-ə gedir.

| Keçid | Kod | Səs |
| --- | --- | --- |
| **Çapraz wipe** | `clipPath: polygon(0 ${100 - w*130}%, 100% ${130 - w*130}%, 100% 100%, 0 100%)` | böyük whoosh, vurğu kəsimdən 2 kadr əvvəl |
| **Dairəvi açılış** | `clipPath: circle(${r*130}% at 50% 62%)`, ease-in quad | orta whoosh, vurğu kəsimdən 2 kadr əvvəl |
| **Aşağıdan dönərək gəlmə** | `translateY((1-r)*1920px) rotate((1-r)*8deg)` + `blur((1-r)*18px)`, ease-out cubic | qısa whoosh |
| **Yandan whip-pan** | `translateX((1-r)*1080px)` + `blur((1-r)*24px)` | qısa whoosh |
| **Ağ flaş** | tam ekran ağ təbəqə, şəffaflıq `[t-4, t, t+18] → [0, 1, 0]` | kamera flaşı; riser-in bitişi bu kadra düzəldilir |
| **Buz çatlağı → shard açılış** | aşağıda | buz qırılması + qısa whoosh |

**Buz çatlağı (köhnə səhnənin son 8 kadrı):** ekran mərkəzindən 9 qırıq SVG yolu çək.
- Hər yol 6 seqment × 210 px; bucaq jitter-i ±0,3 rad (`random()` ilə deterministik).
- Çəkilmə: `pathLength={1}`, `strokeDasharray={1}`, `strokeDashoffset={1 - p}`, rəng `#0B0B10`, 5 px.
- Eyni anda köhnə səhnə 2 px-dən 12 px-ə qədər silkələnir: `Math.sin(f * 4) * genlik`.

**Shard açılış (yeni səhnə):** ease-out cubic ilə böyüyən, 18 küncü qeyri-bərabər çoxbucaqlı:

```ts
const shardClip = (p: number) => `polygon(${new Array(18).fill(0).map((_, i) => {
  const a = (i / 18) * Math.PI * 2;
  const r = p * 1700 * (0.7 + random(`sh${i}`) * 0.6);
  return `${540 + Math.cos(a) * r}px ${960 + Math.sin(a) * r}px`;
}).join(',')})`;
```

## 9. Səhnə kalıpları

**Shader hook:** qara fon, 21st.dev Shader Animation-un WebGL variantı. 1–2 söz `Pop` ilə girir.
- Canvas-a `preserveDrawingBuffer: true` ver və hər kadrda `useLayoutEffect` içində çək.
- Fragment shader:
  ```glsl
  precision highp float;
  uniform vec2 r; uniform float t; uniform float z; uniform float g;
  float ch(float off, vec2 uv) {
    float s = 0.0;
    for (int i = 0; i < 5; i++) {
      float fi = float(i);
      s += 0.002 * g * fi * fi / abs(fract(t - off + fi * 0.01) * 5.0 - length(uv) + mod(uv.x + uv.y, 0.2));
    }
    return s;
  }
  void main() {
    vec2 uv = (gl_FragCoord.xy * 2.0 - r) / min(r.x, r.y) * z;
    gl_FragColor = vec4(ch(0.0, uv), ch(0.01, uv), ch(0.02, uv), 1.0);
  }
  ```
- Halqa radiusu `fract(t) × 5`-dir. Səhnə boyunca `t` dəyərini 0,02-dən 0,42-yə apar, `z = 1`, `g ≈ 1.4` istifadə et.

**Problem səhnəsi ("Saatlarla timeline."):**
- Krem fonda 16 "timeline klipi" kartı uçuşur. Kartlar ağ, `r18`; sol kənarda 16 px pastel zolaq, yuxarıda mono `clip_XX.mov`, aşağıda keyframe almazları.
- Kartlar yuxarıdan düşərək girir (gecikmə 1,2 kadr), sonra süzülür, fırlanır və ±3 px titrəyir.
- Yazının arxasında krem rəngli radial pərdə var; oxunaqlılığı o təmin edir.
- Yuxarıda coral mono sayğac (`⏱ 03:12:47`) sürətlə axır.
- Səs: saat tik-taqı. Səhnə buz çatlağı ilə bitir.

**Prompt səhnəsi:**
- Kosmik qradiyent fon, ulduzlar, iki qat dağ silueti (parallax). Üstündə şüşə effektli prompt qutusu:
  - `rgba(255,255,255,.16 → .05)` qradiyent, 1,5 px ağ 25% kənar, `backdrop-filter: blur(30px)`, `r44`.
- Qarşılıqlı təsir ardıcıllığı:
  1. Hər kadrda bir hərf yazı maşını effekti, coral kursor.
  2. Kursor göndər düyməsinə süzülür.
  3. Kliklədə düymə `scale 1 → 0.82 → 1` edir, qutu coral parlayır.
  4. Krem rəngli cavab toast-u enir.
- Səs: klaviatura → mouse click → bildiriş.

**Kart morfu (Scroll Morph):**
- Ağ fon, 12 kart (150×200, `r22`).
- **Faza 1:** hər kart `spr(f, 6 + 2i, {damping 16, stiffness 130})` ilə təsadüfi mövqedən çevrəyə oturur (radius 360, mərkəz 540, 1060). Kartın bucağı tangensə baxır, çevrə yavaş fırlanır.
- **Faza 2:** `spr(f, 34, {damping 22, stiffness 80})` ilə radius 580-ə, mərkəz y 1560-a, bucaq aralığı 2π-dən 1,05π-yə gedir və çevrə göyqurşağı qövsünə çevrilir.
- Səs: kartlar oturdıqca hər 6 kadrdan bir pop; sonda ding.

**Ritm / səs sinxronu:**
- 40 çubuqlu dalğa forması hər beat-də pulsasiya edir. 3 kəsim işarəsi zirvə nöqtələrinə "snap" olur.
- Hər snap-də pop səsi, mikro silkələnmə və RGB split olur.

**Sayğac / render:**
- Böyük odometr (%000 → %100): onluq dəyəri davamlı sürüşən rəqəm sütunları; baş sıfırlar solğun.
- Aşağıda qradiyent progress xətti. %100-də ağ flaş partlayır.

**Bağlanış (Horizon):**
- Kosmik qradiyent, sələnmə, ulduzlar, dağ silueti və dağın zirvəsindən yüksələn şaquli işıq şüası.
- Kamera dağdan yuxarı tilt edir. Böyük wordmark hərf-hərf aşağıdan gəlir (gecikmə 2,5 kadr), coral qradiyentlə.
- Tagline maskadan keçərək girir. Tagline girərkən şüanın şəffaflığını 0,2-yə endir, yoxsa yazının üstündən keçər.

## 10. Səs dizaynı

Effektləri fayl adına görə yox, **növünə** görə uyğunlaşdır və hər birinin vurğu anını ölç (bax bölmə 2). Pixabay-də aşağıdakı axtarışlar yaxşı nəticə verir:

| Növ (Pixabay axtarışı) | İstifadə | Tipik vurğu | Səviyyə |
| --- | --- | --- | --- |
| whoosh (qısa) | slide, whip-pan | 0,1–0,2 san | 0,45–0,7 |
| whoosh (uzun) | böyük wipe | 0,6–0,9 san | 0,4–0,7 |
| pop | söz və ya kart oturması, snap | 0,1–0,2 san | 0,5–0,9 |
| ding | bölümün tamamlanması | ~0,1 san | 0,6–0,7, fade 6–8 kadr |
| notification | cavab toast-u, loqo oturması | ~0,1 san | 0,75 |
| mouse click | düymə kliki | ~0,02 san | 0,9 |
| keyboard typing | yazı maşını effekti | ilk düyməyə `trim` ilə keç | 0,6, fade 4 kadr |
| clock ticking | gərginlik, "saatlarla" | — | 0,45, fade 6 kadr |
| ice crack / glass crack | ekranın qırılması | ən sərt qırılmanın qısa hissəsi (`trim`) | 0,95, fade 8 kadr |
| riser | bağlanışdan əvvəl yüksəlmə | bitişini flaş kadrına düzəlt | 0,8 |
| camera flash | ağ flaş | ~0,15 san | 0,9 |

İstifadə nümunələri:

```tsx
<Sfx name="whoosh-2" at={kesim - 2} peak={0.85} vol={0.7} dur={50} />
<Sfx name="ice-crack" at={kesim - 8} trim={5.12} peak={0.1} vol={0.95} dur={22} fadeOut={8} />
```

- **Səviyyə və fade:** effektlərin səviyyəsi, kəsimi və fade-i sərbəst tənzimlənə bilər. İstifadəçinin öz danışıq səsi varsa, ona effekt, EQ və ya səviyyə tətbiq etmə; istəsə özü edər.
- **Musiqi:** kəsimləri beat-ə oturt, effektləri musiqinin altında itməyəcək səviyyədə saxla.

## 11. Önizləmə və yoxlama

1. **Studio-nu aç:** `npx remotion studio`. Desktop tətbiqində `.claude/launch.json` faylı yaz və `preview_start` istifadə et; port olaraq məsələn 3123 ver və `--no-open` əlavə et.
2. **Kadrları özün yoxla:** kritik kadrlardan (hər səhnənin ortası və keçid anları) still götür, sonra hamısını yan-yana birləşdirib bax:
   ```bash
   npx remotion still <Comp> kadr.jpg --frame=N --scale=0.4 --gl=angle
   ffmpeg -i a.jpg -i b.jpg -i c.jpg -filter_complex "hstack=3" sheet.jpg
   ```
   Bunlara bax: yazı təhlükəsiz sahədədirmi, oxunaqlıdırmı, türk hərfləri düzgündürmü, ilk kadr qaradırmı (Reels qapağı üçün boş qalmamalıdır), shader görünürmü.
3. **İstifadəçiyə göstər:** Studio ünvanını ver; zaman göstəricisi `dəqiqə:saniye.kadr` formatındadır (`00:01:23` = 1 san 23 kadr). İstifadəçi bu zamanlarla düzəliş versə, kadra çevirib tətbiq et.

## 12. Render

Render yalnız istifadəçi son təsdiqini verdikdən sonra alınır:

```bash
npx remotion render <Comp> out/video.mp4 --gl=angle
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration -of compact out/video.mp4
ffmpeg -i out/video.mp4 -af volumedetect -f null - 2>&1 | grep max_volume
```

Çıxışın 1080×1920, 30 fps və düzgün müddətdə olduğunu yoxla; səsin pik səviyyəsi 0 dB-dən aşağı olmalıdır. Bir neçə kadrlıq contact sheet ilə görüntüyə son dəfə bax. Səsləri qulaqla dinləyə bilmədiyini istifadəçiyə açıq de.

## Tələlər

- **Shader yalnız boz çarpaz xətt göstərirsə:** halqa ekrandan kənardadır. `t` dəyərini kiçilt (radius `fract(t) × 5`).
- **Shader çox parlaqdırsa:** `g` dəyərini 5-dən 1,4-ə endir.
- **GLSL:** dövr daxilində vektoru dinamik indekslə (`c[j]`) işlətmə; hər kanalı ayrıca funksiya ilə hesabla.
- **Render-də shader boş çıxırsa:** `--gl=angle` əlavə et və canvas-a `preserveDrawingBuffer: true` ver.
- **Təsadüfilik:** `Math.random()` istifadə etmə; render kadrları fərqli çıxır. Remotion-un `random('seed')` funksiyasından istifadə et.
- **Qradiyent yazı:** `background-clip: text` olan yazıya `text-shadow` vermə; kölgə yazının içindən görünür. Bu yazılarda yalnız blur və scale istifadə et.