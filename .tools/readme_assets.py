"""README figures: motion curves (small multiples) and the palette card.

    python3 readme_assets.py            # writes ../.assets/{motion.svg,palette.svg}
"""
import math
import os
import sys

from palette import SUNLIT, TIDEPOOL

REPO = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, ".assets")
os.makedirs(OUT, exist_ok=True)

P = TIDEPOOL
FONT = "font-family:'JetBrains Mono','SFMono-Regular',Menlo,Consolas,monospace"


# ---------------------------------------------------------------- curves

def bezier(p1, p2, steps=400):
    """Return y(t) sampled on x in [0,1] for a CSS-style cubic bezier."""
    (x1, y1), (x2, y2) = p1, p2

    def bx(t):
        return 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3

    def by(t):
        return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3

    pts = [(bx(i / steps), by(i / steps)) for i in range(steps + 1)]
    return pts


def spring(k, c, m=1.0, dt=0.001, t_end=0.6):
    """Same closed form Hyprland uses (hyprutils advanceSpring), from rest at 0 to 1."""
    w0 = math.sqrt(k / m)
    g = c / (2 * m)
    wd = math.sqrt(max(w0 * w0 - g * g, 1e-9))
    pts = []
    t = 0.0
    while t <= t_end + 1e-9:
        d = -1.0
        v = 0.0
        x = math.exp(-g * t) * (d * math.cos(wd * t) + (v + g * d) / wd * math.sin(wd * t))
        pts.append((t, 1 + x))
        t += dt
    return pts


panels = [
    ("pebble", "windows in", "spring k=324 c=23.4", [(t * 1000, y) for t, y in spring(324, 23.4)]),
    ("drift", "windows move", "spring k=225 c=27", [(t * 1000, y) for t, y in spring(225, 27)]),
    ("glassOut", "workspaces · borders", "bezier .16 1 .3 1 · 340ms", [(x * 340, y) for x, y in bezier((0.16, 1), (0.3, 1))] + [(600, 1)]),
    ("tide", "focus crossfade", "bezier .45 .05 .55 .95 · 320ms", [(x * 320, y) for x, y in bezier((0.45, 0.05), (0.55, 0.95))] + [(600, 1)]),
    ("sink", "closing", "bezier .55 .06 .68 .19 · 170ms", [(x * 170, y) for x, y in bezier((0.55, 0.06), (0.68, 0.19))] + [(600, 1)]),
]

PW, PH = 248, 168          # panel size
PAD_L, PAD_T, PAD_B = 34, 52, 30
GAP = 14
W = 24 + len(panels) * PW + (len(panels) - 1) * GAP + 24
H = 52 + PH + 26 + 20
surface = P["background"]
grid = P["selection"]
ink = P["foreground"]
ink2 = P["dark_foreground"]
line = P["accent"]

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
       f'aria-label="Sea Glass animation curves: progress over time for pebble, drift, glassOut, tide and sink">',
       f'<rect width="{W}" height="{H}" rx="16" fill="{surface}"/>',
       f'<text x="24" y="34" style="{FONT};font-size:15px;font-weight:700" fill="{P["bright_foreground"]}">Motion</text>',
       f'<text x="96" y="34" style="{FONT};font-size:12px" fill="{ink2}">progress over the first 600 ms · dashed line = final position</text>']
