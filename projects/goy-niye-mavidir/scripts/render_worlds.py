"""Physically based backgrounds for 'Göy niyə mavidir' (v3).

Skies are computed with single-scattering Rayleigh + Mie (Nishita model) —
the same physics the video explains. Ground is a procedural heightfield
(craters, boulders, dunes, layered mesas, hills, planet curvature) baked to a
perspective grid (u = x/z, w = ln z) so detail density follows screen
resolution, then ray-marched with soft sun shadows, a per-world BRDF
(Lommel-Seeliger regolith on the Moon, Lambert elsewhere) and aerial
perspective. Post: HDR bloom, ACES filmic tonemap, vignette, film grain.

Output: 1188x2112 PNGs (10% overscan of 1080x1920 for slow camera moves)
in ../assets/images/.

Usage: python render_worlds.py [scene ...]   (default: all)
       RW_SCALE=0.35 python render_worlds.py moon   (fast preview)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "assets" / "images"
SCALE = float(os.environ.get("RW_SCALE", "1"))
W, H = int(1188 * SCALE) // 2 * 2, int(2112 * SCALE) // 2 * 2
FOV = 58.0                       # vertical field of view, degrees
PIX = np.radians(FOV) / H        # angular size of one pixel


# ---------------------------------------------------------------- noise utils
def _hash2(ix, iz, seed):
    h = (ix * 374761393 + iz * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _hash3(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 1440662683 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def value_noise(x, z, seed=0):
    ix, iz = np.floor(x).astype(np.int64), np.floor(z).astype(np.int64)
    fx, fz = x - ix, z - iz
    ux, uz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = _hash2(ix, iz, seed); b = _hash2(ix + 1, iz, seed)
    c = _hash2(ix, iz + 1, seed); d = _hash2(ix + 1, iz + 1, seed)
    top = a + (b - a) * ux
    return top + ((c + (d - c) * ux) - top) * uz


def value_noise3(x, y, z, seed=0):
    ix, iy, iz = (np.floor(v).astype(np.int64) for v in (x, y, z))
    f = [v - i for v, i in ((x, ix), (y, iy), (z, iz))]
    u = [t * t * (3 - 2 * t) for t in f]
    acc = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                wgt = ((u[0] if dx else 1 - u[0]) * (u[1] if dy else 1 - u[1]) * (u[2] if dz else 1 - u[2]))
                acc = acc + wgt * _hash3(ix + dx, iy + dy, iz + dz, seed)
    return acc


def fbm(x, z, octaves=6, seed=0, lac=2.03, gain=0.5):
    total, amp, freq = 0.0, 1.0, 1.0
    for o in range(octaves):
        total = total + amp * (value_noise(x * freq, z * freq, seed + o * 17) - 0.5)
        amp *= gain
        freq *= lac
    return total


def fbm3(p, octaves=6, seed=0, lac=2.03, gain=0.5):
    total, amp, freq = 0.0, 1.0, 1.0
    for o in range(octaves):
        total = total + amp * (value_noise3(p[..., 0] * freq, p[..., 1] * freq, p[..., 2] * freq, seed + o * 17) - 0.5)
        amp *= gain
        freq *= lac
    return total


def ridged(x, z, octaves=6, seed=0):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        n = 1 - np.abs(2 * value_noise(x * freq, z * freq, seed + o * 31) - 1)
        total = total + amp * n * n
        norm += amp
        amp *= 0.5
        freq *= 2.1
    return total / norm


def fbm_lod(x, z, freq, octaves, amp, seed, footprint):
    """fBm whose octaves fade out once their wavelength drops below ~4 pixels."""
    total = np.zeros_like(x)
    for o in range(octaves):
        wl = 1.0 / freq
        fade = np.clip((wl / (footprint + 1e-6) - 4.0) / 4.0, 0, 1)
        total += amp * fade * (value_noise(x * freq, z * freq, seed + o * 13) - 0.5)
        freq *= 2.07
        amp *= 0.55
    return total


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------- terrain features
def craters(x, z, cell, seed, density=0.55, depth=0.2, rim=0.06):
    """Bowl craters with raised rims on a jittered grid; `cell` in metres."""
    gx, gz = x / cell, z / cell
    ix0, iz0 = np.floor(gx).astype(np.int64), np.floor(gz).astype(np.int64)
    h = np.zeros_like(x)
    for ox in (-1, 0, 1):
        for oz in (-1, 0, 1):
            cx, cz = ix0 + ox, iz0 + oz
            px = cx + _hash2(cx, cz, seed)
            pz = cz + _hash2(cx, cz, seed + 1)
            r = 0.1 + 0.4 * _hash2(cx, cz, seed + 2) ** 1.6
            keep = _hash2(cx, cz, seed + 3) < density
            d = np.sqrt((gx - px) ** 2 + (gz - pz) ** 2) / r
            bowl = np.where(d < 1, (d * d - 1) * depth, 0.0)
            rimh = rim * np.exp(-((d - 1.0) / 0.32) ** 2) * (d < 2.0)
            h += np.where(keep, (bowl + rimh) * r * cell, 0.0)
    return h


def rocks(x, z, cell, seed, density, rmin, rmax):
    """Scattered boulders (squashed half-ellipsoids); radii in metres."""
    gx, gz = x / cell, z / cell
    ix0, iz0 = np.floor(gx).astype(np.int64), np.floor(gz).astype(np.int64)
    h = np.zeros_like(x)
    for ox in (-1, 0, 1):
        for oz in (-1, 0, 1):
            cx, cz = ix0 + ox, iz0 + oz
            px = cx + 0.15 + 0.7 * _hash2(cx, cz, seed)
            pz = cz + 0.15 + 0.7 * _hash2(cx, cz, seed + 1)
            r = (rmin + (rmax - rmin) * _hash2(cx, cz, seed + 2) ** 3) / cell
            keep = _hash2(cx, cz, seed + 3) < density
            s = 0.7 + 0.6 * _hash2(cx, cz, seed + 4)
            d2 = (((gx - px) * s) ** 2 + ((gz - pz) / s) ** 2) / (r * r)
            lump = 1 + 0.6 * (value_noise(gx * 1.8 / r, gz * 1.8 / r, seed + 6) - 0.5)
            prof = np.clip(1 - d2 * lump, 0, 1) ** 0.6
            b = prof * r * cell * (0.45 + 0.4 * _hash2(cx, cz, seed + 5))
            h = np.maximum(h, np.where(keep & (d2 < 1.6), b, 0.0))
    return h


def near(fn, x, z, zmax):
    """Evaluate a small-scale feature only where it can be resolved (z < zmax)."""
    out = np.zeros_like(x)
    m = z < zmax
    if m.any():
        out[m] = fn(x[m], z[m]) * np.clip((zmax - z[m]) / (0.3 * zmax), 0, 1)
    return out


class Terrain:
    """Heightfield baked on a perspective grid: u = x/z (columns), w = ln z (rows)."""

    def __init__(self, height_fn, z0=0.8, z1=40000.0, umax=0.6):
        self.fn = height_fn
        self.z0, self.umax = z0, umax
        self.nu, self.nw = int(3000 * SCALE) + 2, int(4500 * SCALE) + 2
        self.lw0, self.lw1 = np.log(z0), np.log(z1)
        u = np.linspace(-umax, umax, self.nu)
        w = np.linspace(self.lw0, self.lw1, self.nw)
        self.g = np.zeros((self.nw, self.nu), np.float32)
        step = max(1, 2_000_000 // self.nu)
        for r0 in range(0, self.nw, step):
            Z = np.exp(w[r0:r0 + step])[:, None] * np.ones((1, self.nu))
            X = u[None, :] * Z
            self.g[r0:r0 + step] = height_fn(X.ravel(), Z.ravel()).reshape(Z.shape)

    def __call__(self, x, z):
        z = np.maximum(z, self.z0)
        fu = (x / z + self.umax) / (2 * self.umax) * (self.nu - 1)
        fw = (np.log(z) - self.lw0) / (self.lw1 - self.lw0) * (self.nw - 1)
        fu = np.clip(fu, 0, self.nu - 1.001)
        fw = np.clip(fw, 0, self.nw - 1.001)
        i, j = fw.astype(np.int64), fu.astype(np.int64)
        a, b = fw - i, fu - j
        g = self.g
        return ((g[i, j] * (1 - b) + g[i, j + 1] * b) * (1 - a)
                + (g[i + 1, j] * (1 - b) + g[i + 1, j + 1] * b) * a)


# ---------------------------------------------------------- atmosphere model
class Atmosphere:
    def __init__(self, planet_r, atmo_h, beta_r, h_r, beta_m, h_m, g, mie_abs=None, sun_I=20.0):
        self.Rp = planet_r
        self.Ra = planet_r + atmo_h
        self.beta_r = np.array(beta_r)
        self.h_r = h_r
        self.beta_m = np.array(beta_m)
        self.h_m = h_m
        self.g = np.array(g) if np.ndim(g) else np.array([g] * 3)
        self.mie_abs = np.array(mie_abs) if mie_abs is not None else np.zeros(3)
        self.sun_I = sun_I
        self.haze = 1.0

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

    def phase_m(self, mu):
        g = self.g[None, :]
        return 3 / (8 * np.pi) * ((1 - g * g) * (1 + mu[:, None] ** 2)) / (
            (2 + g * g) * (1 + g * g - 2 * g * mu[:, None]) ** 1.5)

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
        pm = self.phase_m(mu)
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
        odr, odm, blocked = self._optical_depth_to_sun(p, sun, n=16)
        tau = self.beta_r[None, :] * odr[:, None] + (self.beta_m + self.mie_abs)[None, :] * odm[:, None]
        return np.exp(-tau) * (~blocked)[:, None]

    def sky_irradiance(self, origin, sun, n=384):
        """Cosine-weighted irradiance from the sky hemisphere on a horizontal surface."""
        rng = np.random.default_rng(5)
        u, v = rng.random(n), rng.random(n)
        r, phi = np.sqrt(u), 2 * np.pi * v
        d = np.stack([r * np.cos(phi), np.sqrt(1 - u), r * np.sin(phi)], -1)
        L, _ = self.scatter(origin, d, sun, n=10)
        return L.mean(0) * np.pi

    def ground_extinction(self):
        return (self.beta_r + self.beta_m + self.mie_abs) * self.haze


EARTH = Atmosphere(6360e3, 80e3, (5.8e-6, 13.5e-6, 33.1e-6), 8000, (12e-6,) * 3, 1200, 0.76)
# Mars: thin CO2 (weak Rayleigh) + abundant dust (vertical optical depth ~0.6) that
# absorbs blue and forward-scatters blue more strongly (blue sunsets seen by Curiosity).
MARS = Atmosphere(3390e3, 60e3, (0.20e-6, 0.47e-6, 1.15e-6), 11100,
                  (5.6e-5, 3.9e-5, 3.3e-5), 11000, (0.63, 0.70, 0.87),
                  mie_abs=(0.3e-5, 2.0e-5, 2.0e-5))
EARTH.haze = 1.6


# ---------------------------------------------------------------- camera
def camera_rays(pitch_deg, yaw_deg=0.0, fov_deg=FOV, w=None, h=None):
    """Portrait pinhole camera looking along +z, pitched up by pitch_deg."""
    w, h = w or W, h or H
    aspect = w / h
    tan = np.tan(np.radians(fov_deg) / 2)
    xs = (np.arange(w) + 0.5) / w * 2 - 1
    ys = 1 - (np.arange(h) + 0.5) / h * 2
    X, Y = np.meshgrid(xs * tan * aspect, ys * tan)
    d = np.stack([X, Y, np.ones_like(X)], -1)
    p, yw = np.radians(pitch_deg), np.radians(yaw_deg)
    rp = np.array([[1, 0, 0], [0, np.cos(p), np.sin(p)], [0, -np.sin(p), np.cos(p)]])
    ry = np.array([[np.cos(yw), 0, np.sin(yw)], [0, 1, 0], [-np.sin(yw), 0, np.cos(yw)]])
    d = d @ rp.T @ ry.T
    return (d / np.linalg.norm(d, axis=-1, keepdims=True)).reshape(-1, 3)


def sun_dir(elev_deg, azim_deg):
    e, a = np.radians(elev_deg), np.radians(azim_deg)
    return np.array([np.cos(e) * np.sin(a), np.sin(e), np.cos(e) * np.cos(a)])


# --------------------------------------------------------------- rendering
def march(rays, cam_h, terr, max_dist, steps=3000):
    n = len(rays)
    o = np.array([0.0, cam_h, 0.0])
    t = np.full(n, 0.3)
    t_prev = t.copy()
    hit = np.zeros(n, bool)
    active = rays[:, 1] < 0.03
    for _ in range(steps):
        idx = np.flatnonzero(active)
        if idx.size == 0:
            break
        p = o + rays[idx] * t[idx, None]
        dy = p[:, 1] - terr(p[:, 0], p[:, 2])
        under = dy < 0
        hit[idx[under]] = True
        active[idx[under]] = False
        go = idx[~under]
        t_prev[go] = t[go]
        t[go] += np.maximum(0.45 * dy[~under], 0.004 * t[go] + 0.004)
        active &= t < max_dist
    # bisection refinement against the analytic surface for crisp silhouettes
    hi = np.flatnonzero(hit)
    lo_t, hi_t = t_prev[hi].copy(), t[hi].copy()
    for _ in range(9):
        mid = 0.5 * (lo_t + hi_t)
        p = o + rays[hi] * mid[:, None]
        below = p[:, 1] < terr.fn(p[:, 0], p[:, 2])
        hi_t = np.where(below, mid, hi_t)
        lo_t = np.where(below, lo_t, mid)
    t[hi] = hi_t
    return hit, t


def soft_shadow(terr, pos, sun, dist, k=24.0, steps=56, maxd=4000.0):
    s = np.ones(len(pos))
    t = np.full(len(pos), 0.03) + 0.004 * dist
    # bias grows with distance: the baked grid is coarser there than the shading detail
    base = pos + np.array([0, 1.0, 0]) * (0.01 + 0.0015 * dist)[:, None]
    for _ in range(steps):
        p = base + sun[None, :] * t[:, None]
        dy = p[:, 1] - terr(p[:, 0], p[:, 2])
        s = np.minimum(s, np.clip(k * dy / t, 0, 1))
        t += np.clip(dy * 0.5, 0.02 + 0.02 * t, 80.0)
        if (t > maxd).all():
            break
    return s


def normals(terr, detail, pos, t):
    e = np.maximum(0.004, t * PIX * 1.5)
    x, z = pos[:, 0], pos[:, 2]
    fp = t * PIX

    def hgt(xx, zz):
        return terr.fn(xx, zz) + detail(xx, zz, fp)
    hx = hgt(x + e, z) - hgt(x - e, z)
    hz = hgt(x, z + e) - hgt(x, z - e)
    n = np.stack([-hx, 2 * e, -hz], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def lowres_sky(atmo, origin, rays_shape_pitch, sun, div=6, yaw=0.0):
    """Sky radiance computed at 1/div resolution and bilinearly upsampled (sky is smooth)."""
    lw, lh = max(8, W // div), max(8, H // div)
    d = camera_rays(rays_shape_pitch, yaw, w=lw, h=lh)
    L, _ = atmo.scatter(origin, d, sun)
    L = L.reshape(lh, lw, 3).astype(np.float32)
    up = np.stack([np.asarray(Image.fromarray(L[..., c], "F").resize((W, H), Image.BILINEAR)) for c in range(3)], -1)
    return up.reshape(-1, 3).astype(np.float64)


def horizon_radiance(atmo, origin, rays, sun):
    """Sky radiance just above the horizon for each ray's azimuth (for aerial perspective)."""
    az = np.arctan2(rays[:, 0], rays[:, 2])
    grid = np.linspace(az.min() - 0.01, az.max() + 0.01, 96)
    d = np.stack([np.sin(grid), np.full_like(grid, 0.01), np.cos(grid)], -1)
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    L, _ = atmo.scatter(origin, d, sun)
    return np.stack([np.interp(az, grid, L[:, c]) for c in range(3)], -1)


