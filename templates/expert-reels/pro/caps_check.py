"""Mühitin faktiki imkan yoxlaması (AI prodakşn sənədi: "Başlanğıc yoxlaması").
Hər funksiya real kiçik sınaqla yoxlanır; nəticə caps_report.json və ekrana.

İstifadə:  python3 caps_check.py [nümunə_video.mov] [iş_qovluğu]
Nümunə video verilməzsə test videosu sintez olunur.
"""
import json, os, subprocess, sys, time, difflib, re
from pathlib import Path
A = Path(__file__).resolve().parent; sys.path.insert(0, str(A))
import avkit as K

W = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/caps_check"); W.mkdir(parents=True, exist_ok=True)
R = {}
def check(name, fn):
    t0 = time.time()
    try: ok, note = fn()
    except Exception as e: ok, note = False, f"{type(e).__name__}: {str(e)[:160]}"
    R[name] = {"işləyir": ok, "qeyd": note, "san": round(time.time() - t0, 1)}
    print(f"{'✅' if ok else '❌'} {name:28s} {R[name]['san']:6.1f}s  {note}")

SRC = sys.argv[1] if len(sys.argv) > 1 else None
if not SRC:
    SRC = str(W / "synth.mp4")
    K.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=4", "-f", "lavfi", "-i", "sine=f=440:d=4", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", SRC])

def video_analysis():
    p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration", "-of", "json", SRC], capture_output=True, text=True).stdout)
    v = [s for s in p["streams"] if s["codec_type"] == "video"][0]
    K.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", SRC, "-frames:v", "1", str(W / "frame.jpg")])
    return True, f"{v['codec_name']} {v['width']}x{v['height']} {v['r_frame_rate']} fps, {float(p['format']['duration']):.1f}s, kadr çıxarıldı"
check("video analizi", video_analysis)

WAV = W / "a.wav"; K.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-t", "15", "-vn", "-ac", "1", "-ar", "16000", str(WAV)])
def scribe(path):
    r = subprocess.run(["curl", "-sS", "-X", "POST", "https://api.elevenlabs.io/v1/speech-to-text", "-H", f"xi-api-key: {os.environ.get('ELEVENLABS_API_KEY', '')}",
                        "-F", "model_id=scribe_v1", "-F", "language_code=aze", "-F", "timestamps_granularity=word", "-F", f"file=@{path}"], capture_output=True, text=True).stdout
    d = json.loads(r); return d
def stt_scribe():
    d = scribe(WAV)
    if "words" not in d: return False, str(d)[:160]
    return True, f"ElevenLabs Scribe (aze): {len([w for w in d['words'] if w.get('type') == 'word'])} söz, söz vaxtları var"
check("transkript (Scribe)", stt_scribe)
def stt_whisper():
    import numpy as np
    from faster_whisper import WhisperModel
    pcm = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(WAV), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout, np.float32)
    segs, _ = WhisperModel("small", compute_type="int8").transcribe(pcm, language="az", word_timestamps=True)
    n = sum(len(s.words) for s in segs)
    return True, f"faster-whisper small (raw PCM): {n} söz — Azərbaycan dilində keyfiyyət zəifdir, yalnız ehtiyat"
check("transkript (lokal ehtiyat)", stt_whisper)

def framing():
    K.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-t", "2", "-vf", "crop=iw*0.8:ih*0.8:iw*0.1:ih*0.05,scale=1080:1920", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(W / "crop.mp4")])
    return True, "ffmpeg kəsim + miqyas (brend kitindəki kadraj)"
check("kadraj", framing)
def subtitles():
    ass = W / "t.ass"; ass.write_text("[Script Info]\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: S,Montserrat,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,1,2,80,80,560,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:00.00,0:00:02.00,S,,0,0,0,,Əə Şş Ğğ Iı İi Çç Öö Üü\n")
    K.ensure_font("Montserrat")
    K.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-t", "2", "-vf", f"subtitles={ass}", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(W / "sub.mp4")])
    return True, "libass + Montserrat, Azərbaycan hərfləri (vizual yoxlama: sub.mp4)"
