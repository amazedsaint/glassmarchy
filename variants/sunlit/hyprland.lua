-- Sea Glass · Sunlit · Hyprland look & motion (Omarchy 4, Hyprland 0.55+)
--
-- Frosted glass: rounded pebble corners, kawase blur with a little grain,
-- a glass-tinted drop shadow cast down-right (the sun sits upper-left in
-- the wallpapers), and an animation set tuned like glass settling in water.
--
-- Omarchy only loads this file for themes you install yourself (install.sh,
-- or a copy in ~/.config/omarchy/themes). A theme cloned with
-- `omarchy theme install` keeps its colours but skips any .lua file.

local active_border_color = { colors = { "rgba(3fae8cee)", "rgba(1f9ec0ee)", "rgba(4a78dcee)" }, angle = 45 }
local inactive_border_color = "rgba(b7c3bcaa)"

hl.config({
  general = {
    border_size = 2,
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },

  decoration = {
    -- Squircle corners read as tumbled glass rather than cut panes.
    rounding = 12,
    rounding_power = 3.0,

    shadow = {
      enabled = true,
      range = 26,
      render_power = 3,
      offset = { 6, 10 },
      color = "rgba(1f8fb047)",
      color_inactive = "rgba(2a3a3424)",
    },

    -- A faint lit edge on the focused window, like light caught in a frosted rim.
    glow = {
      enabled = true,
      range = 8,
      render_power = 3,
      color = "rgba(ffffff26)",
      color_inactive = "rgba(00000000)",
    },

    blur = {
      enabled = true,
      size = 8,
      passes = 3,
      noise = 0.03,
      contrast = 0.9,
      brightness = 1.04,
      vibrancy = 0.22,
      vibrancy_darkness = 0.0,
      popups = true,
      popups_ignorealpha = 0.6,
    },
  },

  animations = {
    enabled = true,
  },
})

-- Curves --------------------------------------------------------------------
-- glassOut  expo-out: arrives fast, settles slowly, like a pebble sinking in still water
-- tide      sine in-out: unhurried fades and colour shifts
-- sink      ease-in: things leave quickly and get out of the way
-- pebble    spring with a hint of overshoot for windows dropping into place
-- drift     near-critically damped spring for windows gliding between tiles
hl.curve("glassOut", { type = "bezier", points = { { 0.16, 1 }, { 0.3, 1 } } })
hl.curve("tide", { type = "bezier", points = { { 0.45, 0.05 }, { 0.55, 0.95 } } })
hl.curve("sink", { type = "bezier", points = { { 0.55, 0.06 }, { 0.68, 0.19 } } })
hl.curve("pebble", { type = "spring", mass = 1, stiffness = 324, dampening = 23.4 })
hl.curve("drift", { type = "spring", mass = 1, stiffness = 225, dampening = 27 })

-- Animations ----------------------------------------------------------------
hl.animation({ leaf = "global", enabled = true, speed = 8, bezier = "glassOut" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 4, spring = "pebble", style = "popin 86%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.7, bezier = "sink", style = "popin 92%" })
hl.animation({ leaf = "windowsMove", enabled = true, speed = 4, spring = "drift" })
hl.animation({ leaf = "border", enabled = true, speed = 5, bezier = "glassOut" })
-- When focus lands, the border gradient turns once, a glint travelling round the glass.
-- Change style to "loop" for a slow continuous shimmer (costs a little power).
hl.animation({ leaf = "borderangle", enabled = true, speed = 22, bezier = "tide", style = "once" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 2.4, bezier = "glassOut" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.6, bezier = "sink" })
hl.animation({ leaf = "fadeSwitch", enabled = true, speed = 3.2, bezier = "tide" })
hl.animation({ leaf = "fadeShadow", enabled = true, speed = 3.2, bezier = "tide" })
hl.animation({ leaf = "fadeGlow", enabled = true, speed = 3.2, bezier = "tide" })
hl.animation({ leaf = "fadeDim", enabled = true, speed = 3.2, bezier = "tide" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 3, bezier = "glassOut", style = "popin 94%" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.6, bezier = "sink", style = "fade" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 2.2, bezier = "glassOut" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.5, bezier = "sink" })
hl.animation({ leaf = "fadePopups", enabled = true, speed = 1.8, bezier = "glassOut" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3.4, bezier = "glassOut", style = "slidefade 14%" })
hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 3.4, bezier = "glassOut", style = "slidefadevert 20%" })
hl.animation({ leaf = "zoomFactor", enabled = true, speed = 5, bezier = "glassOut" })

-- Frosted shell -------------------------------------------------------------
-- The theme's shell.toml makes the bar, menus, notifications and OSD translucent;
-- these rules blur what shows through. ignore_alpha keeps the light dimming scrim
-- behind menus clear, so only the cards themselves turn to frosted glass.
hl.layer_rule({ match = { namespace = "^omarchy-bar$" }, blur = true, blur_popups = true, ignore_alpha = 0.2 })
hl.layer_rule({
  match = { namespace = "^(omarchy-menu|omarchy-notifications|omarchy-osd|omarchy-polkit|omarchy-clipboard|omarchy-emojis|omarchy-reminders|omarchy-keyboard-panel)$" },
  blur = true,
  ignore_alpha = 0.5,
})

-- Terminals become panes of frosted glass over the wallpaper.
if o and o.window then
  o.window({ tag = "terminal" }, { opacity = "0.95 0.90" })
end
