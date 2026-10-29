---
name: remotion-video-edit
description: Remotion ile Instagram Reels / TikTok / Shorts kalitesinde dikey tanıtım videosu üretir. Kinetik tipografi, spring animasyonlar, kamera hissi veren zoom/pan, katmanlı geçişler (çapraz wipe, buz çatlağı + shard açılış, daire açılış) ve vurgu anına senkron ses efektleri kullanır. Konuşmalı kayıtlarda boşlukları ve tekrar eden / hatalı cümleleri, ücretsiz yerel AI (faster-whisper) ile yazıya döküp keser. Önce sahne sahne storyboard çıkarır, onay alır, Remotion Studio'da önizleme açar ve son onaydan sonra render alır. Kullanıcı tanıtım videosu, reel, motion graphics, kinetik tipografi, "video yap / video editle", "boşlukları kes", "tekrar eden / hatalı cümleleri kes" ya da Remotion ile video istediğinde kullan.
---

# Remotion ile video edit

Bu skill, Apple ürün tanıtımı temposunda (hızlı, modern, premium) 1080×1920 dikey videolar üretmek içindir. Kalıplar, 15 saniyelik bir "Claude ile video edit" tanıtım reel'inde denendi ve beğenildi. Aşağıdaki stil, geçiş, ses ve kod kalıplarını temel al; kullanıcının konusuna, markasına ve kaynaklarına uyarla.

## 1. Başlamadan önce kullanıcıya sor

Kod yazmadan önce aşağıdakileri **tek mesajda** sor. Kullanıcı bir kısmını zaten verdiyse onları tekrar sorma.

