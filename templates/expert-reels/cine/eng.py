"""Kinematik-sənədli səhnə mühərriki (Xəyyam): divar+işıq, kağız, qaranlıq, kəsim lövhəsi;
çərçivəli foto, iri başlıq, kursiv söz, etiket, səpələnmiş sözlər. Tam ekran (RGB) və ya şəffaf (RGBA) kadrlar."""
import numpy as np, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
W, H, FPS = 1080, 1920, 30
F = {'pi': '/root/.fonts/nuFRD-vYSZviVYUb_rj3ij__anPXDTnCjmHKM4nYO7KN_pqTbtY.ttf',
     'pbi': '/root/.fonts/nuFRD-vYSZviVYUb_rj3ij__anPXDTnCjmHKM4nYO7KN_k-UbtY.ttf',
     'pblack': '/root/.fonts/nuFvD-vYSZviVYUb_rj3ij__anPXJzDwcbmjWBN2PKfsukDQ.ttf',
     'm8': '/root/montaj-data/fonts/montserrat-800.ttf', 'm6': '/root/montaj-data/fonts/montserrat-600.ttf'}
_fc = {}
def font(k, s):
    if (k, s) not in _fc: _fc[(k, s)] = ImageFont.truetype(F[k], s)
    return _fc[(k, s)]