check("subtitr", subtitles)
def motion():
    r = subprocess.run(["node", "-e", "require('playwright').chromium.launch().then(b=>b.close()).then(()=>console.log('ok'))"], capture_output=True, text=True, timeout=60)
    return "ok" in r.stdout, "Playwright/Chromium (HTML qrafika → kadr) + libass animasiya"
check("motion qrafika", motion)
def segmentation():
    import numpy as np, cv2, mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    mdl = Path.home() / ".cache/mp/selfie_segmenter.tflite"
    if not mdl.exists():
        mdl.parent.mkdir(parents=True, exist_ok=True)
        K.run(["curl", "-sS", "-o", str(mdl), "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"])
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path=str(mdl)), output_confidence_masks=True))
    rgb = cv2.cvtColor(cv2.imread(str(W / "frame.jpg")), cv2.COLOR_BGR2RGB)
    m = np.squeeze(seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)).confidence_masks[0].numpy_view())
    return True, f"mediapipe ImageSegmenter: insan payı {float((m > .5).mean()):.0%} — kitabxana işləyir, yaşıl ekran montaj aləti hələ qurulmayıb"
check("fon ayırma (yaşıl ekran)", segmentation)

TXT = "Salam! Bu gün yaddaşı gücləndirən üç sadə üsul haqqında danışacağıq. Əvvəlcə kitabı bağlayın və öyrəndiyinizi xatırlamağa çalışın."
def tts_az():
    out = W / "tts.mp3"
    code = subprocess.run(["curl", "-sS", "-o", str(out), "-w", "%{http_code}", "-X", "POST", "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
                           "-H", f"xi-api-key: {os.environ.get('ELEVENLABS_API_KEY', '')}", "-H", "Content-Type: application/json",
                           "-d", json.dumps({"text": TXT, "model_id": "eleven_multilingual_v2"})], capture_output=True, text=True).stdout
    if code != "200": return False, f"HTTP {code}: {out.read_text(errors='ignore')[:120]}"
    d = scribe(out); back = " ".join(w["text"] for w in d.get("words", []) if w.get("type") == "word")
    norm = lambda s: re.sub(r"[^\wəğıöüşç ]", "", s.lower().replace("İ", "i").replace("I", "ı"))
    sim = difflib.SequenceMatcher(None, norm(TXT), norm(back)).ratio()
    return sim > 0.85, f"ElevenLabs multilingual_v2 → geri transkript oxşarlığı {sim:.0%}. Tələffüz qulaqla da yoxlanmalıdır (tts.mp3)"
check("səsləndirmə (Azərbaycan)", tts_az)
def music():
    out = W / "m.mp3"
    code = subprocess.run(["curl", "-sS", "-o", str(out), "-w", "%{http_code}", "-X", "POST", "https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128",
                           "-H", f"xi-api-key: {os.environ.get('ELEVENLABS_API_KEY', '')}", "-H", "Content-Type: application/json",
                           "-d", json.dumps({"prompt": "calm minimal piano, no vocals", "music_length_ms": 10000, "force_instrumental": True})], capture_output=True, text=True).stdout
    if code != "200": return False, f"HTTP {code}: {re.sub(r'\\s+', ' ', out.read_text(errors='ignore'))[:140]}"
    return True, "ElevenLabs music işləyir"
check("musiqi generasiyası", music)
def render():
    K.run(["ffmpeg", "-v", "error", "-y", "-i", str(W / "sub.mp4"), "-i", str(WAV), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
           "-maxrate", "4.5M", "-bufsize", "9M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(W / "final.mp4")])
    q = K.qa(W / "final.mp4"); return True, f"H.264/AAC MP4, QA: {q['kadr']} kadr, {q['MB']} MB"
check("MP4 render + QA", render)
def ai_video():
    keys = [k for k in ("FAL_KEY", "HEYGEN_API_KEY", "RUNWAY_API_KEY", "REPLICATE_API_TOKEN", "MAGNIFIC_API_KEY", "OPUSCLIP_API_KEY") if os.environ.get(k)]
    return bool(keys), ("açar var: " + ", ".join(keys)) if keys else "AI video / Magnific / OpusClip açarı yoxdur"
check("AI video generasiyası", ai_video)

json.dump(R, open(W / "caps_report.json", "w"), ensure_ascii=False, indent=1)
print("hesabat:", W / "caps_report.json")
