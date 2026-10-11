# Sea Glass tools

Everything in the theme is generated from `palette.py`, so a colour change happens
in one place. Omarchy ignores this folder (dot-folders are never staged).

| Script | Does | Needs |
|---|---|---|
| `build_theme.py` | writes every config file for both moods (`colors.toml`, `shell.toml`, `hyprland.lua`, the 3.x files, btop, …) | Python 3 |
| `wallpapers.py` | renders the six wallpapers; `--size 5120x1440` for other screens, `--only shore` for one layout | numpy, opencv-python, pillow |
| `unlock_art.py` | renders `unlock.png` and `preview-unlock.png` for both moods | same, plus an Omarchy install (uses `$OMARCHY_PATH` for Plymouth's entry and lock images) |
| `screenshots.py` | turns raw desktop captures into both `preview.png` files and everything in `screenshots/` | pillow; imagequant and pyoxipng make smaller PNGs |
| `validate_lua.py` | runs a `hyprland.lua` against Hyprland's own option tables, animation tree and rule fields | lupa, a Hyprland source checkout |
| `readme_assets.py` | redraws the motion and palette figures in `.assets` | Python 3 |
| `seaglass_render.py` | the renderer: frosted glass shading, translucency, caustic shadows | — |

```bash
cd .tools
python3 build_theme.py
python3 wallpapers.py
python3 unlock_art.py
python3 validate_lua.py ~/src/Hyprland ../hyprland.lua ../variants/sunlit/hyprland.lua
```

After regenerating, run `../install.sh` again (or `omarchy theme set "Sea Glass"` if you
installed with `--link`).

## Screenshots

The previews and everything in `screenshots/` are real screenshots, not mockups. To retake
them, set the theme, arrange the desktop, and capture the whole screen with `grim` (a
3024 × 1900 screen at 2× scale, which is what the crop boxes in `screenshots.py` expect):

```bash
mkdir -p ~/captures
grim ~/captures/hero-dark.png                                         # windows open
omarchy theme bg set ~/.local/state/omarchy/current/theme/backgrounds/1-tide-pool.jpg
grim ~/captures/desk-dark-1.png                                       # empty workspace
omarchy menu summon && sleep 1 && grim ~/captures/menu-desk-dark.png  # menu over the wallpaper
```

The script wants, for Tide Pool (`dark`) and Sunlit (`light`):

- `hero-dark`, `hero-light`: a workspace with windows open
- `desk-dark-1` to `desk-dark-3`, `desk-light-1` to `desk-light-3`: an empty workspace on each wallpaper, in order
- `menu-desk-dark`, `menu-desk-light`: the Omarchy menu open over the first wallpaper
- `picker-dark`: the theme picker open (Super + Ctrl + Shift + Space)
- `notify-light`: a notification on screen

Then:

```bash
python3 screenshots.py ~/captures
```