GREEN = (108, 197, 126); DARK = (15, 59, 44); WARM = (255, 214, 160)
rng = np.random.default_rng(3)
GRAIN = [Image.fromarray((rng.normal(128, 22, (H // 2, W // 2))).clip(0, 255).astype(np.uint8)).resize((W, H)) for _ in range(6)]
def ease(t): t = min(1, max(0, t)); return t * t * (3 - 2 * t)
def eout(t): t = min(1, max(0, t)); return 1 - (1 - t) ** 3
def az(s): return s.replace('i', 'İ').replace('ı', 'I').upper()

# ---------- fonlar ----------
_bgc = {}
def bg(kind, t, lamp_on=0.0):
    key = kind
    if key not in _bgc:
        y, x = np.mgrid[0:H, 0:W].astype(float)
        if kind == 'wall':
            base = np.zeros((H, W, 3)); base[...] = (22, 30, 26)
            pan = ((x // 180) % 2) * 3 + np.sin(x / 9) * 1.5
            base += pan[..., None]
            base[int(H * 0.82):] = (14, 18, 16)  # döşəmə
            _bgc[key] = base
        elif kind == 'paper':
            n = rng.normal(0, 1, (H // 8, W // 8)); n = np.array(Image.fromarray(((n + 3) * 40).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(float)
            base = np.zeros((H, W, 3)); base[...] = (226, 214, 190); base += (n[..., None] - 120) * 0.12
            _bgc[key] = base
        elif kind == 'dark':
            base = np.zeros((H, W, 3)); base[...] = (11, 14, 13); _bgc[key] = base
        elif kind == 'board':
            base = np.zeros((H, W, 3)); base[...] = (24, 74, 56)
            g = ((x % 60) < 2) | ((y % 60) < 2); g2 = ((x % 300) < 3) | ((y % 300) < 3)
            base[g] = (40, 100, 78); base[g2] = (70, 135, 108); _bgc[key] = base
        elif kind == 'white':
            base = np.zeros((H, W, 3)); base[...] = (232, 230, 224)
            base += (np.sin(y / 4) * 1.2)[..., None]; _bgc[key] = base
    if ('lit', kind) not in _bgc:
        y, x = np.ogrid[0:H, 0:W]
        cone = np.clip(1 - np.abs(x - W / 2) / (120 + y * 0.42), 0, 1) ** 1.6 * np.clip(1 - y / (H * 0.95), 0, 1) ** 0.6
        pool = np.exp(-(((x - W / 2) / 420) ** 2 + ((y - H * 0.42) / 520) ** 2))
        v = np.clip(1 - 0.55 * (((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.7)) ** 2), 0.25, 1)[..., None]
        if kind == 'white': _bgc[('lit', kind)] = (_bgc[key] * 0.75 * v, _bgc[key] * 0.25 * pool[..., None] * v)
        else: _bgc[('lit', kind)] = (_bgc[key] * v, np.array(WARM) * (0.32 * cone + 0.22 * pool)[..., None] * v)
    b0, b1 = _bgc[('lit', kind)]
    k = lamp_on if (kind in ('wall', 'dark', 'white') or lamp_on) else 0
    a = b0 + b1 * k
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

def grain(c, i, amt=0.07):
    g = GRAIN[i % len(GRAIN)]
    return Image.blend(c, Image.merge('RGB', (g, g, g)), amt) if c.mode == 'RGB' else c

# ---------- elementlər (hər biri draw(c, t) ) ----------
class Photo:
    def __init__(s, src, cx, cy, w, at, rot=0, frame=True, label=None, sub=None, dur_in=0.45, grade=0.9, shadow=True, h=None):
        im = Image.open(src).convert('RGB'); im = ImageEnhance.Color(im).enhance(grade)
        if h: im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
        else: im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
        if frame:
            b = 22; fr = Image.new('RGB', (im.width + 2 * b, im.height + 2 * b), (36, 30, 22))
            ImageDraw.Draw(fr).rectangle([6, 6, fr.width - 7, fr.height - 7], outline=(150, 118, 60), width=4)
            fr.paste(im, (b, b)); im = fr
        s.im = im.convert('RGBA'); s.cx, s.cy, s.at, s.rot, s.label, s.sub, s.di, s.shadow = cx, cy, at, rot, label, sub, dur_in, shadow
    def draw(s, c, t):
        if t < s.at: return
        p = eout((t - s.at) / s.di); sc = 1.10 - 0.10 * p + 0.025 * ease((t - s.at) / 4)
        im = s.im.resize((int(s.im.width * sc), int(s.im.height * sc)), Image.BILINEAR)
        if s.rot: im = im.rotate(s.rot, expand=True, resample=Image.BICUBIC)
        al = im.split()[3].point(lambda v: int(v * p)); im.putalpha(al)
        x, y = int(s.cx - im.width / 2), int(s.cy - im.height / 2 - 30 * (1 - p))
        if s.shadow:
            sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(al.point(lambda v: int(v * 0.55)))
            sh = sh.filter(ImageFilter.GaussianBlur(18)); c.alpha_composite(sh, (x + 14, y + 26)) if c.mode == 'RGBA' else c.paste(sh, (x + 14, y + 26), sh)
        c.paste(im, (x, y), im) if c.mode == 'RGB' else c.alpha_composite(im, (max(0, x), max(0, y)) if x >= 0 and y >= 0 else (0, 0)) if False else _paste(c, im, x, y)
        if s.label and t > s.at + 0.2:
            Tag(s.label, x + 20, y + im.height + 18, s.at + 0.2).draw(c, t)
        if s.sub and t > s.at + 0.3:
            Txt(s.sub, x + 20, y + im.height + 80, s.at + 0.3, 'pi', 40).draw(c, t)
def _paste(c, im, x, y):
    if c.mode == 'RGB': c.paste(im, (x, y), im)
    else:
        L = Image.new('RGBA', c.size, (0, 0, 0, 0)); L.paste(im, (x, y), im); c.alpha_composite(L)

class Txt:
    def __init__(s, text, x, y, at, f='pi', size=64, col=(255, 255, 255), anchor='la', dur_in=0.35, rise=24, shadow=True, until=None):
        s.__dict__.update(text=text, x=x, y=y, at=at, f=f, size=size, col=col, anchor=anchor, di=dur_in, rise=rise, shadow=shadow, until=until)
    def draw(s, c, t):
        if t < s.at or (s.until and t > s.until + 0.3): return
        p = eout((t - s.at) / s.di)
        if s.until and t > s.until: p = min(p, 1 - (t - s.until) / 0.3)
        L = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L); y = s.y + s.rise * (1 - p)
        fn = font(s.f, s.size)
        if s.shadow: d.text((s.x + 3, y + 4), s.text, font=fn, fill=(0, 0, 0, int(140 * p)), anchor=s.anchor)
        d.text((s.x, y), s.text, font=fn, fill=(*s.col, int(255 * p)), anchor=s.anchor)
        c.alpha_composite(L) if c.mode == 'RGBA' else c.paste(L, (0, 0), L)

class Tag:
    def __init__(s, text, x, y, at, bg=GREEN, fg=(12, 30, 22), size=30, anchor='l'):
        s.__dict__.update(text=text, x=x, y=y, at=at, bgc=bg, fg=fg, size=size, anchor=anchor)
    def draw(s, c, t):
        if t < s.at: return
        p = eout((t - s.at) / 0.3); fn = font('m8', s.size); tw = fn.getbbox(s.text)[2]
        L = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        x0 = s.x - (tw + 36) / 2 if s.anchor == 'm' else s.x; w = (tw + 36) * p
        d.rectangle([x0, s.y, x0 + w, s.y + s.size + 26], fill=(*s.bgc, 255))
        if p > 0.6: d.text((x0 + 18, s.y + 12), s.text, font=fn, fill=(*s.fg, int(255 * (p - 0.6) / 0.4)))
        c.alpha_composite(L) if c.mode == 'RGBA' else c.paste(L, (0, 0), L)

class Strike:
    def __init__(s, x0, y, x1, at, col=GREEN, w=10): s.__dict__.update(x0=x0, y=y, x1=x1, at=at, col=col, w=w)
    def draw(s, c, t):
        if t < s.at: return
        p = eout((t - s.at) / 0.35); L = Image.new('RGBA', c.size, (0, 0, 0, 0))
        ImageDraw.Draw(L).line([s.x0, s.y, s.x0 + (s.x1 - s.x0) * p, s.y - 10 * p], fill=(*s.col, 255), width=s.w)
        c.alpha_composite(L) if c.mode == 'RGBA' else c.paste(L, (0, 0), L)

class Card:  # kağız kart (aşağı və ya mərkəz)
    def __init__(s, lines, x, y, w, at, until=None, kick=None):
        s.__dict__.update(lines=lines, x=x, y=y, w=w, at=at, until=until, kick=kick)
    def draw(s, c, t):
        if t < s.at or (s.until and t > s.until + 0.3): return
        p = eout((t - s.at) / 0.4)
        if s.until and t > s.until: p = min(p, 1 - (t - s.until) / 0.3)
        h = 70 + 74 * len(s.lines) + (50 if s.kick else 0)
        L = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L); y = s.y + 60 * (1 - p)
        d.rectangle([s.x + 10, y + 16, s.x + s.w + 10, y + h + 16], fill=(0, 0, 0, int(90 * p)))
        d.rectangle([s.x, y, s.x + s.w, y + h], fill=(242, 236, 222, int(250 * p)))
        d.rectangle([s.x, y, s.x + 10, y + h], fill=(*GREEN, int(255 * p)))
        yy = y + 34
        if s.kick: d.text((s.x + 46, yy), az(s.kick), font=font('m6', 26), fill=(80, 110, 96, int(255 * p))); yy += 50
        for ln in s.lines:
            if isinstance(ln, tuple):
                if t < ln[1]: yy += 74; continue
                q = min(p, eout((t - ln[1]) / 0.3)); ln = ln[0]
            else: q = p
            d.text((s.x + 46, yy), ln, font=font('pi', 52), fill=(*DARK, int(255 * q))); yy += 74
        L = L.filter(ImageFilter.GaussianBlur(0)) ; c.alpha_composite(L) if c.mode == 'RGBA' else c.paste(L, (0, 0), L)

class Search:  # axtarış zolağı (son çağırış)
    def __init__(s, text, cy, at, btn=None, btn_at=None): s.__dict__.update(text=text, cy=cy, at=at, btn=btn, btn_at=btn_at)
    def draw(s, c, t):
        if t < s.at: return
        p = eout((t - s.at) / 0.4); L = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        w = 820; x0 = (W - w) // 2; y = s.cy
        d.rounded_rectangle([x0, y, x0 + w, y + 110], 55, fill=(245, 245, 240, int(240 * p)))
        n = int(len(s.text) * min(1, max(0, (t - s.at - 0.3) / 1.0)))
        d.text((x0 + 60, y + 55), s.text[:n] + ('|' if int(t * 3) % 2 and n < len(s.text) else ''), font=font('m6', 44), fill=(20, 30, 26, 255), anchor='lm')
        d.ellipse([x0 + w - 95, y + 20, x0 + w - 25, y + 90], outline=(20, 30, 26, 255), width=6)
        if s.btn and t > s.btn_at:
            q = eout((t - s.btn_at) / 0.35); bw = 520; bx = (W - bw) // 2
            d.rounded_rectangle([bx, y + 170, bx + bw, y + 170 + 110 * q], 55, fill=(*GREEN, 255))
            if q > 0.7: d.text((W // 2, y + 225), s.btn, font=font('m8', 46), fill=(12, 30, 22, 255), anchor='mm')
        c.alpha_composite(L) if c.mode == 'RGBA' else c.paste(L, (0, 0), L)

# ---------- səhnə ----------
def render_scene(sc, out, alpha=False, start_frame=0):
    """sc: dict(dur, bg, lamp(at), els[list], push(z0,z1), flash)"""
    n = sc.get('n') or int(round(sc['dur'] * FPS))
    if alpha:
        cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'qtrle', '-pix_fmt', 'argb', out]
    else:
        cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    z0, z1 = sc.get('push', (1.0, 1.05))
    for i in range(n):
        t = i / FPS
        if alpha: c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        else:
            la = sc.get('lamp')
            k = 1.0 if la is None else (0.0 if t < la else min(1, 0.35 + (t - la) / 0.25) if t - la < 0.12 or t - la > 0.2 else 0.5)
            if la is not None and t >= la and t - la < 0.25: k = [0.0, 1.0, 0.4, 1.0, 1.0][min(4, int((t - la) / 0.05))]
            c = bg(sc['bg'], t, k)
        for e in sc['els']: e.draw(c, t)
        if not alpha:
            z = z0 + (z1 - z0) * ease(t / max(sc['dur'], 0.01))
            if abs(z - 1) > 1e-3:
                cw, ch = int(W / z), int(H / z); c = c.crop(((W - cw) // 2, int((H - ch) * 0.45), (W - cw) // 2 + cw, int((H - ch) * 0.45) + ch)).resize((W, H), Image.BILINEAR)
            c = grain(c, start_frame + i, 0.06)
        p.stdin.write(c.tobytes())
    p.stdin.close(); p.wait()

class Line:  # düz xətt (ox üçün), istənilən istiqamət
    def __init__(s, x0, y0, x1, y1, at, col=GREEN, w=8, head=True): s.__dict__.update(x0=x0, y0=y0, x1=x1, y1=y1, at=at, col=col, w=w, head=head)
    def draw(s, c, t):
        if t < s.at: return
        p = eout((t - s.at) / 0.35); L = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        xe, ye = s.x0 + (s.x1 - s.x0) * p, s.y0 + (s.y1 - s.y0) * p
        d.line([s.x0, s.y0, xe, ye], fill=(*s.col, 255), width=s.w)
        if s.head and p > 0.95: d.polygon([(xe - 22, ye - 24), (xe + 22, ye - 24), (xe, ye + 4)], fill=(*s.col, 255))
        c.alpha_composite(L) if c.mode == 'RGBA' else c.paste(L, (0, 0), L)

class Check:  # yaşıl dairə içində işarə
    def __init__(s, cx, cy, at, r=30): s.__dict__.update(cx=cx, cy=cy, at=at, r=r)
    def draw(s, c, t):
        if t < s.at: return
        p = eout((t - s.at) / 0.3); L = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L); r = s.r * p
        d.ellipse([s.cx - r, s.cy - r, s.cx + r, s.cy + r], fill=(*GREEN, 255))
        if p > 0.6: d.line([s.cx - 13, s.cy, s.cx - 3, s.cy + 11, s.cx + 15, s.cy - 11], fill=(12, 30, 22, 255), width=7)
        c.alpha_composite(L) if c.mode == 'RGBA' else c.paste(L, (0, 0), L)