1. **Konu ve akış:** video ne anlatıyor? Önerilen akış: hook → problem → 3 özellik → kapanış. Süre ne olsun (varsayılan 15 sn)? Ekrandaki metinler hangi dilde olsun? Bir marka rengi ya da logo var mı?
2. **Ses efektleri kaynağı:** öneri [Pixabay Sound Effects](https://pixabay.com/sound-effects/). Ücretsizdir, telif bildirimi gerektirmez; kullanmadan önce [Pixabay İçerik Lisansı](https://pixabay.com/service/license-summary/)'nı kontrol et. Kullanıcıya şunu sor: "Pixabay uygun mu, yoksa kullandığın başka bir site, alternatif bir önerin ya da elinde hazır efektler var mı?"
3. **Animasyon referansları:** öneri [21st.dev](https://21st.dev). Bu stil şu üç bileşenden türetildi:
   - [Shader Animation](https://21st.dev/@designali-in/components/shader-animation): RGB'ye ayrışan eş merkezli halkalar.
   - [Horizon Hero Section](https://21st.dev/@lovesickfromthe6ix/components/horizon-hero-section): uzay gradyanı, dağ silüeti, ışık huzmesi, dev wordmark.
   - [Scroll Morph Hero](https://21st.dev/@prashantsom75/components/scroll-morph-hero): kartların dağınık → çember → yay morph'u.

   Kullanıcıya şunu sor: "Bu site ve bileşenler uygun mu, yoksa başka bir site, referans video ya da alternatif önerin var mı?"
4. **Dosya yolları:** herkesin klasör yapısı farklıdır, varsayım yapma. Şunları sor:
   - Ses efektleri hangi klasörde?
   - Logo, görsel, ekran kaydı, video ya da font gibi diğer asset'ler hangi klasörde?
   - Remotion projesi nereye kurulsun?
   - Arka plan müziği var mı, varsa yolu ne?
5. **Konuşmalı kayıt:** kesilecek bir konuşmalı kayıt var mı? Varsa şunları sor:
   - boşluklar mı, tekrar eden / hatalı cümleler mi, ikisi birden mi kesilsin?
   - konuşma hangi dilde?
   - transkript için yerel AI kurulumuna izin veriyor mu?
   - modeli nereye indireyim, ya da zaten indirilmiş bir modeli var mı? (bkz. bölüm 5)

Kullanıcı ses efekti indirmeni isterse, indirmeden önce hangi dosyaları hangi siteden indireceğini söyleyip onay al. Pixabay'den indirme çoğu zaman giriş gerektirir; bu durumda dosyaları kullanıcı kendisi indirip verdiği klasöre koyar.

## 2. Kaynakları incele

- **Ses efektleri:** klasördeki her dosyanın süresini, sessizliklerini ve **vurgu anını** (sesin en yüksek olduğu an) ölç. Efektleri bu ana göre yerleştireceksin.
  ```bash
  ffprobe -v error -show_entries format=duration -of csv=p=0 "ses.mp3"
  ffmpeg -i "ses.mp3" -af "silencedetect=n=-40dB:d=0.05" -f null - 2>&1 | grep silence_
  ffmpeg -i "ses.mp3" -af "asetnsamples=2205,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.Peak_level" -f null - 2>&1 \
    | awk '/pts_time/{split($0,a,"pts_time:");t=a[2]} /Peak_level/{split($0,b,"=");if(b[2]>m||m==""){m=b[2];mt=t}} END{print mt}'
  ```
- **Arka plan müziği:** varsa BPM'ini ve beat zamanlarını çıkar, kesimleri beat'e oturt. Yoksa kesimleri 120 BPM grid'ine (0,5 sn = 30 fps'de 15 kare) oturt; sonradan müzik eklenirse beat'e denk gelir.
- **Referans siteler:** sayfaları tarayıcıda açıp ekran görüntüsü al. Renk, tipografi ve hareket dilini not et. Bileşen kaynak kodu genelde giriş ya da API anahtarı ister; kodu kopyalamaya çalışma, görsel dili Remotion'a uyarla.

## 3. Storyboard çıkar ve onay al

Henüz kod yazma ve render alma. Sahne sahne bir storyboard yaz. Her sahne için:
- süre (başlangıç–bitiş, saniye)
- ekranda ne olduğu
- hangi animasyon ve kamera hareketi
- hangi ses efekti, hangi anda

Kurallar:
- Her sahne en fazla 2–3 sn sürsün; ekranda hiçbir an statik kalmasın.
- Yazılar büyük ve okunaklı olsun, güvenli alanın dışına taşmasın (bkz. Tipografi).
- Sahnenin vurgu kelimesi bir renk ya da gradyanla öne çıksın.

Kullanıcı onaylayınca ya da revize verince koda geç.

## 4. Projeyi kur

Projeyi kullanıcının verdiği klasöre kur:

```bash
npm init -y
npm i remotion @remotion/cli @remotion/google-fonts react react-dom
npm i -D typescript @types/react
```

- Ses efektlerini `public/sfx/` altına **boşluksuz adlarla** kopyala (`whoosh 1.mp3` → `whoosh-1.mp3`); `staticFile()` boşluklu adlarda sorun çıkarabilir.
- Dosya yapısı:
  - `src/index.ts`: `registerRoot` çağrısı.
  - `src/Root.tsx`: `<Composition width={1080} height={1920} fps={30} />`.
  - `src/theme.ts`: renkler, fontlar, kesim kareleri.
  - `src/components/kit.tsx`: ortak yardımcılar.
  - `src/scenes/*.tsx`: sahneler.
  - `src/Reel.tsx`: sahne sıralaması ve ses tasarımı.
- `remotion.config.ts`:
  ```ts
  import {Config} from '@remotion/cli/config';
  Config.setVideoImageFormat('jpeg');
  Config.setJpegQuality(95);
  Config.setChromiumOpenGlRenderer('angle'); // shader (WebGL) için şart
  Config.setCodec('h264');
  Config.setCrf(16);
  ```
- Test edilen sürüm Remotion 4.0.539 (2026-10). `Audio` bileşeninde `trimBefore` kullanılır (eski adı `startFrom`). Daha yeni bir sürümde API'yi [Remotion dokümantasyonundan](https://www.remotion.dev/docs) kontrol et.

## 5. Konuşmalı videoda boşluk ve hatalı cümle kesimi

Kullanıcı konuşmalı bir kayıt (anlatım, vlog, ekran kaydı) verip boşlukların ya da tekrar eden / hatalı cümlelerin kesilmesini isterse, kesimi grafiklerden önce yap. Kesim listesi Remotion'da `Series` ile uygulanır; ayrı bir editör gerekmez.

### Yerel ve ücretsiz AI kurulumu

Konuşmayı yazıya dökmek için ücretsiz, internete veri göndermeyen ve bilgisayarda çalışan [faster-whisper](https://github.com/SYSTRAN/faster-whisper) kullan. Model: `large-v3-turbo` (CPU, int8; Türkçe dahil çok dilli). Daha hızlı ama daha az isabetli bir yedek olarak `small` kullanılabilir.

**Kurmadan önce kullanıcıya sor:**
- Python sanal ortamı nereye kurulsun?
- Model nereye indirilsin? `large-v3-turbo` yaklaşık 1,6 GB, `small` yaklaşık 0,5 GB.
- Elinde zaten indirilmiş bir faster-whisper modeli var mı? Varsa yolunu sor ve onu kullan; aynı modeli ikinci kez indirme.

Onay gelince kur:

```bash
python3 -m venv <venv-yolu>
<venv-yolu>/bin/pip install faster-whisper
```

**Modeli indirme:**
- Kullanıcının istediği klasöre `huggingface-cli download Systran/faster-whisper-large-v3-turbo --local-dir <model-klasörü>` ile indir; Hugging Face'e erişim yoksa kullanıcıdan indirmesini iste.
- Ya da `WhisperModel("large-v3-turbo")` ile ilk çalıştırmada indirilmesine izin ver; bu durumda model Hugging Face önbelleğine (`~/.cache/huggingface`) iner.

Yöntem ne olursa olsun, `download_root` değerini mevcut bir model klasörüne verme. Faster-whisper oraya aynı modelin ikinci bir kopyasını indirir.

### Transkript (`transcribe.py`)

Önce sesi mono 16 kHz WAV olarak çıkar:

```bash
ffmpeg -i video.mp4 -vn -ac 1 -ar 16000 ses.wav
```

Sonra transkripti al:

```bash
<venv-yolu>/bin/python -I transcribe.py ses.wav words.json tr <model-klasörü-ya-da-adı>
```

Dil kodunu kullanıcının konuştuğu dile sabitle (Türkçe için `tr`); otomatik algılamaya güvenme.

```python
# Kelime zamanlı transkript: python transcribe.py ses.wav words.json <dil> <model>
# Ses, sessizliklerden parçalara bölünüp her parça ayrı çözülür; Whisper uzun seste tekrar eden denemeleri yutar.
import json, sys, wave
import numpy as np
from faster_whisper import WhisperModel

audio_path, out, lang, model_ref = sys.argv[1:5]
w = wave.open(audio_path)
assert w.getframerate() == 16000 and w.getnchannels() == 1, "mono 16 kHz WAV ver"
# Sesi doğrudan diziye oku: faster-whisper'ın PyAV çözücüsü bazı sürümlerde hata veriyor.
audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

# 10 ms enerji; gürültü tabanının 12 dB üstü konuşma sayılır, 0,35 sn'den uzun sessizlikte bölünür
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
    a0, b0 = max(0, a - 20), min(len(db), b + 20)  # 0,2 sn pay
    segments, _ = model.transcribe(audio[a0 * hop : b0 * hop], language=lang, word_timestamps=True, condition_on_previous_text=False)
    off = a0 * hop / 16000
    words += [{"w": x.word.strip(), "s": round(x.start + off, 2), "e": round(x.end + off, 2)} for s in segments for x in s.words]
json.dump(words, open(out, "w"), ensure_ascii=False, indent=0)
print(len(chunks), "parça,", len(words), "kelime")
```

Hız: Apple Silicon CPU'da `large-v3-turbo` ile parça parça çözüm, 1 dakikalık konuşmada yaklaşık 1 dakika sürer. Uzun kayıtta işi arka planda çalıştır. Transkripti kaynak dosya, model ve dile göre önbelleğe al; kaynak değişmediyse yeniden çözme.

### Hangi sözler çıkarılacak (`remove.json`)

`words.json` dosyasını oku ve çıkarılacak aralıkları kaynak saniyesiyle `remove.json` dosyasına yaz:

```json
[[11.10, 19.45, "tekrar: 'Örneğin Google Meet, Zoom veya' ilk iki deneme"],
 [56.40, 57.30, "kenar söz: 'Tamam.'"]]
```

Çıkarılacaklar:
- **Tekrar eden cümle ya da başlangıç:** **son, eksiksiz ve temiz** deneme kalır, öncekiler çıkar. Önceki deneme açıkça daha iyiyse onu tut ve bunu kullanıcıya söyle.
- **Yarım bırakılan cümle, yanlış başlangıç ve yalnızca dolgudan oluşan parça** ("ıı", "şey", "dur ya").
- **Kayıtta kendine düşülen notlar** ("şuraya blur atmak lazım"): kesilir, ama kullanıcıya yapılacak iş olarak listelenir.

Dikkat edilecekler:
- Cümlelerin sırasını değiştirme, anlamı bozma; yalnızca bir kez söylenmiş içeriği çıkarma.
- Ürün adlarını transkriptte düzelt (ör. ASR'nin "Cloud"u → "Claude"); sözleri değiştirme.

### Kesim listesi (`cuts.py`)

Kesim sınırlarını ses enerjisi, neyin çıkacağını transkript belirler. Whisper'ın kelime zamanları sessizliklere taşar; sınır için tek başına yeterince hassas değildir.

```bash
python3 -I cuts.py ses.wav words.json remove.json cuts.json [eşik_dB]
```

Varsayılanlar (kullanıcı başka değer vermediyse):

| Ayar | Değer |
| --- | --- |
| Kesilecek en kısa sessizlik | 0,5 sn; daha kısa duraklar doğal ritim olarak kalır |
| Konuşmadan önce / sonra bırakılan pay | dikey video 0,10 / 0,20 sn; yatay video 0,12 / 0,15 sn |
| Konuşma eşiği | gürültü tabanının 12 dB üstü (en az −55 dB). Gürültülü kayıtta eşiği elle ver |
| Kelimesiz ses bloğu (nefes, tık, klavye) | konuşmadan en az 0,3 sn uzaksa atılır |
| Sınırlar | kare ızgarasına dışa doğru yuvarlanır; kelime ya da hece kesilmez |

```python
# Boşluk + hatalı cümle kesim listesi: python cuts.py ses.wav words.json remove.json cuts.json [eşik_dB]
import array, json, math, sys, wave

wav, words_path, remove_path, out = sys.argv[1:5]
FPS = 30
MERGE_GAP = 0.10        # bundan kısa boşluklar aynı ses bloğu
MIN_SIL = 0.50          # yalnızca bundan uzun sessizlikler kesilir
PRE, POST = 0.10, 0.20  # konuşmadan önce / sonra bırakılan pay (dikey video)
NOISE_DIST = 0.30       # kelimesiz ses bloğu konuşmadan bu kadar uzaksa atılır

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
print(f"gürültü tabanı {floor:.1f} dB, medyan {sd[len(sd) // 2]:.1f} dB, eşik {THR:.1f} dB")

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
        if keep_words:  # çıkarılacak söz, tutulacak sözle boşluksuz bağlı: kesme, raporla
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
print(f"{len(cuts)} parça, {dur:.1f} sn → {total / FPS:.1f} sn")
for c in conflicts:
    print("ÇAKIŞMA (kesilmedi):", c)
```

"ÇAKIŞMA" satırları şu durumu gösterir: çıkarılacak söz, tutulacak sözle arada sessizlik olmadan bağlı. Bunları kelimenin ortasından kesme; kullanıcıya listele.

### Kontrol

Kesilmiş sesi yeniden kur ve tekrar transkript et. Hiçbir kelime yarım kalmamalı, metin akıcı okunmalı. Bu adım bir render değildir, yalnızca sesle yapılan bir kontrol.

```bash
F=$(python3 -c "import json;d=json.load(open('cuts.json'));print('+'.join(f'between(t,{a/30:.4f},{b/30:.4f})' for a,b in d['cuts']))")
ffmpeg -i ses.wav -af "aselect='$F',asetpts=N/SR/TB" kontrol.wav
<venv-yolu>/bin/python -I transcribe.py kontrol.wav kontrol.json tr <model>
```

Kullanıcıya şunları raporla:
- yeni süre
- çıkarılan her parça: zamanı, sözleri ve sebebi
- çakışmalar
- kendine düşülmüş notlar

Kullanıcının kendi sesine kesim dışında hiçbir ses işlemi (seviye, EQ, gürültü azaltma, fade) uygulama.

### Remotion'da uygula

Videoyu `public/footage/` altına koy (ya da sembolik bağlantı ver). Parçaları `Series` ile arka arkaya diz. `trimBefore` ve `trimAfter` kompozisyonun fps'i cinsinden karedir; kaynak videonun fps'i farklıysa `cuts.py` içindeki `FPS` değerini kompozisyonla aynı yap. JSON'u import edebilmek için `tsconfig.json` içinde `"resolveJsonModule": true` olmalı.

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

**Grafikler ve altyazı:** kinetik yazıları, kartları ve altyazıyı kesim sonrası zamana bağla. Bir kelimenin yeni zamanı şöyle hesaplanır:

`yeni kare = (kelime saniyesi × fps − parçanın a değeri) + o parçadan önceki parçaların toplam uzunluğu`

## 6. Görsel dil

Kullanıcı kendi marka paletini verirse onu kullan; vermezse aşağıdaki paleti kullan.

### Palet

| Ad | Değer | Kullanım |
| --- | --- | --- |
| black | `#000000` | shader / ses sahneleri |
| ink | `#0B0B10` | açık zemin üstünde başlık, çatlak çizgisi |
| cream | `#F5F2EE` | açık sahne zemini, koyu zeminde başlık |
| deep → indigo | `#05040C` → `#120E2E` → `#2A1F63` → `#43307F` | uzay gradyanı (yukarıdan aşağı) |
| violet | `#6B5BD2` | nebula, ışıma |
| coral | `#FF5A4E` | eyebrow, vurgu kelimesi, buton |
| peach → coral → terracotta | `#FFB199` → `#FF5A4E` → `#D97757` | vurgu gradyanı: `linear-gradient(180deg, #FFB199 0%, #FF5A4E 45%, #D97757 100%)`, kelimeye `background-clip: text` ile |

### Fontlar

- **Başlık:** [Inter Tight](https://fonts.google.com/specimen/Inter+Tight) 900 / 800 / 700.
- **Metin:** [Inter](https://fonts.google.com/specimen/Inter) 400–600.
- **Mono:** `SF Mono, Menlo, ui-monospace, monospace` (eyebrow, sayaç, dosya adları).
- Yükleme kodu:
  ```ts
  import {loadFont as loadTight} from '@remotion/google-fonts/InterTight';
  import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
  export const display = loadTight('normal', {weights: ['700', '800', '900'], subsets: ['latin', 'latin-ext']}).fontFamily;
  export const body = loadInter('normal', {weights: ['400', '500', '600'], subsets: ['latin', 'latin-ext']}).fontFamily;
  ```
  Türkçe ve diğer Latin dışı karakterler için `latin-ext` alt kümesini mutlaka ekle.

### Tipografi (1080×1920)

- **Sahne başlığı:** 150 px, Inter Tight 900, `letterSpacing: -0.045em`, `lineHeight: 0.95`. Sola hizalı (`left: 90`), iki satır, her satır ayrı maskeyle girer.
- **Eyebrow:** başlığın üstünde. Mono 38 px, coral, `letterSpacing: 0.2em`, biçim `01 — PROMPT`.
- **Hook kelimeleri:** 170–190 px, ortalı.
- **Alt satır:** Inter 600, 58 px, kelime kelime; son kelime coral.
- **Güvenli alan** (Reels arayüzü için): yanlar 90 px, üst metin y ≥ 300, alt içerik y ≤ 1540.

## 7. Hareket kalıpları

`src/components/kit.tsx` içine koy:

```tsx
import React from 'react';
import {Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame} from 'remotion';

const FPS = 30;
// Her sahne kesimden OVER kare önce başlar; yeni sahne eskisinin üstüne katman olarak biner.
export const OVER = 8;
export const useCut = () => useCurrentFrame() - OVER; // geçiş sırasında negatif
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export const spr = (f: number, delay = 0, config: Partial<{damping: number; stiffness: number; mass: number}> = {}) =>
  spring({frame: f - delay, fps: FPS, config: {damping: 14, stiffness: 170, mass: 0.7, ...config}});

// RGB split gölgesi
export const chroma = (amt: number) =>
  amt < 0.3 ? 'none' : `${amt}px 0 rgba(255,50,90,0.85), ${-amt}px 0 rgba(40,200,255,0.85)`;

// Sesin vurgu anı (trim'den `peak` saniye sonra) tam `at` karesine düşer.
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

// Satır, maskenin arkasından kayarak gelir.
export const MaskUp: React.FC<{f: number; delay: number; children: React.ReactNode}> = ({f, delay, children}) => {
  const s = spr(f, delay, {damping: 16, stiffness: 150});
  return (
    <div style={{overflow: 'hidden', padding: '0.04em 0 0.1em'}}>
      <div style={{transform: `translateY(${(1 - s) * 115}%) rotate(${(1 - s) * 4}deg)`, transformOrigin: 'left bottom'}}>{children}</div>
    </div>
  );
};

// Kelime büyükten oturur: blur + RGB split söner, 2–4. karelerde kısa glitch.
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

**Sahne sıralaması (`Reel.tsx`):** her sahneyi `<Sequence from={kesim - OVER} durationInFrames={sonrakiKesim - kesim + OVER}>` içine koy. İlk sahne için `from` negatif olabilir. Sahne içinde `const f = useCut()` kullan; `f < 0` geçiş anıdır.

**Kurallar:**
- **Spring ayarları:** sert giriş için `stiffness 190–420`, yumuşak morph için `damping 20–22, stiffness 80–90`.
- **Kamera:** her sahnede sürekli zoom olsun. İçerik `1 → 1.06–1.10`, arka plan `1.12–1.25 → 1` (ters yönde parallax).
- **Stagger:** satırlar arasında 4–5 kare, kartlar arasında 1,2–2 kare.

## 8. Geçişler

Hepsi gelen sahnenin kök elemanına uygulanır. `w` ve `r`, `interpolate(f, [-OVER, 2], [0, 1], clamp)` ile 0'dan 1'e gider.

| Geçiş | Kod | Ses |
| --- | --- | --- |
| **Çapraz wipe** | `clipPath: polygon(0 ${100 - w*130}%, 100% ${130 - w*130}%, 100% 100%, 0 100%)` | büyük whoosh, vurgu kesimden 2 kare önce |
| **Daire açılış** | `clipPath: circle(${r*130}% at 50% 62%)`, ease-in quad | orta whoosh, vurgu kesimden 2 kare önce |
| **Alttan dönerek gelme** | `translateY((1-r)*1920px) rotate((1-r)*8deg)` + `blur((1-r)*18px)`, ease-out cubic | kısa whoosh |
| **Yandan whip-pan** | `translateX((1-r)*1080px)` + `blur((1-r)*24px)` | kısa whoosh |
| **Beyaz flash** | tam ekran beyaz katman, opaklık `[t-4, t, t+18] → [0, 1, 0]` | kamera flaşı; riser'ın bitişi bu kareye hizalı |
| **Buz çatlağı → shard açılış** | aşağıda | buz kırılması + kısa whoosh |

**Buz çatlağı (eski sahnenin son 8 karesi):** ekran merkezinden 9 kırık SVG yol çiz.
- Her yol 6 segment × 210 px; açı jitter'ı ±0,3 rad (`random()` ile deterministik).
- Çizim: `pathLength={1}`, `strokeDasharray={1}`, `strokeDashoffset={1 - p}`, renk `#0B0B10`, 5 px.
- Aynı anda sahne 2 px'ten 12 px'e kadar sarsılır: `Math.sin(f * 4) * genlik`.

**Shard açılış (yeni sahne):** 18 köşeli düzensiz bir polygon, ease-out cubic ile büyür:

```ts
const shardClip = (p: number) => `polygon(${new Array(18).fill(0).map((_, i) => {
  const a = (i / 18) * Math.PI * 2;
  const r = p * 1700 * (0.7 + random(`sh${i}`) * 0.6);
  return `${540 + Math.cos(a) * r}px ${960 + Math.sin(a) * r}px`;
}).join(',')})`;
```

## 9. Sahne kalıpları

**Shader hook:** siyah zemin, 21st.dev Shader Animation'ın WebGL karşılığı. 1–2 kelime `Pop` ile girer.
- Canvas'a `preserveDrawingBuffer: true` ver ve her karede `useLayoutEffect` içinde çiz.
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
- Halka yarıçapı `fract(t) × 5`'tir. Sahne boyunca `t` değerini 0,02'den 0,42'ye götür, `z = 1`, `g ≈ 1.4` kullan.

**Problem sahnesi ("Saatlerce timeline."):**
- Krem zemin üzerinde 16 "timeline klibi" kartı uçuşur. Kartlar beyaz, `r18`; sol kenarda 16 px pastel şerit, üstte mono `clip_XX.mov`, altta keyframe elmasları.
- Kartlar yukarıdan düşerek girer (stagger 1,2 kare), sonra süzülür, döner ve ±3 px titrer.
- Yazının arkasında krem renkli radial bir perde var; okunaklılığı o sağlar.
- Üstte coral mono sayaç (`⏱ 03:12:47`) hızla akar.
- Ses: saat tik-takı. Sahne buz çatlağıyla biter.

**Prompt sahnesi:**
- Uzay gradyanı zemin, yıldızlar, iki katman dağ silüeti (parallax). Üstünde cam efektli bir prompt kutusu:
  - `rgba(255,255,255,.16 → .05)` gradyan, 1,5 px beyaz %25 kenar, `backdrop-filter: blur(30px)`, `r44`.
- Etkileşim sırası:
  1. Kare başına bir harf daktilo efekti, coral imleç.
  2. İmleç gönder butonuna süzülür.
  3. Tıklamada buton `scale 1 → 0.82 → 1` yapar, kutu coral parlar.
  4. Krem renkli bir yanıt toast'ı iner.
- Ses: klavye → mouse click → bildirim.

**Kart morph'u (Scroll Morph):**
- Beyaz zemin, 12 kart (150×200, `r22`).
- **Faz 1:** her kart `spr(f, 6 + 2i, {damping 16, stiffness 130})` ile rastgele konumdan çembere oturur (yarıçap 360, merkez 540, 1060). Kart açısı teğete dönük, çember yavaş döner.
- **Faz 2:** `spr(f, 34, {damping 22, stiffness 80})` ile yarıçap 580'e, merkez y 1560'a, açı aralığı 2π'den 1,05π'ye gider ve çember gökkuşağı yayına dönüşür.
- Ses: kartlar oturdukça 6 karede bir pop; sonunda ding.

**Ritim / ses senkronu:**
- 40 barlık bir dalga formu her beat'te pulse atar. 3 kesim işareti tepe noktalarına "snap" olur.
- Her snap'te pop sesi, mikro sarsıntı ve RGB split olur.

**Sayaç / render:**
- Dev bir odometre (%000 → %100): ondalık değeri sürekli kayan rakam sütunları; baştaki sıfırlar soluk.
- Altta gradyan progress çizgisi var. %100'de beyaz flash patlar.

**Kapanış (Horizon):**
- Uzay gradyanı, nebula, yıldızlar, dağ silüeti ve dağın tepesinden yükselen dikey bir ışık huzmesi.
- Kamera dağdan yukarı tilt yapar. Dev wordmark harf harf aşağıdan gelir (stagger 2,5 kare), mercan gradyanlı.
- Tagline maskeyle girer. Tagline girerken huzmenin opaklığını 0,2'ye düşür, yoksa yazının üstünden geçer.

## 10. Ses tasarımı

Efektleri dosya adına göre değil, **türüne** göre eşle ve her birinin vurgu anını ölç (bkz. bölüm 2). Pixabay'de aşağıdaki aramalar iyi sonuç verir:

| Tür (Pixabay araması) | Kullanım | Tipik vurgu | Seviye |
| --- | --- | --- | --- |
| whoosh (kısa) | slide, whip-pan | 0,1–0,2 sn | 0,45–0,7 |
| whoosh (uzun) | büyük wipe | 0,6–0,9 sn | 0,4–0,7 |
| pop | kelime ya da kart oturması, snap | 0,1–0,2 sn | 0,5–0,9 |
| ding | bölümün tamamlanması | ~0,1 sn | 0,6–0,7, fade 6–8 kare |
| notification | yanıt toast'ı, logo oturması | ~0,1 sn | 0,75 |
| mouse click | buton tıklaması | ~0,02 sn | 0,9 |
| keyboard typing | daktilo efekti | ilk tuşa `trim` ile atla | 0,6, fade 4 kare |
| clock ticking | gerilim, "saatlerce" | — | 0,45, fade 6 kare |
| ice crack / glass crack | ekranın kırılması | en sert kırılmanın kısa bir kesiti (`trim`) | 0,95, fade 8 kare |
| riser | kapanış öncesi yükselme | bitişi flash karesine hizala | 0,8 |
| camera flash | beyaz flash | ~0,15 sn | 0,9 |

Kullanım örnekleri:

```tsx
<Sfx name="whoosh-2" at={kesim - 2} peak={0.85} vol={0.7} dur={50} />
<Sfx name="ice-crack" at={kesim - 8} trim={5.12} peak={0.1} vol={0.95} dur={22} fadeOut={8} />
```

- **Seviye ve fade:** efektlerin seviyesi, kırpması ve fade'i serbestçe ayarlanabilir. Kullanıcının kendi anlatım sesi varsa ona efekt, EQ ya da seviye uygulama; isterse kendisi yapar.
- **Müzik:** kesimleri beat'e oturt, efektleri müziğin altında kalmayacak seviyede tut.

## 11. Önizleme ve kontrol

1. **Studio'yu aç:** `npx remotion studio`. Desktop uygulamasında `.claude/launch.json` dosyası yaz ve `preview_start` kullan; port olarak örneğin 3123 ver ve `--no-open` ekle.
2. **Kareleri kendin kontrol et:** kritik karelerden (her sahnenin ortası ve geçiş anları) still al, sonra hepsini yan yana birleştirip bak:
   ```bash
   npx remotion still <Comp> kare.jpg --frame=N --scale=0.4 --gl=angle
   ffmpeg -i a.jpg -i b.jpg -i c.jpg -filter_complex "hstack=3" sheet.jpg
   ```
   Şunlara bak: yazı güvenli alanda mı, okunaklı mı, Türkçe karakterler doğru mu, ilk kare siyah mı (Reels kapağı için boş kalmasın), shader görünüyor mu.
3. **Kullanıcıya göster:** Studio adresini ver; zaman göstergesi `dakika:saniye.kare` biçimindedir (`00:01:23` = 1 sn 23 kare). Kullanıcı bu zamanlarla revize verirse kareye çevirip uygula.

## 12. Render

Yalnızca kullanıcı son onayı verdikten sonra render al:

```bash
npx remotion render <Comp> out/video.mp4 --gl=angle
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration -of compact out/video.mp4
ffmpeg -i out/video.mp4 -af volumedetect -f null - 2>&1 | grep max_volume
```

Çıktının 1080×1920, 30 fps ve doğru süre olduğunu doğrula; ses tepe seviyesi 0 dB'nin altında olmalı. Birkaç karelik contact sheet ile görüntüye son kez bak. Sesleri kulakla dinleyemediğini kullanıcıya açıkça söyle.

## Tuzaklar

- **Shader yalnızca gri çapraz çizgi gösteriyorsa:** halka ekran dışındadır. `t` değerini küçült (yarıçap `fract(t) × 5`).
- **Shader çok parlaksa:** `g` değerini 5'ten 1,4'e indir.
- **GLSL:** döngü içinde vektörü dinamik indeksleme (`c[j]`); her kanalı ayrı bir fonksiyonla hesapla.
- **Render'da shader boş çıkıyorsa:** `--gl=angle` ekle ve canvas'a `preserveDrawingBuffer: true` ver.
- **Rastgelelik:** `Math.random()` kullanma; render kareleri farklı çıkar. Remotion'ın `random('seed')` fonksiyonunu kullan.
- **Gradyan yazı:** `background-clip: text` olan yazıya `text-shadow` verme; gölge yazının içinden görünür. Bu yazılarda yalnızca blur ve scale kullan.
