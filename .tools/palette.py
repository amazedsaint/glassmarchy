"""Sea Glass palettes — sampled from a sunlit tray of beach glass.

Two moods share one set of glass pebbles:
  tidepool  — dark: wet slate, the glass glowing as if backlit
  sunlit    — light: frosted paper in sunshine, colored shadows
"""

GLASS = {  # reference pebble colours measured from the photo (mid-tones)
    "seafoam":    "#7cc4a2",
    "emerald":    "#3c8f52",
    "lime":       "#b5cf7a",
    "turquoise":  "#4cc0d6",
    "aqua":       "#1aa6dc",
    "cornflower": "#a9c3e2",
    "cobalt":     "#2355c8",
    "lavender":   "#d6c8cc",
    "amber":      "#e2a43c",
    "rootbeer":   "#7c4a30",
    "frost":      "#e4ebe6",
    "clear":      "#b8bcb6",
}

TIDEPOOL = dict(
    mode="dark",
    accent="#7fd4b0",
    selection="#21393c",
    muted="#5a7476",
    background="#0f1a1d",
    dark_background="#0b1517",
    darker_background="#071012",
    lighter_background="#162629",
    foreground="#c9d9d3",
    dark_foreground="#7e9894",
    light_foreground="#dde8e3",
    bright_foreground="#f0f6f2",
    red="#ee8b80",
    yellow="#f0c46e",
    orange="#eba25d",
    green="#72c48a",
    cyan="#5dcfe0",
    blue="#7ea9f0",
    magenta="#c4a7e8",
    brown="#a8714f",
    bright_red="#f6aba2",
    bright_yellow="#f6d898",
    bright_green="#b9dc86",
    bright_cyan="#96e3ea",
    bright_blue="#a9c6f6",
    bright_magenta="#dcc9f1",
)

SUNLIT = dict(
    mode="light",
    accent="#0f7686",
    selection="#cfe4da",
    muted="#8a9792",
    background="#f3f4ee",
    dark_background="#e9ece4",
    darker_background="#dde2d8",
    lighter_background="#e6e9e0",
    foreground="#24363b",
    dark_foreground="#64736f",
    light_foreground="#3a4c52",
    bright_foreground="#0f2328",
    red="#bb3f36",
    yellow="#8a5f00",
    orange="#a85816",
    green="#257a40",
    cyan="#0c7488",
    blue="#2a53c4",
    magenta="#8a54b6",
    brown="#7a4428",
    bright_red="#d55a4f",
    bright_yellow="#a87608",
    bright_green="#5a8e1e",
    bright_cyan="#128aa5",
    bright_blue="#4072dd",
    bright_magenta="#9a63c6",
)


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rel_lum(h):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def mix(a, b, t):
    ra, rb = hex2rgb(a), hex2rgb(b)
    return "#%02x%02x%02x" % tuple(int(round(x * (1 - t) + y * t)) for x, y in zip(ra, rb))
