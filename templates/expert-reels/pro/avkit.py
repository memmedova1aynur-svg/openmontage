"""Ümumi səs və ixrac alətləri (talk.py, editorial.py, game.py istifadə edir).

Qaydalar bu həftənin dərslərindən gəlir:
- Instagram ixracı yüngül olsun (≤4.5 Mbit/s, ~25–35 MB): ağır fayllar yüklənəndə ilişir.
- Təsdiqlənmiş versiyanın üstünə yazılmır: hər ixrac yeni _vN alır.
- Səs: danışıq −16 LUFS-ə hazırlanır, musiqi danışıq altında ≈ −29 dBFS RMS, final −14 LUFS / TP −1.5.
"""
import json, re, subprocess
from pathlib import Path
import numpy as np

SR = 48000


def run(cmd):
    subprocess.run(cmd, check=True)


def probe_dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True).stdout)


def next_version(path):
    """out/Ad.mp4 → out/Ad_v1.mp4, _v2 … — mövcud faylın üstünə heç vaxt yazmır."""
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    k = 1
    while (p.parent / f"{p.stem}_v{k}{p.suffix}").exists(): k += 1
    return p.parent / f"{p.stem}_v{k}{p.suffix}"


def load(f, ch=2, sr=SR):
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", str(ch), "-ar", str(sr), "-f", "f32le", "-"],
                                     capture_output=True).stdout, np.float32)
    return a.reshape(-1, ch).astype(np.float64)


def save(a, f, sr=SR):
    raw = Path(str(f) + ".f32"); a.astype(np.float32).tofile(raw)
    run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", str(a.shape[1]), "-i", str(raw), str(f)]); raw.unlink()


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)


SPEECH_CHAIN = "highpass=f=80,afftdn=nf=-30,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=2"


