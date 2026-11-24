# Montaj Engine v3 — sənəd

Məqsəd: Drive linkindən paylaşılmağa hazır video. Hər mərhələ ayrıca modul, hər birinin nəticəsi ölçülür, keçməyən video FINAL-a düşmür.
Ehtiyat nüsxə: git tag `backup-pre-engine-v3` (dəyişikliklərdən əvvəlki vəziyyət).

## Axın

```
video ─▶ disfluency.py (ASR + yarımçıq dubl/ıı/söhbət + MMS dəqiq sərhəd) ─▶ keep.json, review.md
      ─▶ color_auto.py (bu videonun ölçülmüş rəngi, HDR→SDR)
      ─▶ kəsim + kadraj (ffmpeg) ─▶ audio_pro.py (ölçülmüş təmizləmə + studio zənciri, −14 LUFS)
      ─▶ ASS altyazı (brend rəngi) ─▶ motion.py (Remotion overlay) ─▶ clean.mp4 + final.mp4
      ─▶ qc_render.py (kadraj, qrafika-üz, rəng, səs, klik, export) ─▶ timeline_export.py (.otio, Premiere XML, Resolve FCPXML)
      ─▶ deliver.py (Final Videos / Covers / Captions / Quality Control + status)
```
Bir video: `python3 engine.py <video> --client <müştəri> --name NN_ad [--title "Sətir|Sətir"]` → `engine.json` (mərhələ vaxtları + QC).
PRO kart sistemi (build.py) eyni modulları istifadə edir: `look: auto`, `autoCut`, `qc_render` darvazası.

## Audit — niyə problemlər olurdu (ölçülüb)

| problem | səbəb | həll |
|---|---|---|
| cümlə/heca sonu kəsilirdi, yarımçıq dubl qalırdı | VAD-lı Whisper yarımçıq dublu düzgün dublla bir cümlə yazırdı; söz vaxtları ±0.1–0.3 s; kəsim sükut detektoru ilə | `disfluency.py`: VAD-sız ASR + MMS forced alignment (söz sonu −54 dB sükutda, Whisper −36 dB) + səs dalğasında ən sakit nöqtə |
| səs boğuq/metalik | hər videoya eyni güclü DeepFilterNet (20–30 dB) | `audio_pro.py`: küy ölçülür → 0/8/12/18 dB; boğuqluq (3–8 kHz payı) ölçülüb düzəldilir: 0.0065 → 0.044 |
| sərt limiter klik yaradırdı | ffmpeg alimiter böyük qazancda | qazanc → sürətli kompressor → yumşaq tanh tavan (ölçü: 403 → 2 real klik) |
| altyazı səhvi | ASR yazılışı birbaşa altyazıya gedirdi | `glossary_az.json` + QC yazılış yoxlaması; insan/Claude redaktəsi `review.md`-də |
| rəng bəzən tətbiq olunmurdu | `look` konfiqdə yazılmasa heç bir rəng filtri yox idi | `look: auto` standart, hər video ayrıca ölçülür |
| kadr yuxarıda boş / çox yaxın | kadraj yoxlanmırdı | `qc_render` frame: baş üstü ≤0.36, üz hündürlüyü ≤0.30 (istifadəçi rəyi ilə kalibrlənib) |
| stiker üzə düşürdü | qrafika üz yoxlaması bloklamırdı | `qc_render --clean`: piksel fərqi ilə üz qutusu örtülməsi > 10% → FAIL |
| faster-whisper fayl açmırdı | `av` 19 quraşdırılıb, faster-whisper 1.2.1 `av<17` tələb edir | modullar səsi numpy kimi ötürür |

## Araşdırma və seçim