xmax, ymin, ymax = 600.0, -0.04, 1.10
for i, (name, use, spec, pts) in enumerate(panels):
    ox = 24 + i * (PW + GAP)
    oy = 52
    gx0, gy0 = ox + PAD_L, oy + PAD_T - 22
    gw, gh = PW - PAD_L - 10, PH - PAD_T - PAD_B + 30

    def X(t):
        return gx0 + gw * min(t, xmax) / xmax

    def Y(v):
        return gy0 + gh * (1 - (v - ymin) / (ymax - ymin))

    svg.append(f'<rect x="{ox}" y="{oy}" width="{PW}" height="{PH + 26}" rx="11" fill="{P["lighter_background"]}"/>')
    svg.append(f'<text x="{ox + 14}" y="{oy + 22}" style="{FONT};font-size:13px;font-weight:700" fill="{ink}">{name}</text>')
    svg.append(f'<text x="{ox + 14 + len(name) * 8.2 + 8}" y="{oy + 22}" style="{FONT};font-size:11px" fill="{ink2}">{use}</text>')
    # recessive grid: baseline and target
    svg.append(f'<line x1="{gx0}" y1="{Y(0):.1f}" x2="{gx0 + gw}" y2="{Y(0):.1f}" stroke="{grid}" stroke-width="1"/>')
    svg.append(f'<line x1="{gx0}" y1="{Y(1):.1f}" x2="{gx0 + gw}" y2="{Y(1):.1f}" stroke="{ink2}" stroke-width="1" stroke-dasharray="3 4" opacity="0.7"/>')
    for ms, anchor in ((0, "start"), (300, "middle"), (600, "end")):
        svg.append(f'<text x="{X(ms):.1f}" y="{gy0 + gh + 16:.1f}" text-anchor="{anchor}" style="{FONT};font-size:10px" fill="{ink2}">{ms}{" ms" if ms == 600 else ""}</text>')
    svg.append(f'<text x="{gx0 - 8}" y="{Y(1) + 3.5:.1f}" text-anchor="end" style="{FONT};font-size:10px" fill="{ink2}">1</text>')
    svg.append(f'<text x="{gx0 - 8}" y="{Y(0) + 3.5:.1f}" text-anchor="end" style="{FONT};font-size:10px" fill="{ink2}">0</text>')
    d = "M" + " L".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in pts if t <= xmax)
    svg.append(f'<path d="{d}" fill="none" stroke="{line}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    svg.append(f'<text x="{ox + 14}" y="{oy + PH + 16}" style="{FONT};font-size:10.5px" fill="{ink2}">{spec}</text>')
svg.append("</svg>")
open(os.path.join(OUT, "motion.svg"), "w").write("\n".join(svg))


# ---------------------------------------------------------------- palette card

order = [("background", "bg"), ("lighter_background", "surface"), ("selection", "selection"), ("muted", "muted"),
         ("foreground", "fg"), ("bright_foreground", "bright"), ("accent", "accent"),
         ("red", "coral"), ("orange", "amber"), ("yellow", "honey"), ("green", "kelly"), ("cyan", "turquoise"),
         ("blue", "cobalt"), ("magenta", "lavender"), ("brown", "root beer"),
         ("bright_green", "lime"), ("bright_cyan", "aqua"), ("bright_blue", "cornflower")]
CW, CH = 74, 46
cols = 9
rows = math.ceil(len(order) / cols)
PWd = 24 + cols * CW + (cols - 1) * 8 + 24
blockh = 50 + rows * (CH + 40)
HH = blockh * 2 + 16
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PWd}" height="{HH}" viewBox="0 0 {PWd} {HH}" role="img" aria-label="Sea Glass palettes for Tide Pool and Sunlit">']
for bi, (title, PP) in enumerate((("Tide Pool · dark", TIDEPOOL), ("Sunlit · light", SUNLIT))):
    oy = bi * (blockh + 16)
    svg.append(f'<rect x="0" y="{oy}" width="{PWd}" height="{blockh}" rx="16" fill="{PP["background"]}"/>')
    svg.append(f'<text x="24" y="{oy + 30}" style="{FONT};font-size:14px;font-weight:700" fill="{PP["bright_foreground"]}">{title}</text>')
    for i, (key, label) in enumerate(order):
        cx = 24 + (i % cols) * (CW + 8)
        cy = oy + 44 + (i // cols) * (CH + 40)
        svg.append(f'<rect x="{cx}" y="{cy}" width="{CW}" height="{CH}" rx="10" fill="{PP[key]}" stroke="{PP["foreground"]}" stroke-opacity="0.16"/>')
        svg.append(f'<text x="{cx + 2}" y="{cy + CH + 15}" style="{FONT};font-size:10.5px" fill="{PP["foreground"]}">{label}</text>')
        svg.append(f'<text x="{cx + 2}" y="{cy + CH + 28}" style="{FONT};font-size:10px" fill="{PP["dark_foreground"]}">{PP[key]}</text>')
svg.append("</svg>")
open(os.path.join(OUT, "palette.svg"), "w").write("\n".join(svg))
print("ok")