def sun_disk(rays, sun, radius_deg, radiance):
    ang = np.arccos(np.clip(rays @ sun, -1, 1))
    r = ang / np.radians(radius_deg)
    limb = np.clip(1 - 0.6 * (1 - np.sqrt(np.clip(1 - r * r, 0, 1))), 0, 1)
    edge = np.clip((1.0 - r) / 0.08, 0, 1)
    return (edge * limb)[:, None] * radiance[None, :]


# --------------------------------------------------------------- post / I/O
def _box(a, r, axis):
    if r < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
    n = a.shape[axis]
    return (np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis) - np.take(c, np.arange(0, n), axis)) / (2 * r + 1)


def blur(img, sigma):
    """Gaussian approximation: three box passes per axis on a downsampled copy."""
    f = max(1, int(sigma // 6))
    h, w = img.shape[:2]
    small = img[::f, ::f] if f > 1 else img
    r = max(1, int(round(sigma / f * 0.9)))
    for _ in range(3):
        small = _box(_box(small, r, 0), r, 1)
    if f == 1:
        return small
    return np.stack([np.asarray(Image.fromarray(small[..., c].astype(np.float32), "F").resize((w, h), Image.BILINEAR))
                     for c in range(img.shape[2])], -1)


def aces(x):
    return np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1)


def finish(hdr, name, exposure, key_mask=None, key=0.18, bloom=0.06, grain=0.010, vignette=0.28, seed=1):
    img = hdr.reshape(H, W, 3)
    lum = img @ np.array([0.2126, 0.7152, 0.0722])
    m = key_mask.reshape(H, W) if key_mask is not None else np.ones((H, W), bool)
    lo, hi = np.percentile(lum[m], [2, 99])
    m = m & (lum >= lo) & (lum <= hi)
    img = img * (key / (lum[m].mean() + 1e-6) * exposure)
    bright = np.maximum(img - 1.0, 0)
    if bloom > 0:
        glow = sum(wt * blur(bright, s * SCALE) for s, wt in ((6, 0.5), (24, 0.3), (80, 0.2)))
        img = img + bloom * glow
    out = aces(img)
    out = np.where(out <= 0.0031308, 12.92 * out, 1.055 * np.power(out, 1 / 2.4) - 0.055)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
    out = out * (1 - vignette * r[..., None] ** 2.2)
    rng = np.random.default_rng(seed)
    out = out + grain * rng.standard_normal((H, W, 1)) * (0.4 + 0.6 * out)
    im = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = "" if SCALE == 1 else "_preview"
    im.save(OUT / f"{name}{suffix}.png")
    print("wrote", OUT / f"{name}{suffix}.png", flush=True)


def add_stars(hdr, mask, seed, density=0.0006, level=0.02):
    rng = np.random.default_rng(seed)
    n = int(W * H * density)
    idx = rng.integers(0, W * H, n)
    b = (rng.random(n) ** 4) * level
    keep = mask[idx]
    hdr[idx[keep]] += b[keep, None] * np.array([1.0, 0.97, 0.93])[None, :]
    return hdr


def render_surface(name, atmo, sun, pitch, cam_h, terr, detail, albedo_fn, *, brdf="lambert",
                   exposure=1.0, key=0.18, key_on="all", sun_radius=0.27, sun_radiance=None,
                   max_dist=40000.0, stars=False, extra_sky=None, ambient=None, planet_r=1737e3):
    rays = camera_rays(pitch)
    origin = np.array([0.0, (atmo.Rp if atmo else planet_r) + cam_h, 0.0])
    n = len(rays)
    if atmo is not None:
        sky = lowres_sky(atmo, origin, pitch, sun)
        sun_T = atmo.sun_transmittance(np.array([[0.0, atmo.Rp + 2.0, 0.0]]), sun)[0]
        E_sun = atmo.sun_I * sun_T
        E_sky = atmo.sky_irradiance(origin, sun) if ambient is None else ambient
    else:
        sky = np.zeros((n, 3))
        sun_T = np.ones(3)
        E_sun = np.full(3, 20.0)
        E_sky = np.full(3, 0.004) if ambient is None else ambient
    hdr = sky.copy()
    if stars:
        hdr = add_stars(hdr, np.ones(n, bool), 7)
    if extra_sky is not None:
        hdr = extra_sky(rays, hdr)
    rad = sun_radiance if sun_radiance is not None else 2.0e4 * sun_T
    hdr += sun_disk(rays, sun, sun_radius, rad)

    hit, t = march(rays, cam_h, terr, max_dist)
    print(f"  {name}: {hit.mean():.0%} ground pixels", flush=True)
    if hit.any():
        o = np.array([0.0, cam_h, 0.0])
        th = t[hit]
        pos = o + rays[hit] * th[:, None]
        nrm = normals(terr, detail, pos, th)
        sh = soft_shadow(terr, pos, sun, th, k=40.0 if atmo is None else 16.0)
        mu0 = np.clip(nrm @ sun, 0, 1)
        if brdf == "lunar":
            mu = np.clip(-(nrm * rays[hit]).sum(-1), 0.02, 1)
            f = 0.75 * 2 * mu0 / (mu0 + mu + 1e-6) + 0.25 * mu0
        else:
            f = mu0
        alb = albedo_fn(pos, nrm, th)
        skyvis = 0.55 + 0.45 * nrm[:, 1]
        col = alb / np.pi * (E_sun[None, :] * (f * sh)[:, None] + E_sky[None, :] * skyvis[:, None])
        if atmo is not None:
            ext = atmo.ground_extinction()
            T = np.exp(-ext[None, :] * th[:, None])
            Lh = horizon_radiance(atmo, origin, rays[hit], sun)
            col = col * T + Lh * (1 - T)
        hdr[hit] = col
    mask = {"all": np.ones(n, bool), "ground": hit, "sky": ~hit}[key_on]
    finish(hdr, name, exposure, mask, key=key)
    return hdr


# ------------------------------------------------------------- the worlds
def moon():
    R = 1737e3

    def hf(x, z):
        h = 7 * fbm(x * 0.002, z * 0.002, 4, 1) + 1.1 * fbm(x * 0.02, z * 0.02, 4, 5)
        h += craters(x, z, 700, 11, 0.5, 0.18, 0.05) + craters(x, z, 110, 13, 0.55)
        h += near(lambda a, b: craters(a, b, 18, 17, 0.4, 0.14, 0.05) + 0.15 * fbm(a * 0.3, b * 0.3, 3, 9), x, z, 900)
        h += near(lambda a, b: craters(a, b, 3.2, 19, 0.25, 0.09, 0.03), x, z, 90)
        h += near(lambda a, b: rocks(a, b, 1.7, 23, 0.22, 0.03, 0.32) + rocks(a, b, 8, 29, 0.12, 0.2, 1.1), x, z, 120)
        return h - (x * x + z * z) / (2 * R)

    def detail(x, z, fp):
        return fbm_lod(x, z, 1.2, 6, 0.035, 41, fp)

    def alb(p, n, t):
        x, z = p[:, 0], p[:, 2]
        v = 0.16 * (1 + 0.35 * fbm(x * 0.006, z * 0.006, 4, 51) + 0.2 * fbm(x * 0.15, z * 0.15, 3, 53)
                    + 0.12 * fbm_lod(x, z, 3.0, 4, 1.0, 55, t * PIX))
        return v[:, None] * np.array([1.0, 0.985, 0.965])[None, :]

    def earth_in_sky(rays, hdr):
        # Earth hangs in the black lunar sky: 1.9 deg, gibbous, lit by the same sun.
        c = sun_dir(11.5, -9)
        ang = np.arccos(np.clip(rays @ c, -1, 1))
        rad = np.radians(1.9 / 2)
        m = ang < rad * 1.08
        if not m.any():
            return hdr
        up = np.array([0, 1.0, 0]); right = np.cross(up, c); right /= np.linalg.norm(right)
        up2 = np.cross(c, right)
        d = rays[m]
        px, py = (d @ right) / rad, (d @ up2) / rad
        rr = px * px + py * py
        inside = rr < 1
        nz = np.sqrt(np.clip(1 - rr, 0, 1))
        nrm = px[:, None] * right + py[:, None] * up2 - nz[:, None] * c
        cl = np.clip((fbm3(nrm * 3.0, 5, 61) + 0.05) * 3.5, 0, 1)
        land = fbm3(nrm * 1.6, 5, 67) > 0.07
        base = np.where(land[:, None], np.array([0.12, 0.11, 0.07]), np.array([0.02, 0.05, 0.12]))
        a = base * (1 - cl[:, None]) + 0.75 * cl[:, None]
        lit = np.clip(nrm @ SUN_MOON, 0, 1)
        limb = np.exp(-nz * 6)[:, None] * np.array([0.25, 0.5, 1.0])
        col = (a * lit[:, None] * 20 / np.pi + limb * lit[:, None] * 6) * 1.0
        aa = np.clip((1 - np.sqrt(rr)) * 40, 0, 1)
        out = hdr[m]
        out = out * (1 - aa[:, None] * inside[:, None]) + col * (aa * inside)[:, None]
        hdr[m] = out
        return hdr

    render_surface("moon_surface", None, SUN_MOON, pitch=-3, cam_h=1.7, terr=Terrain(hf), detail=detail,
                   albedo_fn=alb, brdf="lunar", key=0.30, key_on="ground", exposure=1.0, stars=True,
                   extra_sky=earth_in_sky, sun_radius=0.27, sun_radiance=np.full(3, 2.5e4), planet_r=R)


SUN_MOON = sun_dir(15, -102)


def mars(name="mars_day", sun=None, pitch=-3.0, key=0.2, key_on="all", exposure=1.0):
    sun = sun if sun is not None else sun_dir(34, -48)
    R = 3390e3

    def hf(x, z):
        h = 1.6 * fbm(x * 0.006, z * 0.006, 5, 21) + 0.3 * fbm(x * 0.05, z * 0.05, 4, 23)
        # layered mesas in the distance (Mount Sharp-like), with soft terraces
        m = smoothstep(0.02, 0.2, fbm(x * 0.00045 + 3.1, z * 0.00045, 5, 25) + 0.1 * ridged(x * 0.003, z * 0.003, 4, 26))
        m = m * smoothstep(1500, 4000, z)
        lay = m * 520
        lay = lay - 6 * np.sin(lay / 22.0 * 2 * np.pi) * m
        h += lay
        h += near(lambda a, b: 0.12 * np.sin(a * 0.9 + 3 * fbm(a * 0.05, b * 0.05, 3, 27)) * smoothstep(0.0, 0.15, fbm(a * 0.02, b * 0.02, 3, 28)), x, z, 300)
        h += near(lambda a, b: rocks(a, b, 1.3, 61, 0.38, 0.03, 0.28) + rocks(a, b, 5.5, 63, 0.18, 0.15, 0.85), x, z, 140)
        h += near(lambda a, b: craters(a, b, 40, 65, 0.25, 0.12, 0.04), x, z, 1500)
        return h - (x * x + z * z) / (2 * R)

    def detail(x, z, fp):
        return fbm_lod(x, z, 1.5, 6, 0.03, 71, fp)

    def alb(p, n, t):
        x, z = p[:, 0], p[:, 2]
        v = 1 + 0.25 * fbm(x * 0.03, z * 0.03, 4, 31) + 0.15 * fbm_lod(x, z, 2.0, 4, 1.0, 33, t * PIX)
        dust = np.array([0.36, 0.19, 0.10])
        rock = np.array([0.15, 0.11, 0.085])
        steep = smoothstep(0.88, 0.62, n[:, 1])
        bed = steep * smoothstep(0.0, 0.3, fbm(x * 0.4, z * 0.4, 3, 35) + 0.2)
        rk = near(lambda a, b: rocks(a, b, 1.3, 61, 0.38, 0.03, 0.28) + rocks(a, b, 5.5, 63, 0.18, 0.15, 0.85), x, z, 140)
        bed = np.maximum(bed, smoothstep(0.01, 0.04, rk))
        a = dust[None, :] * (1 - bed[:, None]) + rock[None, :] * bed[:, None]
        return a * v[:, None]

    render_surface(name, MARS, sun, pitch=pitch, cam_h=1.9, terr=Terrain(hf), detail=detail, albedo_fn=alb,
                   key=key, key_on=key_on, exposure=exposure, sun_radius=0.18, planet_r=R)


def mars_day():
    mars(key=0.16, key_on="all")


def mars_sunset():
    mars("mars_sunset", sun=sun_dir(2.0, 4), pitch=2.0, key=0.10, key_on="sky", exposure=1.0)


def earth():
    R = 6360e3
    sun = sun_dir(48, -55)

    def hf(x, z):
        h = 60 * fbm(x * 0.0018, z * 0.0018, 6, 41) * smoothstep(80, 600, z)
        h += 3200 * np.clip(ridged(x * 0.00035, z * 0.00035, 7, 45) - 0.3, 0, None) * smoothstep(9000, 16000, z)
        h += near(lambda a, b: 0.9 * fbm(a * 0.03, b * 0.03, 4, 43), x, z, 2500)
        return h - (x * x + z * z) / (2 * R)

    def detail(x, z, fp):
        return fbm_lod(x, z, 2.0, 6, 0.02, 81, fp)

    def alb(p, n, t):
        x, z = p[:, 0], p[:, 2]
        v = 1 + 0.35 * fbm(x * 0.02, z * 0.02, 4, 51) + 0.2 * fbm_lod(x, z, 1.5, 4, 1.0, 53, t * PIX)
        grass = np.array([0.075, 0.13, 0.035])
        forest = np.array([0.025, 0.05, 0.02])
        rock = np.array([0.17, 0.16, 0.15])
        snow = np.array([0.85, 0.87, 0.9])
        fd = np.exp(-t / 2500.0)
        v = 1 + (v - 1) * fd
        fo = smoothstep(0.05, 0.12, fbm(x * 0.004, z * 0.004, 5, 57)) * fd
        a = grass[None, :] * (1 - fo[:, None]) + forest[None, :] * fo[:, None]
        st = smoothstep(0.85, 0.65, n[:, 1])
        a = a * (1 - st[:, None]) + rock[None, :] * st[:, None]
        sn = smoothstep(1500, 1900, p[:, 1] + 60 * fbm(x * 0.01, z * 0.01, 3, 59)) * smoothstep(0.55, 0.8, n[:, 1])
        a = a * (1 - sn[:, None]) + snow[None, :] * sn[:, None]
        return a * v[:, None]

    def clouds(rays, hdr):
        up = rays[:, 1] > 0.004
        d = rays[up]
        tcl = 1800.0 / d[:, 1]
        p = d * tcl[:, None]
        dens = np.clip((fbm(p[:, 0] * 0.00035, p[:, 2] * 0.00035, 7, 91) + 0.03) * 4.0, 0, 1)
        q = p + sun[None, :] * 350
        shade = np.clip((fbm(q[:, 0] * 0.00035, q[:, 2] * 0.00035, 7, 91) + 0.03) * 4.0, 0, 1)
        E = EARTH.sun_I * EARTH.sun_transmittance(np.array([[0.0, EARTH.Rp + 1800, 0.0]]), sun)[0]
        lit = 0.9 / np.pi * E[None, :] * (1 - 0.55 * shade[:, None]) + 0.25 * hdr[up]
        fade = np.exp(-tcl / 26000.0)
        a = dens * fade
        hdr[up] = hdr[up] * (1 - a[:, None]) + lit * a[:, None]
        return hdr

    render_surface("earth_day", EARTH, sun, pitch=15, cam_h=40.0, terr=Terrain(hf), detail=detail, albedo_fn=alb,
                   key=0.22, key_on="sky", exposure=1.0, extra_sky=clouds, planet_r=R)


def earth_limb():
    """View from 400 km orbit toward the horizon: the thin blue shell of air."""
    rays = camera_rays(-16, fov_deg=64)
    R = EARTH.Rp
    origin = np.array([0.0, R + 400e3, 0.0])
    sun = sun_dir(26, 30)
    # scattering at half resolution (smooth), surface texture at full resolution
    hw, hh = W // 2, H // 2
    rl = camera_rays(-16, fov_deg=64, w=hw, h=hh)
    Ll, Tl = EARTH.scatter(origin, rl, sun, n=24)

    def up(a):
        a = a.reshape(hh, hw, 3).astype(np.float32)
        return np.stack([np.asarray(Image.fromarray(a[..., c], "F").resize((W, H), Image.BILINEAR)) for c in range(3)], -1).reshape(-1, 3)
    L, T = up(Ll), up(Tl)
    t0, _, ghit = EARTH._ray_sphere(origin[None, :], rays, R)
    ground = ghit & (t0 > 0)
    gp = origin[None, :] + rays * t0[:, None]
    nrm = gp / np.linalg.norm(gp, axis=-1, keepdims=True)
    q = nrm[ground]
    land = fbm3(q * 14.0, 6, 61) > 0.11
    cl = np.clip((fbm3(q * 70.0 + 0.6 * fbm3(q * 25.0, 4, 75)[..., None], 7, 71) - 0.03) * 2.4, 0, 1) ** 1.3
    cl = cl * smoothstep(-0.12, 0.05, fbm3(q * 4.0, 4, 73))
    alb = np.where(land[:, None], np.array([0.09, 0.10, 0.05])[None, :], np.array([0.012, 0.03, 0.07])[None, :])
    alb = alb * (1 - cl[:, None]) + 0.8 * cl[:, None]
    ndl = np.clip(q @ sun, 0, 1)
    sunT = EARTH.sun_transmittance(gp[ground] + q * 10, sun)
    view = -rays[ground]
    refl = 2 * (q @ sun)[:, None] * q - sun[None, :]
    glint = np.exp(-((1 - np.clip((refl * view).sum(-1), 0, 1)) / 0.004)) * (~land) * (1 - cl) * 0.6
    surf = (alb / np.pi * ndl[:, None] + glint[:, None]) * sunT * EARTH.sun_I
    hdr = L.astype(np.float64).copy()
    hdr[ground] = surf * T[ground] + L[ground]
    space = ~ground & (L.sum(-1) < 1e-3)
    hdr = add_stars(hdr, space, 13, density=0.0008, level=0.05)
    finish(hdr, "earth_limb", 1.0, ground, key=0.16, bloom=0.08)


SCENES = {"moon": moon, "mars": mars_day, "mars_sunset": mars_sunset, "earth": earth, "limb": earth_limb}

if __name__ == "__main__":
    for key in (sys.argv[1:] or SCENES):
        SCENES[key]()