def loudnorm_2pass(src, out, I=-16, TP=-1.5, LRA=9, pre="", post=""):
    """İki keçidli loudnorm (dəqiq hədəf). pre: əvvəlcə tətbiq olunan filtr zənciri."""
    pre = (pre + ",") if pre else ""
    s = subprocess.run(["ffmpeg", "-v", "info", "-i", str(src), "-af", f"{pre}loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = json.loads(s[s.rfind("{"):s.rfind("}") + 1])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
         f"{pre}loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
         f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true" + ("," + post if post else ""), "-ar", str(SR), str(out)])


def music_bed(mus, n, speech_mask=None, level=-29.0, duck_db=4.0, fade_in=1.2, fade_out=1.9, end_up=None):
    """Musiqi zərfi: yumşaq giriş/çıxış, danışıq altında ducking, danışıq olan yerdə RMS = level dBFS.
    mus: (N,2) massiv; speech_mask: (n,) bool; end_up: (başlanğıc_s, +dB) son kartda yüksəlmə."""
    o = np.zeros((n, 2)); o[:min(n, len(mus))] = mus[:n]
    t = np.arange(n) / SR; T = n / SR
    env = np.clip(t / fade_in, 0, 1) ** 1.5 * np.clip((T - t) / fade_out, 0, 1) ** 1.3
    if end_up: env *= 1 + (10 ** (end_up[1] / 20) - 1) * np.clip((t - end_up[0]) / 0.6, 0, 1)
    if speech_mask is not None and speech_mask.any():
        k = int(0.25 * SR); sm = np.convolve(speech_mask.astype(float), np.ones(k) / k, mode="same")
        env *= 10 ** (-duck_db * sm / 20)
        sel = speech_mask & (t > min(3, T * .1)) & (t < T - 2)
        ref = rms_db((o * env[:, None])[sel if sel.any() else speech_mask])
    else:
        ref = rms_db(o * env[:, None])
    return o * env[:, None] * 10 ** ((level - ref) / 20)


def place_sfx(out, sfx_list):
    """sfx_list: [(fayl, saniyə, səviyyə_dBFS_RMS)] — səsli hissənin RMS-i səviyyəyə bərabər edilir."""
    n = len(out)
    for f, at, lvl in sfx_list:
        a = load(f); i = int(at * SR); m = min(len(a), n - i)
        if m <= 0: continue
        a = a[:m]; nz = np.abs(a).max(1) > 1e-4
        g = 10 ** ((lvl - rms_db(a[nz] if nz.any() else a)) / 20)
        fade = np.ones(m); fo = min(m, int(0.08 * SR)); fade[-fo:] = np.linspace(1, 0, fo)
        out[i:i + m] += a * g * fade[:, None]
    return out


def finalize(mix_wav, out_wav, I=-14, TP=-1.5):
    """Limiter + iki keçidli xətti loudnorm → yayım səviyyəsi."""
    # son limiter: AAC kodlaması pikləri ~1 dB qaldırır, ona görə −2.5 dBFS-də tutulur
    loudnorm_2pass(mix_wav, out_wav, I=I, TP=TP, LRA=11, pre="alimiter=limit=0.84:attack=3:release=60:level=false",
                   post="alimiter=limit=0.75:attack=2:release=50:level=false")


def export_ig(video_in, audio_in, out, copy_video=False):
    """Instagram üçün yüngül, etibarlı ixrac. copy_video=True: video artıq düzgün kodlanıbsa yenidən kodlama."""
    v = ["-c:v", "copy"] if copy_video else ["-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "4.5M", "-bufsize", "9M",
                                              "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-r", "30", "-g", "60"]
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video_in), "-i", str(audio_in), "-map", "0:v", "-map", "1:a", *v,
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", "-map_metadata", "-1", str(out)])
    return out


def qa(f):
    """Kadr sayı, müddət, LUFS, pik, ölçü."""
    d = probe_dur(f)
    vd = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=duration", "-of", "csv=p=0", str(f)],
                              capture_output=True, text=True).stdout.strip() or d)
    n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True).stdout.strip()
    s = subprocess.run(["ffmpeg", "-i", str(f), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", s); pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", s)
    r = {"fayl": Path(f).name, "san": round(d, 2), "kadr": int(n or 0), "kadr_gözlənən": round(vd * 30), "səs_video_fərq": round(d - vd, 2),
         "LUFS": float(I[-1]) if I else None, "pik": float(pk[-1]) if pk else None, "MB": round(Path(f).stat().st_size / 1e6, 1)}
    r["ok"] = abs(r["kadr"] - r["kadr_gözlənən"]) <= 3 and r["səs_video_fərq"] <= 0.25 and (r["pik"] is None or r["pik"] <= -0.5) and r["MB"] <= 60
    return r


def story_clips(video, ranges, outdir, label=None):
    """Hazır videodan story üçün 5–15 s parçalar (9:16, səsli). label: aşağıda kiçik yazı, məs. "Tam video profildə"."""
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True); outs = []
    for k, (a, b) in enumerate(ranges, 1):
        o = outdir / f"{Path(video).stem}_story{k}.mp4"
        vf = "null"
        if label:
            vf = (f"drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:text='{label}':fontsize=40:fontcolor=white"
                  ":box=1:boxcolor=0x0B2A20@0.85:boxborderw=22:x=(w-text_w)/2:y=h*0.82")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(video), "-vf", vf,
             "-af", f"afade=t=in:d=0.15,afade=t=out:st={max(0, b - a - 0.3):.3f}:d=0.3",
             "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(o)])
        outs.append(o)
    return outs


def cover(video, t, out, vf="null"):
    """Üz qabığı kadrı (altyazısız mənbədən götürmək üçün vf ilə kəsim/rəng verilə bilər)."""
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1", "-vf", vf, "-q:v", "2", str(out)])
    return out


# --- sintez SFX (lisenziya problemi yoxdur)
def _env(n, a=.002, dec=.05):
    t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / dec)


