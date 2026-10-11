"""Procedural sea glass renderer.

Renders frosted beach-glass pebbles lying on a surface, lit by a low sun from
the upper left: soft body shading, frosted grain and pitting, a subsurface rim
glow on the shadow side, and translucent coloured shadows with a focused
caustic core — the look of the reference photo.

One code path, two moods:
  sunlit   — pebbles on bright paper (light theme)
  tidepool — pebbles on dark wet slate; the same light makes the glass glow and
             pools coloured caustics onto the stone (dark theme)

Everything is computed in linear light and tone-mapped once at the end.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image

# --------------------------------------------------------------------------- colour


def srgb_to_lin(c):
    c = np.asarray(c, dtype=np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def hex_lin(h):
    h = h.lstrip("#")
    return srgb_to_lin([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


# Glass body colours (sRGB) and how strongly each glass tints / transmits.
#   tint      — saturation of the transmitted (shadow) light, 0 = clear
#   transmit  — how much light gets through (dark glass casts darker shadows)
# translucency: how much of the (blurred) ground shows through the frosted body
CLARITY = {"frost": 0.50, "clear": 0.62, "lavender": 0.42, "cornflower": 0.38, "seafoam2": 0.40,
           "cobalt": 0.22, "rootbeer": 0.20, "emerald": 0.26}

GLASS = {
    "seafoam":    ("#8fd0b2", 0.70, 0.80),
    "seafoam2":   ("#b4dcc4", 0.55, 0.86),
    "emerald":    ("#3a9659", 0.95, 0.55),
    "lime":       ("#bcd585", 0.75, 0.80),
    "turquoise":  ("#4fc4da", 0.95, 0.85),
    "aqua":       ("#22a9df", 0.95, 0.75),
    "cornflower": ("#aac6e6", 0.70, 0.85),
    "cobalt":     ("#2a58cf", 1.00, 0.55),
    "lavender":   ("#ddd0d8", 0.45, 0.88),
    "amber":      ("#e8aa45", 1.00, 0.80),
    "rootbeer":   ("#6f452d", 1.00, 0.45),
    "frost":      ("#e3ebe9", 0.12, 0.90),
    "clear":      ("#c4cac5", 0.08, 0.85),
    "coral":      ("#ec8e80", 0.85, 0.80),   # the rare red piece
}


# --------------------------------------------------------------------------- noise


def value_noise(h, w, scale, rng, octaves=3, persistence=0.5):
    """Smooth multi-octave noise in [-1, 1] (bicubic-upsampled random grids)."""
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gh, gw = max(2, int(h / s) + 3), max(2, int(w / s) + 3)
        grid = rng.standard_normal((gh, gw)).astype(np.float32)
        up = cv2.resize(grid, (int(gw * s), int(gh * s)), interpolation=cv2.INTER_CUBIC)
        oy, ox = rng.integers(0, max(1, up.shape[0] - h)), rng.integers(0, max(1, up.shape[1] - w))
        out += amp * up[oy:oy + h, ox:ox + w]
        total += amp
        amp *= persistence
        s /= 2.0
    out /= total
    return np.clip(out / 1.2, -1, 1)


# --------------------------------------------------------------------------- pebbles


@dataclass
class Pebble:
    cx: float
    cy: float
    R: float               # base radius (px)
    ax: float = 1.0        # anisotropy along local u
    ay: float = 1.0        # anisotropy along local v
    rot: float = 0.0
    n: float = 2.2         # superellipse exponent (2 = ellipse, higher = squarer)
    harm: list = field(default_factory=list)  # (k, amplitude, phase)
    H: float = 0.0         # height (px)
    glass: str = "seafoam"
    tone: float = 0.0      # small per-pebble lightness jitter
    seed: int = 0

    @property
    def extent(self):
        return self.R * max(self.ax, self.ay) * 1.18


def pebble_sn(p: Pebble, X, Y):
    """Normalised superellipse radius: <1 inside, 1 on the outline."""
    dx, dy = X - p.cx, Y - p.cy
    c, s = math.cos(p.rot), math.sin(p.rot)
    u = (c * dx + s * dy) / p.ax
    v = (-s * dx + c * dy) / p.ay
    phi = np.arctan2(v, u)
    rmod = np.ones_like(phi)
    for k, a, ph in p.harm:
        rmod += a * np.cos(k * phi + ph)
    n = p.n
    norm = (np.abs(u) ** n + np.abs(v) ** n) ** (1.0 / n)
    return norm / (p.R * rmod)


# --------------------------------------------------------------------------- scene


@dataclass
class Mood:
    name: str
    ground: str                 # surface colour (sRGB) under full light
    ground_texture: float       # fibre / sand grain amplitude
    ambient: float              # sky light reaching the ground
    direct: float               # sun light reaching the ground
    glass_ambient: float        # how luminous glass is on its unlit side
    glass_direct: float
    glass_glow: float           # internal scattering glow (dark mood ~ emissive)
    rim: float                  # subsurface exit glow on the shadow side
    sheen: float                # frosted surface highlight
    caustic: float              # focused light in the shadow core
    shadow_soft: float          # penumbra factor
    bloom: float                # light spill around glowing glass (dark mood)
    vignette: float
    hotspot: float              # sun pool on the surface (upper left)
    exposure: float = 1.0
    grade_shadows: str = "#000000"
    clarity_scale: float = 1.0     # how much of the ground reads through the glass
    body_gamma: tuple = (0.80, 0.45)  # colour deepening with thickness
    saturation: float = 1.0
    caustic_add: float = 0.0       # caustic light that reads even on a dark surface


SUNLIT = Mood(
    name="sunlit", ground="#f0f1eb", ground_texture=0.016, ambient=0.30, direct=0.80,
    glass_ambient=0.36, glass_direct=0.72, glass_glow=0.14, rim=0.70, sheen=0.22,
    caustic=1.35, shadow_soft=1.0, bloom=0.0, vignette=0.10, hotspot=0.10, exposure=1.0,
)

TIDEPOOL = Mood(
    name="tidepool", ground="#26393b", ground_texture=0.12, ambient=0.045, direct=0.80,
    glass_ambient=0.16, glass_direct=0.80, glass_glow=0.55, rim=1.7, sheen=0.20,
    caustic=4.2, shadow_soft=1.25, bloom=0.42, vignette=0.42, hotspot=0.92, exposure=0.92,
    grade_shadows="#040c0e", clarity_scale=0.35, body_gamma=(0.95, 0.65), saturation=1.18,
    caustic_add=0.11,
)


class Scene:
    def __init__(self, w, h, mood: Mood, seed=1, light=(0.52, 0.78)):
        self.w, self.h, self.mood = w, h, mood
        self.rng = np.random.default_rng(seed)
        lx, ly = light
        n = math.hypot(lx, ly)
        self.ldir = (lx / n, ly / n)  # direction shadows are cast (down-right)
        self.pebbles: list[Pebble] = []

    # ---------------------------------------------------------------- layout
    def scatter(self, count, rmin, rmax, colors, weights, margin=-0.15, tries=20000,
                region=None, gap=1.18, rare=None, sort_big=True, density_fn=None, glass_weights=None):
        """Place pebbles without overlaps (checked on a coarse raster) and keep
        each pebble clear of its neighbours' shadows."""
        rng = self.rng
        w, h = self.w, self.h
        gs = 6.0  # occupancy raster scale (px per cell)
        if not hasattr(self, "_occ"):
            self._occ = np.zeros((int(h / gs) + 1, int(w / gs) + 1), bool)
            self._shade = np.zeros_like(self._occ)
        occ, shade = self._occ, self._shade
        placed = 0
        radii = rmin + (rmax - rmin) * rng.uniform(0, 1, count * 4) ** 1.6
        if sort_big:
            radii = np.sort(radii)[::-1]
        ri = 0
        weights = np.asarray(weights, float)
        weights /= weights.sum()
        # a shuffled "bag" keeps the colour mix close to the weights in every layout
        exact = weights * count
        counts = np.floor(exact).astype(int)
        for i in np.argsort(-(exact - counts))[: count - counts.sum()]:
            counts[i] += 1
        bag = [c for c, n in zip(colors, counts) for _ in range(n)]
        rng.shuffle(bag)
        Lx, Ly = self.ldir
        for _ in range(tries):
            if placed >= count or ri >= len(radii):
                break
            R = float(radii[ri])
            if region is not None:
                x0, y0, x1, y1 = region
            else:
                x0, y0, x1, y1 = margin * w, margin * h, (1 - margin) * w, (1 - margin) * h
            cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
            if density_fn is not None and rng.uniform() > density_fn(cx / w, cy / h):
                continue
            family = rng.uniform()
            aspect = rng.uniform(1.0, 1.5) if rng.uniform() < 0.78 else rng.uniform(1.55, 2.2)
            harm = [(k, rng.uniform(0.0, 0.055 / (k - 1) ** 0.8), rng.uniform(0, 2 * math.pi)) for k in (2, 3, 4, 5)]
            harm.append((1, rng.uniform(0.0, 0.05), rng.uniform(0, 2 * math.pi)))   # egg-like asymmetry
            n = rng.uniform(2.0, 2.35)
            if family < 0.22:      # rounded shard: three soft corners
                harm[1] = (3, rng.uniform(0.07, 0.12), rng.uniform(0, 2 * math.pi))
            elif family < 0.40:    # tumbled bottle-wall piece: squarer outline
                n = rng.uniform(2.5, 3.1)
            p = Pebble(
                cx=cx, cy=cy, R=R / math.sqrt(aspect) * 1.05, ax=aspect, ay=1.0,
                rot=rng.uniform(0, math.pi), n=n, harm=harm,
                glass="", tone=rng.uniform(-0.05, 0.05), seed=int(rng.integers(1 << 30)),
            )
            p.H = p.R * rng.uniform(0.32, 0.46)
            # coarse raster of the pebble (dilated by the gap) and of its shadow
            pad = p.extent * 1.1 + self.shadow_len(p.R) + 8
            gx0, gx1 = int(max(0, (cx - pad) / gs)), int(min(occ.shape[1], (cx + pad) / gs + 1))
            gy0, gy1 = int(max(0, (cy - pad) / gs)), int(min(occ.shape[0], (cy + pad) / gs + 1))
            if gx1 <= gx0 or gy1 <= gy0:
                continue
            GX, GY = np.meshgrid((np.arange(gx0, gx1) + 0.5) * gs, (np.arange(gy0, gy1) + 0.5) * gs)
            body = pebble_sn(p, GX, GY) < gap
            D = self.shadow_len(p.R)
            sh = np.zeros_like(body)
            for t in (0.35, 0.7, 1.0):
                sh |= pebble_sn(p, GX - Lx * D * t, GY - Ly * D * t) < 1.0
            sub_occ, sub_shade = occ[gy0:gy1, gx0:gx1], shade[gy0:gy1, gx0:gx1]
            if (body & sub_occ).any() or (body & sub_shade).any() or (sh & sub_occ).any():
                continue
            glass = bag[placed % len(bag)] if bag else rng.choice(colors, p=weights)
            if rare and placed == rare[1]:
                glass = rare[0]
            p.glass = str(glass)
            occ[gy0:gy1, gx0:gx1] |= pebble_sn(p, GX, GY) < 1.0
            shade[gy0:gy1, gx0:gx1] |= sh
            self.pebbles.append(p)
            placed += 1
            ri += 1
        return placed

    def shadow_len(self, R):
        return R * 1.25

    # ---------------------------------------------------------------- render
    def _pebble_geometry(self, p, W, H):
        D = self.shadow_len(p.R * max(p.ax, p.ay) ** 0.5)
        pad = int(p.extent + D + p.R * 1.0 + 40)
        bx0, bx1 = int(p.cx - pad), int(p.cx + pad)
        by0, by1 = int(p.cy - pad), int(p.cy + pad)
        x0, x1 = max(0, bx0), min(W, bx1)
        y0, y1 = max(0, by0), min(H, by1)
        if x1 <= x0 or y1 <= y0:
            return None
        # geometry is built on the unclipped box so off-canvas parts still cast shadows
        X, Y = np.meshgrid(np.arange(bx0, bx1, dtype=np.float32), np.arange(by0, by1, dtype=np.float32))
        sn = pebble_sn(p, X, Y)
        Rloc = p.R * min(p.ax, p.ay)
        dist = (1 - sn) * Rloc
        alpha = np.clip(dist / 1.15 + 0.5, 0, 1).astype(np.float32)
        inside = np.clip(sn, 0, 1)
        hgt = p.H * np.clip(1 - inside ** 2.6, 0, 1) ** 0.50
        prng = np.random.default_rng(p.seed)
        lump = value_noise(by1 - by0, bx1 - bx0, max(10, Rloc * 0.9), prng, octaves=2)
        hgt = (hgt * (1 + 0.035 * lump) * (alpha > 0)).astype(np.float32)
        crop = (slice(y0 - by0, y1 - by0), slice(x0 - bx0, x1 - bx0))
        return dict(D=D, box=(x0, x1, y0, y1), full=(bx0, bx1, by0, by1), crop=crop,
                    X=X, Y=Y, alpha=alpha, hgt=hgt, Rloc=Rloc, prng=prng)

    def render(self, out_path=None):
        m = self.mood
        rng = np.random.default_rng(int(self.rng.integers(1 << 30)))
        W, H = self.w, self.h
        Lx, Ly = self.ldir

        # ground albedo with texture
        g = hex_lin(m.ground).astype(np.float32)
        tex = value_noise(H, W, 6, rng, octaves=3) * 0.55 + value_noise(H, W, 110, rng, octaves=3) * 0.45
        grain = cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.8)
        albedo = g[None, None, :] * (1 + m.ground_texture * (tex[..., None] + 0.45 * grain[..., None]))

        # sunlight across the surface: a broad pool from the upper left
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        nx, ny = xx / W, yy / H
        pool = np.exp(-(((nx - 0.22) / 0.85) ** 2 + ((ny - 0.05) / 0.95) ** 2))
        light_field = ((1 - m.hotspot) + m.hotspot * pool).astype(np.float32)
        vig = 1 - m.vignette * np.clip(((nx - 0.5) ** 2 / 0.30 + (ny - 0.5) ** 2 / 0.28), 0, 1.7) ** 1.35

        direct_T = np.ones((H, W, 3), np.float32)
        ao = np.ones((H, W), np.float32)
        caustic_light = np.zeros((H, W, 3), np.float32)
        geo = []

        # ---------------- pass 1: shadows, caustics and contact occlusion
        for p in self.pebbles:
            gm = self._pebble_geometry(p, W, H)
            if gm is None:
                continue
            geo.append((p, gm))
            col, tint, transmit = GLASS[p.glass]
            C = hex_lin(col).astype(np.float32) * (1 + p.tone)
            x0, x1, y0, y1 = gm["box"]
            bx0, bx1, by0, by1 = gm["full"]
            cr = gm["crop"]
            X, Y, alpha, hgt, Rloc, D = gm["X"], gm["Y"], gm["alpha"], gm["hgt"], gm["Rloc"], gm["D"]
            bw, bh = bx1 - bx0, by1 - by0

            steps = 20
            sh = np.zeros_like(hgt)
            for i in range(steps + 1):
                t = i / steps
                sl = (hgt >= t * p.H * 0.97).astype(np.float32) * alpha
                M = np.float32([[1, 0, Lx * D * t], [0, 1, Ly * D * t]])
                sh = np.maximum(sh, cv2.warpAffine(sl, M, (bw, bh), flags=cv2.INTER_LINEAR))
            sig_near = max(1.0, 0.012 * Rloc * m.shadow_soft)
            sig_far = max(2.0, 0.085 * Rloc * m.shadow_soft)
            near = cv2.GaussianBlur(sh, (0, 0), sig_near)
            far = cv2.GaussianBlur(sh, (0, 0), sig_far)
            rel = ((X - p.cx) * Lx + (Y - p.cy) * Ly) / (Rloc + D)
            wfar = np.clip(rel * 1.1, 0, 1) ** 1.2
            shadow = near * (1 - wfar) + far * wfar

            cn = C / max(float(C.max()), 1e-4)
            tcol = (1 - tint) + tint * cn
            tcol = np.clip(tcol, 0, 1) ** 1.7 * transmit
            ccx, ccy = p.cx + Lx * D * 0.62, p.cy + Ly * D * 0.62
            du, dv = X - ccx, Y - ccy
            along = du * Lx + dv * Ly
            across = -du * Ly + dv * Lx
            core = np.exp(-(along / (Rloc * 0.62)) ** 2 - (across / (Rloc * 0.40)) ** 2)
            core2 = np.exp(-(along / (Rloc * 0.30)) ** 2 - (across / (Rloc * 0.20)) ** 2)
            edge = np.clip(far - cv2.GaussianBlur(sh, (0, 0), sig_far * 3.0), 0, 1)
            focus = 0.30 + m.caustic * (0.75 * core + 0.45 * core2) - 0.55 * edge
            focus = np.clip(focus, 0.04, None)
            T = 1 - shadow[..., None] * (1 - tcol[None, None, :] * focus[..., None])
            direct_T[y0:y1, x0:x1] *= np.clip(T, 0, None)[cr]
            if m.caustic_add > 0:
                cmix = shadow * (0.75 * core + 0.45 * core2)
                caustic_light[y0:y1, x0:x1] += (cmix[..., None] * (cn ** 1.4)[None, None, :] * min(1.0, tint + 0.25))[cr]

            base = cv2.GaussianBlur(alpha, (0, 0), max(1.5, 0.05 * Rloc))
            shift = np.float32([[1, 0, Lx * 0.05 * Rloc], [0, 1, Ly * 0.05 * Rloc]])
            base = cv2.warpAffine(base, shift, (bw, bh))
            ao[y0:y1, x0:x1] *= (1 - 0.55 * base * (1 - alpha))[cr]

        # ---------------- ground
        E = (m.ambient * ao[..., None] + m.direct * direct_T * ao[..., None]) * light_field[..., None]
        img = (albedo * E).astype(np.float32)
        if m.caustic_add > 0:
            img += m.caustic_add * caustic_light * light_field[..., None]
        ground = img.copy()

        # ---------------- pass 2: glass bodies (seen from above, frosted, translucent)
        sx_, sy_, sz_ = -Lx * 0.66, -Ly * 0.66, 0.75
        hx, hy, hz = sx_, sy_, sz_ + 1
        hn = math.sqrt(hx * hx + hy * hy + hz * hz)
        for p, gm in geo:
            col, tint, transmit = GLASS[p.glass]
            C = hex_lin(col).astype(np.float32) * (1 + p.tone)
            cn = C / max(float(C.max()), 1e-4)
            x0, x1, y0, y1 = gm["box"]
            cr = gm["crop"]
            Rloc, prng = gm["Rloc"], gm["prng"]
            gy, gx = np.gradient(gm["hgt"])
            gy, gx = gy[cr], gx[cr]
            alpha, hgt = gm["alpha"][cr], gm["hgt"][cr]
            nrm = np.sqrt(gx ** 2 + gy ** 2 + 1)
            Nx, Ny, Nz = -gx / nrm, -gy / nrm, 1 / nrm
            ndl = np.clip(Nx * sx_ + Ny * sy_ + Nz * sz_, 0, 1)
            ndh = np.clip((Nx * hx + Ny * hy + Nz * hz) / hn, 0, 1)
            thick = np.clip(hgt / max(p.H, 1e-3), 0, 1)
            lf = light_field[y0:y1, x0:x1, None]

            Cs = np.clip(C.mean() + (C - C.mean()) * m.saturation, 1e-4, None)
            body = Cs[None, None, :] ** (m.body_gamma[0] + m.body_gamma[1] * thick[..., None])
            shade = m.glass_ambient + m.glass_direct * ndl ** 1.2
            col_lin = body * shade[..., None] * lf
            gw = 0.55 if p.glass in ("frost", "clear") else 1.0
            col_lin += gw * m.glass_glow * body * (0.5 + 0.5 * (1 - thick))[..., None] * lf

            # translucency: the frosted body passes a blurred, tinted view of what lies beneath
            clarity = CLARITY.get(p.glass, 0.40) * m.clarity_scale
            under = cv2.GaussianBlur(ground[y0:y1, x0:x1], (0, 0), max(3, 0.20 * Rloc))
            tcol = (1 - tint) + tint * cn
            col_lin = col_lin * (1 - clarity) + under * (tcol ** 1.3)[None, None, :] * clarity * 1.15

            # light exiting the edge that faces away from the sun (subsurface rim)
            nxy = np.sqrt(Nx ** 2 + Ny ** 2) + 1e-4
            away = np.clip(-(Nx * sx_ + Ny * sy_) / nxy, 0, 1)
            band = np.clip(1 - thick, 0, 1) ** 1.5 * (alpha > 0)
            col_lin += m.rim * (cn ** 1.2)[None, None, :] * (band * away ** 1.4)[..., None] * lf * 0.9
            # refraction darkening at the steep edge facing the sun
            toward = np.clip((Nx * sx_ + Ny * sy_) / nxy, 0, 1)
            col_lin *= (1 - 0.22 * (band * toward ** 2))[..., None]
            # frosted sheen
            sheen = m.sheen * (0.75 * ndh ** 18 + 0.35 * ndl ** 4 * (0.4 + 0.6 * (1 - thick)))
            col_lin += (sheen[..., None] * lf) * np.array([1.0, 1.0, 0.985], np.float32)
            # frost texture: grain, mottling and tiny pits that catch the light
            fine = cv2.GaussianBlur(prng.standard_normal(hgt.shape).astype(np.float32), (0, 0), 0.7)
            mott = value_noise(y1 - y0, x1 - x0, max(6, Rloc * 0.16), prng, octaves=2)
            mamp = 0.018 if p.glass in ("frost", "clear", "lavender") else 0.03
            col_lin *= (1 + 0.035 * fine + mamp * mott)[..., None]
            npits = int((x1 - x0) * (y1 - y0) / 120)
            if npits > 0:
                pits = np.zeros(hgt.shape, np.float32)
                py = prng.integers(0, y1 - y0, npits)
                px = prng.integers(0, x1 - x0, npits)
                pits[py, px] = prng.uniform(0.3, 1.0, npits)
                pits = cv2.GaussianBlur(pits, (0, 0), 0.6) * 2.4
                pits *= 0.3 + 0.7 * ndl
                col_lin += (0.26 * pits)[..., None] * lf * (alpha > 0.6)[..., None]

            a = alpha[..., None]
            img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + col_lin * a

        if m.bloom > 0:
            lum = img.max(axis=2, keepdims=True)
            bright = img * np.clip((lum - 0.22) * 2.5, 0, 1)
            small = cv2.resize(bright, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
            b1 = cv2.GaussianBlur(small, (0, 0), 5)
            b2 = cv2.GaussianBlur(small, (0, 0), 18)
            bl = cv2.resize(b1 * 0.55 + b2 * 0.45, (W, H), interpolation=cv2.INTER_CUBIC)
            img += m.bloom * bl

        img *= vig[..., None] * m.exposure
        gs = hex_lin(m.grade_shadows)
        img = img + gs[None, None, :] * (1 - np.clip(img / 0.04, 0, 1))
        img = img / (1 + 0.10 * img) * 1.10
        out = lin_to_srgb(img)
        out = np.clip(out + rng.uniform(-0.5, 0.5, out.shape).astype(np.float32) / 255, 0, 1)
        im = Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGB")
        if out_path:
            if out_path.endswith(".jpg"):
                im.save(out_path, quality=93, subsampling=0, optimize=True, progressive=True)
            else:
                im.save(out_path, optimize=True)
        return im
