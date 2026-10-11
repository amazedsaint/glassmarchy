"""Turn raw desktop captures into the theme previews and the screenshots folder.

The captures are `grim` screenshots of Omarchy 4.0.2 (Hyprland 0.56.1) at
3024 x 1900, 2x scale. Only resizing, cropping and PNG palette reduction
happen here.

Usage: python3 .tools/screenshots.py RAW_DIR

RAW_DIR must contain:
  hero-dark.png  hero-light.png              windows open, Tide Pool and Sunlit
  desk-dark-1..3.png  desk-light-1..3.png    an empty workspace on each wallpaper
  menu-desk-dark.png  menu-desk-light.png    Omarchy menu open over the wallpaper
  picker-dark.png                            theme picker open
  notify-light.png                           a notification on screen

Writes preview.png, variants/sunlit/preview.png and screenshots/*.jpg.
Needs Pillow; `pip install imagequant pyoxipng` makes the previews about a
third of the size.
"""
import os
import sys

from PIL import Image

if len(sys.argv) != 2:
    sys.exit(__doc__)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = sys.argv[1]
OUT = os.path.join(REPO, "screenshots")

FULL_SIZE = (1800, 1131)   # the screen's 16:10, at the width Omarchy's own previews use
TILE_SIZE = (1200, 750)

# Whole screens: (capture, output name).
SCREENS = [
    ("hero-dark", "tide-pool"),
    ("hero-light", "sunlit"),
    ("desk-dark-1", "wallpaper-1-tide-pool"),
    ("desk-dark-2", "wallpaper-2-moonlit-wrack"),
    ("desk-dark-3", "wallpaper-3-night-swim"),
    ("desk-light-1", "wallpaper-1-sunlit-shore"),
    ("desk-light-2", "wallpaper-2-low-tide"),
    ("desk-light-3", "wallpaper-3-white-sand"),
]

# Close-ups: (capture, output name, crop box in capture pixels). All 16:10.
TILES = [
    ("menu-desk-dark", "tide-pool-menu", (472, 300, 2552, 1600)),
    ("menu-desk-light", "sunlit-menu", (472, 300, 2552, 1600)),
    ("picker-dark", "tide-pool-theme-picker", (520, 330, 2504, 1570)),
    ("notify-light", "sunlit-notification", (1744, 0, 3024, 800)),
]


def load(name):
    image = Image.open(os.path.join(RAW, name + ".png")).convert("RGB")
    if image.size != (3024, 1900):
        sys.exit(f"{name}.png is {image.size[0]}x{image.size[1]}, expected 3024x1900")
    return image


def report(path):
    print(f"  {os.path.relpath(path, REPO)}  {os.path.getsize(path) // 1024} KB")


def save_png(image, path):
    try:
        import imagequant
    except ImportError:
        image.save(path, optimize=True)
    else:
        imagequant.quantize_pil_image(image.convert("RGBA"), dithering_level=1.0, max_colors=256).save(path, optimize=True)
    try:
        import oxipng
    except ImportError:
        pass
    else:
        oxipng.optimize(path, level=4)
    report(path)


def save_jpg(image, name):
    path = os.path.join(OUT, name + ".jpg")
    image.save(path, quality=90, subsampling=0, optimize=True, progressive=True)
    report(path)


print("Theme picker previews")
for raw, dest in (("hero-dark", "preview.png"), ("hero-light", os.path.join("variants", "sunlit", "preview.png"))):
    save_png(load(raw).resize(FULL_SIZE, Image.LANCZOS), os.path.join(REPO, dest))

print("Screenshots")
os.makedirs(OUT, exist_ok=True)
for raw, name in SCREENS:
    save_jpg(load(raw).resize(FULL_SIZE, Image.LANCZOS), name)
for raw, name, box in TILES:
    x0, y0, x1, y1 = box
    assert abs((x1 - x0) / (y1 - y0) - 1.6) < 1e-6, name
    save_jpg(load(raw).crop(box).resize(TILE_SIZE, Image.LANCZOS), name)