| sahə | baxılan | seçilən | quraşdırıldı? | niyə / sınaq |
|---|---|---|---|---|
| ASR (az) | Whisper large-v3, large-v3-turbo, MMS ASR | **large-v3-turbo** (mövcud) | var | real klipdə turbo 23 s, large-v3 109 s; keyfiyyət fərqi yox |
| söz vaxtı | Whisper, WhisperX (az align modeli yoxdur), **MMS_FA** | **torchaudio MMS_FA** | ✔ | 1100+ dil, az daxil; söz sərhədi sükuta düşür |
| səs ayırma | Demucs htdemucs, DeepFilterNet, RNNoise (arnndn) | DeepFilterNet (ölçülmüş) + Demucs (yalnız musiqi/kənar səs olanda) | ✔ ikisi də | Demucs CPU-da yavaşdır → `--isolate` ilə |
| studio audio | ffmpeg filtrləri, **pedalboard** (Spotify) | pedalboard + ffmpeg deesser | ✔ | EQ/kompressor/qapı peşəkar keyfiyyətdə, sürətli |
| LUFS | ffmpeg loudnorm, **pyloudnorm** | pyloudnorm (iki keçid) | ✔ | inline loudnorm sonu kəsirdi |
| rəng | sabit preset, OpenColorIO, LUT | **color_auto** (ölçü əsaslı ffmpeg zənciri) + zscale HLG/PQ→709 | ✔ (öz modul) | OCIO iPhone profili üçün əlavə dəyər vermədi; `lut3d` hazırdır |
| motion graphics | Remotion (repoda var), HyperFrames, Blender, ffmpeg drawtext | **Remotion** (spring, maska, hərəkət bulanıqlığı) | ✔ repoda | 3 s overlay = 12 s CPU; şəffaf ProRes 4444 |
| NLE eksport | OTIO, EDL, AAF | **OpenTimelineIO** → FCP7 XML (Premiere), FCPXML (Resolve) | ✔ | 21 klip yazıldı və geri oxundu (Premiere-də açılış sınanmayıb) |
| səhnə/dubl | PySceneDetect | PySceneDetect | ✔ | çox kameralı/kadr dəyişən çəkilişlər üçün |
| üz | MediaPipe BlazeFace | (mövcud) `facedet.py` | var | — |
| optical flow / slow-mo | ffmpeg minterpolate, RIFE | ffmpeg minterpolate | var | RIFE GPU tələb edir |
| rotoscoping, mətn obyekt arxasında | MediaPipe selfie segmenter (repoda `montaj/background.py`) | mövcud seqmentator | var | — |

## Lisenziya qeydləri
- **Remotion**: fərdi şəxs və ≤3 işçili şirkət üçün pulsuz; daha böyük komandada şirkət lisenziyası lazımdır.
- **pedalboard**: GPL-3.0 — daxili istifadə üçün problem yoxdur; kodu paylayanda GPL şərtləri.
- **Demucs, PySceneDetect, OTIO, pyloudnorm**: MIT/BSD/Apache.
- **MMS**: CC-BY-NC 4.0 (Meta) — model çəkiləri qeyri-kommersiya lisenziyasındadır. Ona görə STANDART SÖNDÜRÜLÜB; `MONTAJ_MMS=1` və ya `--mms` ilə açılır (istifadəçi təsdiqi lazımdır).
- Musiqi: Mixkit (pulsuz lisenziya, kommersiya daxil).

## Məhdudiyyətlər
- GPU yoxdur (4 nüvəli CPU) → hardware encoding, RIFE, böyük modellər yoxdur.
- Premiere/Resolve-da faktiki açılış sınanmayıb (fayllar OTIO ilə yazılıb və geri oxunub).
- Mövzu bölgüsü, ən yaxşı dubl seçimi və mövzudan kənar hissələrin son qərarı Claude-un `review.md` yoxlamasıdır (avtomatik təkliflərlə).

## Faktiki ölçmələr (4 nüvəli CPU, video kartsız, 14.11.2026, real iPhone talking-head videoları)

| versiya | paket | ümumi vaxt | 1 dəq hazır video üçün |
|---|---|---|---|
| əvvəlki xüsusi skript | 6 video | ~50 dəq | ~7 dəq |
| engine v3 ilk (ardıcıl, 2 dəfə kodlama) | 3 video, 2.8 dəq | 13.5 dəq | 4.5 dəq |
| + tək keçidli render, QC 2 s, 2 paralel xətt | 5 video, 6.6 dəq | 19.3 dəq | 2.9 dəq |
| + ASR ardıcıl ön keçid, veryfast/bicubic | 5 video, 6.4 dəq | 16.8 dəq | 2.6 dəq |

Mərhələ payı (son ölçü, 1 video): ASR+plan 32–58 s · rəng 3–4 s · səs 6–33 s · motion 11 s (keşdə 0) · **render 130–320 s** · QC 41–112 s.
20 videoluq paket üçün (orta 1.3 dəq video) ekstrapolyasiya: ~65–70 dəq — ölçülməyib, 5 videodan hesablanıb.
Darboğaz render-dir (CPU-da HEVC dekod + x264 kodlama); növbəti real sıçrayış GPU (NVENC/NVDEC) tələb edir.
