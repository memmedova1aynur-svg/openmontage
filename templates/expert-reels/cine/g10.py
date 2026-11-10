"""Gecə/yuxu vizual dili üçün çəkilmiş elementlər (ay, gecə tonu, zaman xətti, söz kartları, günəş, ox)."""
import sys; sys.path.insert(0, '/root/montaj-data/plans/pro/cine')
from eng import *
MOON = (244, 234, 206); NIGHT = (8, 18, 28)
def _comp(c, L): c.alpha_composite(L) if c.mode == 'RGBA' else c.paste(L, (0, 0), L)

class Moon:
    def __init__(s, cx, cy, r, at, zzz=True, until=None): s.__dict__.update(cx=cx, cy=cy, r=r, at=at, zzz=zzz, until=until)
    def draw(s, c, t):
        if t < s.at or (s.until and t > s.until + 0.3): return
        p = eout((t - s.at) / 0.5)
        if s.until and t > s.until: p = min(p, 1 - (t - s.until) / 0.3)
        r = s.r * (0.7 + 0.3 * p); L = Image.new('RGBA', c.size, (0, 0, 0, 0))
        g = Image.new('L', c.size, 0); ImageDraw.Draw(g).ellipse([s.cx - r * 1.5, s.cy - r * 1.5, s.cx + r * 1.5, s.cy + r * 1.5], fill=int(90 * p))
        g = g.filter(ImageFilter.GaussianBlur(r * 0.5)); Gl = Image.new('RGBA', c.size, (*MOON, 0)); Gl.putalpha(g); _comp(c, Gl)
        m = Image.new('L', c.size, 0); dm = ImageDraw.Draw(m)
        dm.ellipse([s.cx - r, s.cy - r, s.cx + r, s.cy + r], fill=int(255 * p))
        dm.ellipse([s.cx - r * 0.45, s.cy - r * 1.05, s.cx + r * 1.3, s.cy + r * 0.75], fill=0)
        Mn = Image.new('RGBA', c.size, (*MOON, 0)); Mn.putalpha(m); _comp(c, Mn)
        if s.zzz:
            d = ImageDraw.Draw(L)
            for k in range(3):
                u = ((t - s.at) * 0.6 + k / 3) % 1.0
                a = int(230 * p * math.sin(u * math.pi))
                d.text((s.cx + r * 0.9 + 40 * k + 20 * u, s.cy - r * 0.6 - 120 * u), 'z', font=font('pbi', int(34 + 16 * k)), fill=(*MOON, a))
            _comp(c, L)

class Tint:  # gecə tonu: kadrı tündləşdirir (yuxarı daha çox)
    def __init__(s, at, until, k=0.5): s.__dict__.update(at=at, until=until, k=k); s._m = None
    def draw(s, c, t):
        if t < s.at or t > s.until + 0.5: return
        p = min(eout((t - s.at) / 0.5), 1 - ease((t - s.until) / 0.5) if t > s.until else 1)
        if s._m is None:
            y = np.linspace(1, 0.45, H)[:, None] * np.ones((1, W)); s._m = y
        a = Image.fromarray((s._m * 255 * s.k * p).astype(np.uint8)); L = Image.new('RGBA', c.size, (*NIGHT, 0)); L.putalpha(a); _comp(c, L)

class Timeline:
    def __init__(s, y, at, labels, hi):  # hi: [(t, index)]
        s.__dict__.update(y=y, at=at, labels=labels, hi=hi)
    def draw(s, c, t):
        if t < s.at: return
        p = eout((t - s.at) / 0.5); L = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        x0, x1 = 150, 930; n = len(s.labels); xs = [x0 + (x1 - x0) * k / (n - 1) for k in range(n)]
        d.line([x0, s.y, x0 + (x1 - x0) * p, s.y], fill=(235, 230, 215, 220), width=5)
        cur = None
        for tt, k in s.hi:
            if t >= tt: cur = (k, tt)
        for k, (x, lb) in enumerate(zip(xs, s.labels)):
            q = eout((t - s.at - 0.15 * k) / 0.35)
            if q <= 0: continue
            on = cur and cur[0] == k; hq = eout((t - cur[1]) / 0.3) if on else 0
            r = 16 + 10 * hq
            d.ellipse([x - r, s.y - r, x + r, s.y + r], fill=(*GREEN, int(255 * q)) if on else (235, 230, 215, int(255 * q)))
            fn = font('m8', 30 + int(6 * hq)); col = GREEN if on else (235, 230, 215)
            d.text((x + 3, s.y + 46), lb, font=fn, fill=(0, 0, 0, int(150 * q)), anchor='ma')
            d.text((x, s.y + 43), lb, font=fn, fill=(*col, int(255 * q)), anchor='ma')
        _comp(c, L)

