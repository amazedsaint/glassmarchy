"""Unlock (Plymouth) art: a small arc of sea glass pebbles on a transparent PNG,
plus the preview-unlock.png the Style > Unlock picker shows.

    python3 unlock_art.py [omarchy-path] [out-dark] [out-light]

omarchy-path defaults to $OMARCHY_PATH (or /usr/share/omarchy); it is only used
for Plymouth's entry/lock/bullet images in preview-unlock.png.
"""
import math
import sys
from dataclasses import replace

import numpy as np
from PIL import Image

from palette import SUNLIT as SUNLIT_P, TIDEPOOL as TIDEPOOL_P
from seaglass_render import SUNLIT, TIDEPOOL, Pebble, Scene

SCALE = 2  # render at 2x, downsample for clean edges


def cluster(scene, W, H):
    """Seven pebbles in a gentle arc, largest in the middle."""
    spec = [
        ("lavender", -3, 0.62, 1.25, 0.4),
        ("cobalt", -2, 0.74, 1.15, 2.2),
        ("turquoise", -1, 0.90, 1.35, 0.9),
        ("seafoam", 0, 1.08, 1.30, 2.6),
        ("amber", 1, 0.88, 1.20, 1.4),
        ("lime", 2, 0.72, 1.30, 0.2),
        ("frost", 3, 0.60, 1.15, 1.9),
    ]
    rng = np.random.default_rng(42)
    base = H * 0.165
    for glass, i, size, aspect, rot in spec:
        x = W / 2 + i * W * 0.104
        y = H * 0.40 + (abs(i) ** 1.6) * H * 0.045
        R = base * size
        p = Pebble(cx=x, cy=y, R=R / math.sqrt(aspect), ax=aspect, ay=1.0, rot=rot, n=2.2,
                   harm=[(k, rng.uniform(0, 0.05 / (k - 1) ** 0.8), rng.uniform(0, 6.28)) for k in (2, 3, 4)],
                   glass=glass, tone=0.0, seed=int(rng.integers(1 << 30)))
        p.H = p.R * 0.40
        scene.pebbles.append(p)


def unblend(img, bg):
    """GIMP-style colour-to-alpha against a known background: returns RGBA that
    composites back to `img` over `bg` exactly."""
    C = img.astype(np.float32) / 255
    B = np.asarray(bg, np.float32) / 255
    with np.errstate(divide="ignore", invalid="ignore"):
        up = np.where(C > B, (C - B) / np.maximum(1 - B, 1e-4), 0)
        down = np.where(C < B, (B - C) / np.maximum(B, 1e-4), 0)
    a = np.clip(np.maximum(up, down).max(axis=2), 0, 1)
    a = np.where(np.abs(C - B).max(axis=2) < 2.5 / 255, 0, a)
    col = np.where(a[..., None] > 0, B + (C - B) / np.maximum(a[..., None], 1e-4), 0)
    out = np.dstack([np.clip(col, 0, 1), a])
    return (out * 255 + 0.5).astype(np.uint8)


def render_logo(mood, P):
    W, H = 760 * SCALE, 340 * SCALE
    flat = replace(mood, ground=P["background"], ground_texture=0.0, hotspot=0.0, vignette=0.0,
                   bloom=mood.bloom * 0.35, grade_shadows="#000000")
    sc = Scene(W, H, flat, seed=3, light=(0.52, 0.78))
    sc.shadow_len = lambda R: R * 0.85
    cluster(sc, W, H)
    im = np.asarray(sc.render(None).convert("RGB")).astype(np.float32) / 255
    # re-expose so the empty ground lands exactly on the theme background,
    # then un-blend against that background
    from seaglass_render import srgb_to_lin, lin_to_srgb, hex_lin
    ref = np.median(im[:12, :12].reshape(-1, 3), axis=0)
    lin = srgb_to_lin(im) * (hex_lin(P["background"]) / srgb_to_lin(ref))[None, None, :]
    im = (np.clip(lin_to_srgb(lin), 0, 1) * 255 + 0.5).astype(np.uint8)
    h = P["background"].lstrip("#")
    rgba = unblend(im, [int(h[i:i + 2], 16) for i in (0, 2, 4)])
    # feather the canvas edge so glow never ends in a hard line
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    edge = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
    feather = np.clip(edge / (60 * SCALE), 0, 1) ** 1.5
    rgba[..., 3] = (rgba[..., 3] * feather).astype(np.uint8)
    logo = Image.fromarray(rgba, "RGBA").resize((W // SCALE, H // SCALE), Image.LANCZOS)
    bbox = logo.getbbox()
    pad = 16
    logo = logo.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(logo.width, bbox[2] + pad), min(logo.height, bbox[3] + pad)))
    return logo


def tint(asset, color):
    a = np.asarray(asset.convert("RGBA"))
    h = color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    out = np.zeros_like(a)
    out[..., :3] = rgb
    out[..., 3] = a[..., 3]
    return Image.fromarray(out, "RGBA")


def preview_unlock(logo, P, omarchy_src):
    W, H = 1920, 1080
    bg = Image.new("RGBA", (W, H), P["background"])
    lx, ly = W // 2 - logo.width // 2, H // 2 - logo.height // 2
    bg.alpha_composite(logo, (lx, ly))
    pdir = f"{omarchy_src}/default/plymouth"
    entry = tint(Image.open(f"{pdir}/entry.png"), P["foreground"])
    lock = tint(Image.open(f"{pdir}/lock.png"), P["foreground"])
    bullet = tint(Image.open(f"{pdir}/bullet.png"), P["foreground"]).resize((7, 7), Image.LANCZOS)
    ex, ey = W // 2 - entry.width // 2, ly + logo.height + 40
    bg.alpha_composite(entry, (ex, ey))
    lh = int(entry.height * 0.8)
    lw = int(84 * lh / 96)
    lock = lock.resize((lw, lh), Image.LANCZOS)
    bg.alpha_composite(lock, (ex - lw - 15, ey + entry.height // 2 - lh // 2))
    for i in range(6):
        bg.alpha_composite(bullet, (ex + 20 + i * 12, int(ey + entry.height / 2 - 3.5)))
    return bg.convert("RGB")


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    argv = sys.argv[1:] + [None] * 3
    src = argv[0] or os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")
    out_dark = argv[1] or repo
    out_light = argv[2] or os.path.join(repo, "variants", "sunlit")
    for mood, P, out in ((TIDEPOOL, TIDEPOOL_P, out_dark), (SUNLIT, SUNLIT_P, out_light)):
        logo = render_logo(mood, P)
        logo.save(f"{out}/unlock.png", optimize=True)
        preview_unlock(logo, P, src).save(f"{out}/preview-unlock.png", optimize=True)
        print(out, logo.size)
