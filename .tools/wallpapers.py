"""Render the Sea Glass wallpaper set: the same three compositions lit two ways.

    python3 wallpapers.py                      # 3840x2160 into backgrounds/ and variants/sunlit/backgrounds/
    python3 wallpapers.py --size 5120x1440     # e.g. a 32:9 ultrawide
    python3 wallpapers.py --only shore --size 1920x1080 --dark-out /tmp/test --light-out /tmp/test

Pebble sizes are defined in screen-height units, so every size keeps the same scale;
wider screens get proportionally more glass. The big-pebble layout takes a few minutes at 4K.
"""
import math
import sys
import time

from seaglass_render import SUNLIT, TIDEPOOL, Scene

PALETTE = ["seafoam", "seafoam2", "emerald", "lime", "turquoise", "aqua", "cornflower",
           "cobalt", "lavender", "amber", "rootbeer", "frost", "clear"]
WEIGHTS = [1.5, 1.1, 0.8, 0.8, 1.3, 0.8, 1.0, 0.8, 0.6, 0.9, 0.32, 0.7, 0.45]


def shore(sc, k, ar=1.0):
    """Scattered like a tray of glass drying in the sun (the reference photo)."""
    sc.scatter(round(42 * ar), 54 * k, 110 * k, PALETTE, WEIGHTS, rare=("coral", 11), gap=1.10, tries=200000, margin=-0.10)


def wrack(sc, k, ar=1.0):
    """A drift line left by the receding tide: a band from lower left to upper right."""
    def band(x, y):
        c = 0.78 - 0.50 * x + 0.05 * math.sin(7.0 * x)
        return math.exp(-((y - c) / 0.13) ** 2)
    sc.scatter(round(30 * ar), 36 * k, 90 * k, PALETTE, WEIGHTS, rare=("coral", 6), gap=1.08,
               density_fn=band, tries=90000, margin=-0.08)


def corners(sc, k, ar=1.0):
    """A few large pieces at the edges, calm open centre for windows."""
    def edge(x, y):
        d = max(abs(x - 0.5) / 0.5, abs(y - 0.5) / 0.5)
        return max(0.0, min(1.0, (d - 0.62) / 0.25))
    sc.scatter(round(11 * ar), 150 * k, 235 * k, PALETTE, WEIGHTS, rare=("coral", 9), gap=1.05,
               density_fn=edge, tries=90000, margin=-0.12)


LAYOUTS = [("shore", shore, 11), ("wrack", wrack, 23), ("corners", corners, 5)]
NAMES = {
    ("tidepool", "shore"): "1-tide-pool", ("tidepool", "wrack"): "2-moonlit-wrack", ("tidepool", "corners"): "3-night-swim",
    ("sunlit", "shore"): "1-sunlit-shore", ("sunlit", "wrack"): "2-low-tide", ("sunlit", "corners"): "3-white-sand",
}


def main():
    import argparse
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--size", default="3840x2160", help="WxH, e.g. 5120x1440 for an ultrawide (default 3840x2160)")
    ap.add_argument("--dark-out", default=os.path.join(repo, "backgrounds"))
    ap.add_argument("--light-out", default=os.path.join(repo, "variants", "sunlit", "backgrounds"))
    ap.add_argument("--only", default="", help="comma list of layouts: shore,wrack,corners")
    args = ap.parse_args()
    W, H = (int(x) for x in args.size.lower().split("x"))
    k = H / 1080
    ar = (W / H) / (16 / 9)
    only = set(filter(None, args.only.split(",")))
    for mood, out in ((TIDEPOOL, args.dark_out), (SUNLIT, args.light_out)):
        os.makedirs(out, exist_ok=True)
        for name, fn, seed in LAYOUTS:
            if only and name not in only:
                continue
            t = time.time()
            sc = Scene(W, H, mood, seed=seed)
            fn(sc, k, ar)
            path = os.path.join(out, NAMES[(mood.name, name)] + ".jpg")
            sc.render(path)
            print(f"{path}: {len(sc.pebbles)} pebbles, {time.time() - t:.1f}s", flush=True)


if __name__ == "__main__":
    main()