class Cards:  # söz kartları yelpazə kimi açılır + sayğac
    def __init__(s, cx, cy, at, words, count=20, until=None): s.__dict__.update(cx=cx, cy=cy, at=at, words=words, count=count, until=until)
    def draw(s, c, t):
        if t < s.at or (s.until and t > s.until + 0.3): return
        fade = 1 - (t - s.until) / 0.3 if s.until and t > s.until else 1
        n = len(s.words)
        for k, wd in enumerate(s.words):
            q = eout((t - s.at - 0.12 * k) / 0.4) * fade
            if q <= 0: continue
            cw, ch = 300, 190; im = Image.new('RGBA', (cw + 30, ch + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.rectangle([15, 15, 15 + cw, 15 + ch], fill=(250, 247, 238, int(255 * q)))
            d.line([15, 60, 15 + cw, 60], fill=(200, 80, 80, int(160 * q)), width=2)
            for yy in range(95, ch, 34): d.line([15, yy, 15 + cw, yy], fill=(150, 185, 210, int(110 * q)), width=1)
            d.text((15 + cw / 2, 15 + ch / 2 + 18), wd, font=font('pbi', 44), fill=(*DARK, int(255 * q)), anchor='mm')
            ang = (k - (n - 1) / 2) * 6 * q
            im = im.rotate(-ang, expand=True, resample=Image.BICUBIC)
            x = s.cx + (k - (n - 1) / 2) * 320 * q - im.width / 2; y = s.cy + abs(k - (n - 1) / 2) * 18 * q - im.height / 2 + 40 * (1 - q)
            sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.split()[3].point(lambda v: int(v * 0.45))); sh = sh.filter(ImageFilter.GaussianBlur(10))
            from eng import _paste
            _paste(c, sh, int(x + 8), int(y + 14)); _paste(c, im, int(x), int(y))
        if s.count and t > s.at + 0.3:
            q = min(1, (t - s.at - 0.3) / 0.9); v = max(1, int(round(s.count * eout(q))))
            Tag(f'{v} SÖZ', s.cx, s.cy - 190, s.at + 0.3, anchor='m', size=44).draw(c, t)

class Sun:
    def __init__(s, cx, cy, r, at): s.__dict__.update(cx=cx, cy=cy, r=r, at=at)
    def draw(s, c, t):
        if t < s.at: return
        p = eout((t - s.at) / 0.5); L = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L); r = s.r * p
        col = (247, 205, 110)
        for k in range(12):
            a = k * math.pi / 6 + (t - s.at) * 0.4
            d.line([s.cx + math.cos(a) * r * 1.35, s.cy + math.sin(a) * r * 1.35, s.cx + math.cos(a) * r * 1.75, s.cy + math.sin(a) * r * 1.75], fill=(*col, int(255 * p)), width=8)
        d.ellipse([s.cx - r, s.cy - r, s.cx + r, s.cy + r], fill=(*col, int(255 * p)))
        _comp(c, L)

class ArrowUp:
    def __init__(s, x, y0, y1, at, col=GREEN): s.__dict__.update(x=x, y0=y0, y1=y1, at=at, col=col)
    def draw(s, c, t):
        if t < s.at: return
        p = eout((t - s.at) / 0.45); L = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        ye = s.y0 + (s.y1 - s.y0) * p
        d.line([s.x, s.y0, s.x, ye], fill=(*s.col, 255), width=14)
        d.polygon([(s.x - 34, ye + 20), (s.x + 34, ye + 20), (s.x, ye - 30)], fill=(*s.col, 255))
        _comp(c, L)
