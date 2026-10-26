"""Physically based backgrounds for 'Göy niyə mavidir' (v2).

Skies are computed with single-scattering Rayleigh + Mie (Nishita model) —
the same physics the video explains. Ground is a ray-marched procedural
heightfield (fBm + craters / dunes / hills) with sun shading, soft shadows
and aerial perspective. Output: 1080x1920 PNGs in ../assets/images/.

Usage: python render_worlds.py [scene ...]   (default: all)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets" / "images"
W, H = 720, 1280          # render size; upscaled to 1080x1920
FINAL = (1080, 1920)


# ---------------------------------------------------------------- noise utils
def _hash2(ix, iz, seed):
    h = (ix * 374761393 + iz * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def value_noise(x, z, seed=0):
    ix, iz = np.floor(x).astype(np.int64), np.floor(z).astype(np.int64)
    fx, fz = x - ix, z - iz
    ux, uz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = _hash2(ix, iz, seed); b = _hash2(ix + 1, iz, seed)
    c = _hash2(ix, iz + 1, seed); d = _hash2(ix + 1, iz + 1, seed)
    return (a + (b - a) * ux) + ((c + (d - c) * ux) - (a + (b - a) * ux)) * uz


def fbm(x, z, octaves=6, seed=0, lac=2.03, gain=0.5):
    total, amp, freq = 0.0, 1.0, 1.0
    for o in range(octaves):
        total = total + amp * (value_noise(x * freq, z * freq, seed + o * 17) - 0.5)
        amp *= gain
        freq *= lac
    return total


def craters(x, z, cells=0.06, seed=3):
    """Sum of bowl-shaped craters on a jittered grid (two size scales)."""
    h = np.zeros_like(x)
    for scale, depth, s in ((cells, 1.6, seed), (cells * 3.5, 0.45, seed + 9)):
        gx, gz = x * scale, z * scale
        ix, iz = np.floor(gx), np.floor(gz)
        for ox in (-1, 0, 1):
            for oz in (-1, 0, 1):
                cx, cz = ix + ox, iz + oz
                px = cx + _hash2(cx.astype(np.int64), cz.astype(np.int64), s)
                pz = cz + _hash2(cx.astype(np.int64), cz.astype(np.int64), s + 1)
                rad = 0.15 + 0.3 * _hash2(cx.astype(np.int64), cz.astype(np.int64), s + 2)
                keep = _hash2(cx.astype(np.int64), cz.astype(np.int64), s + 3) < 0.55
                d = np.sqrt((gx - px) ** 2 + (gz - pz) ** 2) / rad
                bowl = np.where(d < 1, d * d - 1, 0.0)
                rim = np.where((d >= 1) & (d < 1.6), 0.25 * np.cos((d - 1) / 0.6 * np.pi / 2) ** 2, 0.0)
                h = h + np.where(keep, (bowl + rim) * depth * rad / scale * 0.08, 0.0)
    return h


# ---------------------------------------------------------- atmosphere model
class Atmosphere:
    def __init__(self, planet_r, atmo_h, beta_r, h_r, beta_m, h_m, g, mie_abs=None, sun_I=22.0):
        self.Rp = planet_r
        self.Ra = planet_r + atmo_h
        self.beta_r = np.array(beta_r)
        self.h_r = h_r
        self.beta_m = np.array(beta_m)
        self.h_m = h_m
        self.g = np.array(g) if np.ndim(g) else np.array([g] * 3)
        self.mie_abs = np.array(mie_abs) if mie_abs is not None else np.zeros(3)
        self.sun_I = sun_I

    @staticmethod
    def _ray_sphere(o, d, r):
        b = np.sum(o * d, -1)
        c = np.sum(o * o, -1) - r * r
        disc = b * b - c
        sq = np.sqrt(np.maximum(disc, 0))
        return -b - sq, -b + sq, disc >= 0

    def _optical_depth_to_sun(self, p, sun, n=8):
        _, t1, _ = self._ray_sphere(p, sun[None, :], self.Ra)
        ds = (t1 / n)[:, None]
        odr = np.zeros(len(p)); odm = np.zeros(len(p))
        blocked = np.zeros(len(p), bool)
        for i in range(n):
            q = p + sun[None, :] * ds * (i + 0.5)
            hh = np.linalg.norm(q, axis=-1) - self.Rp
            blocked |= hh < 0
            odr += np.exp(-hh / self.h_r) * ds[:, 0]
            odm += np.exp(-hh / self.h_m) * ds[:, 0]
        return odr, odm, blocked

    def scatter(self, origin, dirs, sun, max_t=None, n=16):
        """Single-scattered radiance and transmittance along rays (N,3)."""
        t0, t1, hit = self._ray_sphere(origin[None, :], dirs, self.Ra)
        t0 = np.maximum(t0, 0)
        tg0, _, ghit = self._ray_sphere(origin[None, :], dirs, self.Rp)
        t1 = np.where(ghit & (tg0 > 0), np.minimum(t1, tg0), t1)
        if max_t is not None:
            t1 = np.minimum(t1, max_t)
        seg = np.maximum(t1 - t0, 0) / n
        mu = dirs @ sun
        pr = 3 / (16 * np.pi) * (1 + mu * mu)
        g = self.g[None, :]
        pm = 3 / (8 * np.pi) * ((1 - g * g) * (1 + mu[:, None] ** 2)) / (
            (2 + g * g) * (1 + g * g - 2 * g * mu[:, None]) ** 1.5)
        sum_r = np.zeros((len(dirs), 3)); sum_m = np.zeros((len(dirs), 3))
        odr = np.zeros(len(dirs)); odm = np.zeros(len(dirs))
        ext_m = self.beta_m + self.mie_abs
        for i in range(n):
            p = origin[None, :] + dirs * (t0 + seg * (i + 0.5))[:, None]
            hh = np.linalg.norm(p, axis=-1) - self.Rp
            dr = np.exp(-hh / self.h_r) * seg
            dm = np.exp(-hh / self.h_m) * seg
            odr += dr; odm += dm
            lr, lm, blocked = self._optical_depth_to_sun(p, sun)
            tau = self.beta_r[None, :] * (odr + lr)[:, None] + ext_m[None, :] * (odm + lm)[:, None]
            att = np.exp(-tau) * (~blocked)[:, None]
            sum_r += att * dr[:, None]
            sum_m += att * dm[:, None]
        L = self.sun_I * (sum_r * self.beta_r[None, :] * pr[:, None] + sum_m * self.beta_m[None, :] * pm)
        T = np.exp(-(self.beta_r[None, :] * odr[:, None] + ext_m[None, :] * odm[:, None]))
        return L, T

    def sun_transmittance(self, p, sun):
        odr, odm, blocked = self._optical_depth_to_sun(p, sun, n=12)
        tau = self.beta_r[None, :] * odr[:, None] + (self.beta_m + self.mie_abs)[None, :] * odm[:, None]
        return np.exp(-tau) * (~blocked)[:, None]


EARTH = Atmosphere(6360e3, 80e3, (5.8e-6, 13.5e-6, 33.1e-6), 8000, (21e-6,) * 3, 1200, 0.76, sun_I=22)
# Mars: thin CO2 (weak Rayleigh) + abundant dust that absorbs blue and forward-scatters blue (Curiosity sunsets)
MARS = Atmosphere(3390e3, 60e3, (0.20e-6, 0.47e-6, 1.15e-6), 11100,
                  (1.6e-5, 1.25e-5, 0.85e-5), 11000, (0.62, 0.68, 0.86),
                  mie_abs=(0.15e-5, 0.35e-5, 0.75e-5), sun_I=16)


def tonemap(c, exposure=1.0, gamma=2.2):
    c = 1.0 - np.exp(-c * exposure)
    return np.clip(c, 0, 1) ** (1 / gamma)


# ---------------------------------------------------------------- camera
def camera_rays(pitch_deg, fov_deg=62.0, w=W, h=H):
    """Portrait pinhole camera looking along +z, pitched up by pitch_deg."""
    aspect = w / h
    tan = np.tan(np.radians(fov_deg) / 2)
    xs = (np.arange(w) + 0.5) / w * 2 - 1
    ys = 1 - (np.arange(h) + 0.5) / h * 2
    X, Y = np.meshgrid(xs * tan * aspect, ys * tan)
    d = np.stack([X, Y, np.ones_like(X)], -1)
    p = np.radians(pitch_deg)
    rot = np.array([[1, 0, 0], [0, np.cos(p), np.sin(p)], [0, -np.sin(p), np.cos(p)]])
    d = d @ rot.T
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


def sun_dir(elev_deg, azim_deg):
    e, a = np.radians(elev_deg), np.radians(azim_deg)
    return np.array([np.cos(e) * np.sin(a), np.sin(e), np.cos(e) * np.cos(a)])


# --------------------------------------------------------------- terrain
def march_terrain(rays, cam_h, height_fn, max_dist, steps=260):
    """Ray-march a heightfield y = height_fn(x, z). Returns hit mask and positions."""
    n = len(rays)
    t = np.full(n, 0.5)
    hit = np.zeros(n, bool)
    pos = np.zeros((n, 3))
    down = rays[:, 1] < 0.02
    active = down.copy()
    for i in range(steps):
        if not active.any():
            break
        idx = np.where(active)[0]
        p = np.array([0.0, cam_h, 0.0])[None, :] + rays[idx] * t[idx, None]
        hgt = height_fn(p[:, 0], p[:, 2])
        dy = p[:, 1] - hgt
        under = dy < 0.0
        h_idx = idx[under]
        hit[h_idx] = True
        pos[h_idx] = p[under]
        active[h_idx] = False
        step = np.maximum(0.45 * dy[~under], 0.002 * t[idx[~under]] + 0.01)
        t[idx[~under]] += step
        far = t > max_dist
        active &= ~far
    return hit, pos


def shade_terrain(pos, height_fn, sun, albedo_fn, sun_col, ambient_col, shadow_steps=40, cam=None):
    e = 0.05
    x, z = pos[:, 0], pos[:, 2]
    hx = height_fn(x + e, z) - height_fn(x - e, z)
    hz = height_fn(x, z + e) - height_fn(x, z - e)
    n = np.stack([-hx, np.full_like(hx, 2 * e), -hz], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    ndl = np.clip(n @ sun, 0, 1)
    # soft shadow march toward the sun
    shadow = np.ones(len(pos))
    t = np.full(len(pos), 0.15)
    for _ in range(shadow_steps):
        p = pos + sun[None, :] * t[:, None]
        dy = p[:, 1] - height_fn(p[:, 0], p[:, 2])
        shadow = np.minimum(shadow, np.clip(8 * dy / t, 0, 1))
        t += np.maximum(dy * 0.6, 0.12)
    alb = albedo_fn(pos, n)
    sky = 0.5 + 0.5 * n[:, 1]
    col = alb * (sun_col[None, :] * (ndl * shadow)[:, None] + ambient_col[None, :] * sky[:, None])
    return col


def stars(img, rays_up, seed, density=0.0016, sky_mask=None):
    rng = np.random.default_rng(seed)
    h, w, _ = img.shape
    n = int(h * w * density)
    ys, xs = rng.integers(0, h, n), rng.integers(0, w, n)
    b = rng.random(n) ** 3 * 0.9 + 0.05
    for y, x, v in zip(ys, xs, b):
        if sky_mask is None or sky_mask[y, x]:
            img[y, x] = np.maximum(img[y, x], v)
    return img


def save(img, name, sharpen=True):
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    im = im.resize(FINAL, Image.LANCZOS)
    if sharpen:
        im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / f"{name}.png")
    print("wrote", OUT / f"{name}.png")


def render_surface(name, atmo, sun, pitch, cam_h, height_fn, albedo_fn, exposure,
                   sun_disk=0.9995, sky_scale=1.0, star_seed=None, max_dist=900.0, km_per_unit=0.03):
    rays = camera_rays(pitch).reshape(-1, 3)
    origin = np.array([0.0, (atmo.Rp if atmo is not None else 1737e3) + 2.0, 0.0])
    L, _ = (atmo.scatter(origin, rays, sun) if atmo is not None else (np.zeros((len(rays), 3)), None))
    L = L * sky_scale
    sky_tone = tonemap(L, exposure)
    # sun disk + glare
    mu = rays @ sun
    if atmo is not None:
        sun_T = atmo.sun_transmittance(origin[None, :], sun)[0]
    else:
        sun_T = np.ones(3)
    glow = np.clip((mu - 0.995) / 0.005, 0, 1) ** 4 * 0.6 + (mu > sun_disk) * 1.0
    sky_tone = np.clip(sky_tone + glow[:, None] * sun_T[None, :] * (1.3 if atmo is None else 1.0), 0, 1)
    img = sky_tone.reshape(H, W, 3)
    sky_mask = np.ones((H, W), bool)
    if star_seed is not None:
        img = stars(img, None, star_seed)

    hit, pos = march_terrain(rays, cam_h, height_fn, max_dist)
    if hit.any():
        hp = pos[hit]
        world = origin[None, :] + np.array([0, 1, 0])[None, :] * 0
        if atmo is not None:
            sun_col = atmo.sun_transmittance(np.array([[0.0, atmo.Rp + 50.0, 0.0]]), sun)[0] * 3.2
            amb = tonemap(atmo.scatter(origin, np.array([[0, 1.0, 0]]), sun)[0][0], 1.0) * 0.55
        else:
            sun_col, amb = np.array([3.4, 3.35, 3.2]), np.array([0.012, 0.012, 0.014])
        col = shade_terrain(hp, height_fn, sun, albedo_fn, sun_col, amb)
        col = tonemap(col, 1.0)
        if atmo is not None:
            # aerial perspective: blend toward in-scattered sky along the view distance
            dist = np.linalg.norm(hp - np.array([0, cam_h, 0])[None, :], axis=-1) * km_per_unit * 1000
            Lr, Tr = atmo.scatter(origin, rays[hit], sun, max_t=dist, n=8)
            col = col * Tr + tonemap(Lr * sky_scale, exposure)
        flat = img.reshape(-1, 3)
        flat[hit] = np.clip(col, 0, 1)
        img = flat.reshape(H, W, 3)
        sky_mask = (~hit).reshape(H, W)
    save(img, name)
    return img


# ------------------------------------------------------------- the worlds
def moon():
    hf = lambda x, z: 1.2 * fbm(x * 0.05, z * 0.05, 6, 1) + craters(x, z, 0.035, 5) + 0.15 * fbm(x * 0.6, z * 0.6, 4, 7)

    def alb(p, n):
        v = 0.42 + 0.12 * fbm(p[:, 0] * 0.3, p[:, 2] * 0.3, 4, 11) + 0.05 * fbm(p[:, 0] * 3, p[:, 2] * 3, 3, 13)
        return np.repeat(v[:, None], 3, 1) * np.array([1.0, 0.99, 0.97])[None, :]
    render_surface("moon_surface", None, sun_dir(24, -62), pitch=-9, cam_h=2.2, height_fn=hf,
                   albedo_fn=alb, exposure=1.0, star_seed=7, sun_disk=0.99985)


def mars(name="mars_day", sun=None, exposure=2.6, pitch=-4):
    sun = sun if sun is not None else sun_dir(38, -40)
    def hf(x, z):
        dunes = 0.9 * np.sin(x * 0.11 + 0.8 * fbm(x * 0.02, z * 0.02, 3, 2) * 6) * np.exp(-0.002 * z)
        hills = 7.0 * np.clip(fbm(x * 0.006, z * 0.006, 5, 4) + 0.12, 0, None) * np.clip((z - 120) / 300, 0, 1)
        return dunes * 0.4 + hills + 0.9 * fbm(x * 0.04, z * 0.04, 6, 21) + 0.12 * fbm(x * 0.8, z * 0.8, 3, 3)

    def alb(p, n):
        v = 0.5 + 0.18 * fbm(p[:, 0] * 0.15, p[:, 2] * 0.15, 4, 31)
        rock = (fbm(p[:, 0] * 1.4, p[:, 2] * 1.4, 3, 33) > 0.22) * 0.35
        base = np.array([0.62, 0.33, 0.18])[None, :] * v[:, None]
        return base * (1 - rock[:, None]) + np.array([0.22, 0.14, 0.1])[None, :] * rock[:, None]
    render_surface(name, MARS, sun, pitch=pitch, cam_h=1.7, height_fn=hf, albedo_fn=alb,
                   exposure=exposure, km_per_unit=0.06)


def mars_sunset():
    mars("mars_sunset", sun=sun_dir(2.2, 0), exposure=7.5, pitch=2)


def earth():
    def hf(x, z):
        return 6.0 * fbm(x * 0.004, z * 0.004, 5, 41) * np.clip((z - 40) / 200, 0, 1) + 1.2 * fbm(x * 0.02, z * 0.02, 5, 43)

    def alb(p, n):
        v = 0.6 + 0.3 * fbm(p[:, 0] * 0.08, p[:, 2] * 0.08, 4, 51)
        grass = np.array([0.18, 0.36, 0.09])[None, :] * v[:, None]
        tree = (fbm(p[:, 0] * 0.35, p[:, 2] * 0.35, 3, 53) > 0.12)
        return np.where(tree[:, None], np.array([0.07, 0.16, 0.05])[None, :], grass)
    render_surface("earth_day", EARTH, sun_dir(55, -50), pitch=6, cam_h=1.8, height_fn=hf, albedo_fn=alb,
                   exposure=1.6, km_per_unit=0.05)


def earth_limb():
    """View from 400 km orbit toward the horizon: the thin blue shell of air."""
    rays = camera_rays(-14, fov_deg=70).reshape(-1, 3)
    R = EARTH.Rp
    origin = np.array([0.0, R + 400e3, 0.0])
    sun = sun_dir(12, 25)
    L, T = EARTH.scatter(origin, rays, sun, n=24)
    t0, _, ghit = EARTH._ray_sphere(origin[None, :], rays, R)
    ground = ghit & (t0 > 0)
    gp = origin[None, :] + rays * t0[:, None]
    nrm = gp / np.linalg.norm(gp, axis=-1, keepdims=True)
    # spherical lat/long texture: ocean, land, clouds
    lat = np.arcsin(np.clip(nrm[:, 1], -1, 1)) * 40
    lon = np.arctan2(nrm[:, 0], nrm[:, 2]) * 40
    land = fbm(lon * 0.9, lat * 0.9, 6, 61) > 0.06
    cloud = np.clip((fbm(lon * 2.2, lat * 3.0, 6, 71) + 0.02) * 3.2, 0, 1)
    alb = np.where(land[:, None], np.array([0.16, 0.14, 0.08])[None, :], np.array([0.02, 0.05, 0.11])[None, :])
    alb = alb * (1 - cloud[:, None]) + 0.75 * cloud[:, None]
    ndl = np.clip(nrm @ sun, 0, 1)
    sunT = EARTH.sun_transmittance(gp + nrm * 10, sun)
    surf = alb * sunT * ndl[:, None] * 3.0
    col = np.where(ground[:, None], surf * T + L, L)
    img = tonemap(col, 2.4).reshape(H, W, 3)
    img = stars(img, None, 13, density=0.0012, sky_mask=(~ground).reshape(H, W) & (L.sum(-1) < 0.02).reshape(H, W))
    save(img, "earth_limb")


SCENES = {"moon": moon, "mars": mars, "mars_sunset": mars_sunset, "earth": earth, "limb": earth_limb}

if __name__ == "__main__":
    for key in (sys.argv[1:] or SCENES):
        SCENES[key]()
