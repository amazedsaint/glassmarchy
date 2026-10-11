#!/usr/bin/env bash
#
# Sea Glass for Omarchy — local installer
#
# Installs both moods as your own themes in ~/.config/omarchy/themes:
#   sea-glass          Tide Pool (dark)   — this folder
#   sea-glass-sunlit   Sunlit (light)     — variants/sunlit
#
# Omarchy applies everything in a theme you installed yourself, including
# hyprland.lua (frosted blur, rounded corners, animations). A theme cloned with
# `omarchy theme install <url>` keeps only its colours, so use this script for
# the full effect. Read hyprland.lua first if you like — it is plain Hyprland
# config.
#
# Usage: ./install.sh [--set dark|light|none] [--link]
#   --set   theme to switch to afterwards (default: dark)
#   --link  symlink to this checkout instead of copying (edits apply on next
#           `omarchy theme set`)

set -euo pipefail

SET="dark"
LINK=0
while (($#)); do
  case "$1" in
  --set)
    if (($# < 2)); then
      echo "--set expects dark, light or none" >&2
      exit 1
    fi
    SET="$2"
    shift 2
    ;;
  --link)
    LINK=1
    shift
    ;;
  -h | --help)
    awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"
    exit 0
    ;;
  *)
    echo "Unknown option: $1 (try --help)" >&2
    exit 1
    ;;
  esac
done

case "$SET" in dark | light | none) ;; *)
  echo "--set expects dark, light or none" >&2
  exit 1
  ;;
esac

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEMES="${HOME:?}/.config/omarchy/themes"
mkdir -p "$THEMES"

# Files that belong to the repo, not to a theme.
is_repo_only() {
  case "$1" in
  variants | screenshots | install.sh | README* | LICENSE* | *.md) return 0 ;;
  *) return 1 ;;
  esac
}

install_theme() {
  local name="$1" src="$2" dest="$THEMES/$1" entry base

  if [[ -L $dest || -e $dest ]]; then
    rm -rf -- "$dest"
  fi

  if ((LINK)); then
    ln -s -- "$src" "$dest"
  else
    mkdir -p -- "$dest"
    for entry in "$src"/*; do
      base="${entry##*/}"
      is_repo_only "$base" && continue
      cp -R -- "$entry" "$dest/"
    done
  fi

  echo "  ✓ $name  →  $dest"
}

echo "Installing Sea Glass themes"
install_theme "sea-glass" "$REPO"
install_theme "sea-glass-sunlit" "$REPO/variants/sunlit"

target=""
case "$SET" in
dark) target="sea-glass" ;;
light) target="sea-glass-sunlit" ;;
esac

if [[ -n $target ]]; then
  if command -v omarchy-theme-set >/dev/null 2>&1; then
    echo "Switching to $target"
    omarchy-theme-set "$target"
  else
    echo "omarchy-theme-set not found — pick the theme from Style > Theme in the Omarchy menu."
  fi
fi

cat <<'EOF'

Done. Switch any time with Super + Ctrl + Shift + Space (or `omarchy theme set "Sea Glass"`).
The unlock art is under Style > Unlock; pick a wallpaper with Super + Ctrl + Space.
EOF