def synth(kind):
    """swoosh | pop | ding | buzz | wobble → (N,2) massiv."""
    rng = np.random.default_rng(5)
    def tone(fr, dur, dec): n = int(dur * SR); t = np.arange(n) / SR; return sum(np.sin(2 * np.pi * f * t) * w for f, w in fr) * _env(n, .003, dec)
    if kind == "swoosh":
        n = int(.3 * SR); f = np.linspace(400, 2200, n); s = rng.standard_normal(n) * .4 + np.sin(2 * np.pi * np.cumsum(f) / SR) * .2
        s = np.convolve(s, np.ones(30) / 30, "same") * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    elif kind == "pop": s = tone([(330, 1), (660, .4)], .2, .06)
    elif kind == "ding": s = tone([(880, 1), (1320, .5), (1760, .25)], .9, .25)
    elif kind == "buzz":
        n = int(.45 * SR); t = np.arange(n) / SR; s = np.sign(np.sin(2 * np.pi * 140 * t)) * .5 * _env(n, .004, .18) + np.sin(2 * np.pi * 110 * t) * .5 * _env(n, .004, .2)
        s = np.convolve(s, np.ones(8) / 8, "same")
    elif kind == "wobble":
        n = int(.6 * SR); t = np.arange(n) / SR; s = np.sin(2 * np.pi * (520 + 60 * np.sin(2 * np.pi * 7 * t)) * t) * _env(n, .004, .25)
    else: raise ValueError(kind)
    return np.stack([s, s], 1)


def add_sfx(mix, sig, at, lvl):
    """sig-i at saniyəsinə lvl dBFS RMS səviyyəsində əlavə et."""
    i = int(max(0, at) * SR); m = min(len(sig), len(mix) - i)
    if m <= 0: return mix
    nz = np.abs(sig).max(1) > 1e-4; g = 10 ** ((lvl - rms_db(sig[nz] if nz.any() else sig)) / 20)
    mix[i:i + m] += sig[:m] * g; return mix


def ensure_font(family):
    """Tərzin istədiyi şrift sistemdə yoxdursa Google Fonts-dan ~/.fonts-a yüklə (OFL lisenziyalı)."""
    if not family or family == "Inter": return
    have = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
    if family.lower() in have.lower(): return
    css = subprocess.run(["curl", "-sS", "-A", "Mozilla/4.0", f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}:ital,wght@0,600;0,700;1,600"],
                         capture_output=True, text=True).stdout
    d = Path.home() / ".fonts"; d.mkdir(exist_ok=True)
    for u in re.findall(r"https://[^)]+\.ttf", css):
        subprocess.run(["curl", "-sS", "-o", str(d / Path(u).name), u])
    subprocess.run(["fc-cache", "-f"], capture_output=True)


def cover_first(video, t=None, image=None, frames=3):
    """Üz qabığını videonun ilk kadrlarına yerləşdir (Instagram default üz qabığı = ilk kadr).
    t: videodan götürüləcək kadrın saniyəsi, və ya image: hazır üz qabığı şəkli. Fayl yerində yenilənir."""
    video = Path(video); tmp_img = video.with_suffix(".cover.png"); out = video.with_suffix(".cf.mp4")
    if image is None: run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t or 1.0:.3f}", "-i", str(video), "-frames:v", "1", str(tmp_img)]); image = tmp_img
    d = frames / 30
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{d:.4f}", "-framerate", "30", "-i", str(image), "-i", str(video),
         "-filter_complex", f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[cv];"
                            f"anullsrc=r=44100:cl=stereo,atrim=0:{d:.4f}[ca];[1:v]setsar=1,fps=30,format=yuv420p[mv];[1:a]aresample=44100,alimiter=limit=0.79:attack=2:release=50:level=false[ma];"
                            f"[cv][ca][mv][ma]concat=n=2:v=1:a=1[v][a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "4.5M", "-bufsize", "9M",
         "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-r", "30", "-g", "60", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)])
    out.replace(video); tmp_img.unlink(missing_ok=True)
    return video
