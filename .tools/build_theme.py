"""Generate the Sea Glass Omarchy theme files for both variants.

    python3 build_theme.py [repo-dir]      # default: the folder above .tools

Writes the dark theme (Tide Pool) at the repo root and the light theme
(Sunlit) under variants/sunlit/. Images (backgrounds, previews, unlock art)
are produced by the other scripts and copied in separately.
"""
import os
import sys
import textwrap

from palette import SUNLIT as SUNLIT_P, TIDEPOOL as TIDEPOOL_P, mix


def rgb(h):
    h = h.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def strip(h):
    return h.lstrip("#")


# ----------------------------------------------------------------------------- variants

VARIANTS = {
    "tidepool": dict(
        title="Sea Glass",
        mood="Tide Pool",
        slug="sea-glass",
        tagline="Frosted beach glass glowing on wet slate after sundown.",
        P=TIDEPOOL_P,
        grad=["8fd8b8", "5dcfe0", "7ea9f0"],        # seafoam -> turquoise -> cornflower
        inactive_border="2a3f42aa",
        shadow="2fb3c43d",                           # glass-tinted shadow on the focused window
        shadow_inactive="02080a59",
        glow="8fd8b81a",
        blur=dict(size=7, passes=3, noise=0.04, contrast=0.92, brightness=0.92, vibrancy=0.26, vibrancy_darkness=0.18),
        terminal_opacity="0.94 0.88",
        bar_alpha=0.82,
        icons="Yaru-prussiangreen",
    ),
    "sunlit": dict(
        title="Sea Glass",
        mood="Sunlit",
        slug="sea-glass-sunlit",
        tagline="Sea glass drying on white paper in the afternoon sun.",
        P=SUNLIT_P,
        grad=["3fae8c", "1f9ec0", "4a78dc"],
        inactive_border="b7c3bcaa",
        shadow="1f8fb047",                           # turquoise shadow, like light through glass
        shadow_inactive="2a3a3424",
        glow="ffffff26",
        blur=dict(size=8, passes=3, noise=0.03, contrast=0.90, brightness=1.04, vibrancy=0.22, vibrancy_darkness=0.0),
        terminal_opacity="0.95 0.90",
        bar_alpha=0.80,
        icons="Yaru-prussiangreen",
    ),
}


def grad_rgba(v, alpha="ee"):
    return " ".join(f"rgba({c}{alpha})" for c in v["grad"])


# ----------------------------------------------------------------------------- colors.toml

def colors_toml(v):
    P = v["P"]
    order = [
        ("mode", None),
        None,
        ("accent", "seafoam" if P["mode"] == "dark" else "deep turquoise"),
        ("selection", None),
        ("muted", None),
        None,
        ("background", None), ("dark_background", None), ("darker_background", None), ("lighter_background", None),
        None,
        ("foreground", None), ("dark_foreground", None), ("light_foreground", None), ("bright_foreground", None),
        None,
        ("red", "coral, the rare red piece"), ("yellow", "honey amber"), ("orange", "amber"), ("green", "kelly glass"),
        ("cyan", "turquoise"), ("blue", "cobalt"), ("magenta", "lavender / amethyst"), ("brown", "root beer"),
        None,
        ("bright_red", None), ("bright_yellow", None), ("bright_green", "lime / chartreuse"), ("bright_cyan", "aqua"),
        ("bright_blue", "cornflower"), ("bright_magenta", "lavender frost"),
    ]
    lines = [
        f"# {v['title']} · {v['mood']}",
        f"# {v['tagline']}",
        "# Palette sampled from a tray of frosted sea glass in low sun.",
        "",
    ]
    for item in order:
        if item is None:
            lines.append("")
            continue
        key, note = item
        val = P[key]
        lines.append(f'{key} = "{val}"' + (f"  # {note}" if note else ""))
    ansi = ["background", "red", "green", "yellow", "blue", "magenta", "cyan", "foreground",
            "muted", "bright_red", "bright_green", "bright_yellow", "bright_blue", "bright_magenta",
            "bright_cyan", "bright_foreground"]
    lines += [
        "",
        "# Omarchy 3.x reads these legacy names directly; Omarchy 4 derives the same values",
        "# from the keys above, so both versions see one palette.",
        f'cursor = "{P["bright_foreground"]}"',
        f'selection_foreground = "{P["bright_foreground"]}"',
        f'selection_background = "{P["selection"]}"',
    ] + [f'color{i} = "{P[k]}"' for i, k in enumerate(ansi)]
    lines += [
        "",
        "# Window border: light refracting through seafoam, turquoise and cobalt glass.",
        f'hyprland_active_border = "{grad_rgba(v)} 45deg"',
        f'hyprland_inactive_border = "rgba({v["inactive_border"]})"',
        "",
    ]
    return "\n".join(lines)


# ----------------------------------------------------------------------------- shell.toml (Omarchy 4)

def shell_toml(v):
    P = v["P"]
    dark = P["mode"] == "dark"
    g = grad_rgba(v)
    fg, bg, acc = P["foreground"], P["background"], P["accent"]
    lock_border_active = " ".join(f"rgba({c}ff)" for c in (v["grad"][1], v["grad"][0], v["grad"][2])) + " 135deg"
    return textwrap.dedent(f"""\
        # {v['title']} · {v['mood']} · Omarchy shell surfaces
        # Frosted-glass cards: translucent fills (Hyprland blurs them when the theme's
        # hyprland.lua is active), a sea-glass gradient edge, and glass-tinted selection.

        [bar]
        background       = "{bg}"
        background-alpha = {v['bar_alpha']}
        text             = "{fg}"
        active           = "{P['red']}"
        scale-with-font  = true
        size-horizontal  = 26
        size-vertical    = 28

        [hyprland]
        active-border            = "{g} 45deg"
        active-border-foreground = "{g} 45deg"

        [controls]
        normal-color        = "{fg}"
        normal-fill-alpha   = {0.05 if dark else 0.035}
        normal-border       = "{fg}"
        normal-border-width = 1
        normal-border-alpha = {0.22 if dark else 0.26}

        hover-cursor-color        = "{acc}"
        hover-cursor-fill-alpha   = {0.10 if dark else 0.09}
        hover-cursor-border       = "{acc}"
        hover-cursor-border-width = 1
        hover-cursor-border-alpha = 0.45

        focus-color        = "{acc}"
        focus-fill-alpha   = {0.10 if dark else 0.09}
        focus-border       = "{g} 45deg"
        focus-border-width = 1
        focus-border-alpha = 0.85

        selected-color        = "{acc}"
        selected-fill-alpha   = {0.18 if dark else 0.15}
        selected-border       = "{acc}"
        selected-border-width = 0
        selected-border-alpha = 1.0

        pressed-fill-alpha   = 0.26
        selection-fill-alpha = 0.35

        [spacing]
        scale = 1.0
        scale-with-font = true

        [font]
        base-size = 12

        [popups]
        background       = "{bg}"
        background-alpha = {0.90 if dark else 0.88}
        text             = "{fg}"
        border           = "hyprland.active-border"
        border-alpha     = 0.85

        [tooltip]
        background       = "{P['lighter_background']}"
        background-alpha = 0.94
        text             = "{P['light_foreground']}"
        border           = "{acc}"
        border-alpha     = 0.40

        [notifications]
        background       = "{bg}"
        background-alpha = {0.90 if dark else 0.88}
        text             = "{fg}"
        border           = "hyprland.active-border"
        border-alpha     = 0.90
        countdown        = "{acc}"

        [launcher]
        background                = "{bg}"
        background-alpha          = {0.88 if dark else 0.86}
        text                      = "{fg}"
        border                    = "hyprland.active-border"
        border-alpha              = 0.75
        scrim                     = "{P['darker_background'] if dark else P['foreground']}"
        scrim-alpha               = {0.32 if dark else 0.14}
        selected-background       = "{acc}"
        selected-background-alpha = {0.14 if dark else 0.12}
        selected-text             = "{acc}"
        selected-border           = "{acc}"
        selected-border-alpha     = 0.9
        selected-border-width     = "0 0 0 3"

        [menu]
        background                = "{bg}"
        background-alpha          = {0.90 if dark else 0.88}
        text                      = "{fg}"
        border                    = "hyprland.active-border"
        border-alpha              = 0.75
        scrim                     = "{P['darker_background'] if dark else P['foreground']}"
        scrim-alpha               = {0.32 if dark else 0.14}
        selected-background       = "{acc}"
        selected-background-alpha = {0.14 if dark else 0.12}
        selected-text             = "{acc}"
        selected-border           = "{acc}"
        selected-border-alpha     = 0.9
        selected-border-width     = "0 0 0 3"

        [polkit]
        background       = "{bg}"
        background-alpha = 0.94
        text             = "{fg}"
        text-error       = "{P['red']}"
        border           = "hyprland.active-border"
        border-error     = "{P['red']}"
        border-alpha     = 1.0
        scrim            = "{P['darker_background'] if dark else P['foreground']}"
        scrim-alpha      = {0.45 if dark else 0.22}
        accent           = "{acc}"

        [lock]
        background       = "{bg}"
        background-alpha = {0.58 if dark else 0.62}
        text             = "{P['bright_foreground']}"
        placeholder      = "{mix(fg, bg, 0.40)}"
        text-error       = "{P['red']}"
        border           = "hyprland.active-border"
        border-active    = "{lock_border_active}"
        border-error     = "{P['red']}"
        border-alpha     = 1.0
        selection        = "{acc}"
        selection-alpha  = 0.45

        [image-picker]
        scrim                   = "{P['darker_background'] if dark else P['foreground']}"
        scrim-alpha             = {0.55 if dark else 0.30}
        text                    = "{fg}"
        selected-border         = "{acc}"
        selected-border-alpha   = 1.0
        unselected-border       = "{fg}"
        unselected-border-alpha = 0.22
        """)


# ----------------------------------------------------------------------------- hyprland.lua (Omarchy 4)

def hyprland_lua(v):
    P = v["P"]
    b = v["blur"]
    g = ", ".join(f'"rgba({c}ee)"' for c in v["grad"])
    return textwrap.dedent(f"""\
        -- {v['title']} · {v['mood']} · Hyprland look & motion (Omarchy 4, Hyprland 0.55+)
        --
        -- Frosted glass: rounded pebble corners, kawase blur with a little grain,
        -- a glass-tinted drop shadow cast down-right (the sun sits upper-left in
        -- the wallpapers), and an animation set tuned like glass settling in water.
        --
        -- Omarchy only loads this file for themes you install yourself (install.sh,
        -- or a copy in ~/.config/omarchy/themes). A theme cloned with
        -- `omarchy theme install` keeps its colours but skips any .lua file.

        local active_border_color = {{ colors = {{ {g} }}, angle = 45 }}
        local inactive_border_color = "rgba({v['inactive_border']})"

        hl.config({{
          general = {{
            border_size = 2,
            col = {{
              active_border = active_border_color,
              inactive_border = inactive_border_color,
            }},
          }},

          group = {{
            col = {{
              border_active = active_border_color,
              border_inactive = inactive_border_color,
            }},
          }},

          decoration = {{
            -- Squircle corners read as tumbled glass rather than cut panes.
            rounding = 12,
            rounding_power = 3.0,

            shadow = {{
              enabled = true,
              range = 26,
              render_power = 3,
              offset = {{ 6, 10 }},
              color = "rgba({v['shadow']})",
              color_inactive = "rgba({v['shadow_inactive']})",
            }},

            -- A faint lit edge on the focused window, like light caught in a frosted rim.
            glow = {{
              enabled = true,
              range = 8,
              render_power = 3,
              color = "rgba({v['glow']})",
              color_inactive = "rgba(00000000)",
            }},

            blur = {{
              enabled = true,
              size = {b['size']},
              passes = {b['passes']},
              noise = {b['noise']},
              contrast = {b['contrast']},
              brightness = {b['brightness']},
              vibrancy = {b['vibrancy']},
              vibrancy_darkness = {b['vibrancy_darkness']},
              popups = true,
              popups_ignorealpha = 0.6,
            }},
          }},

          animations = {{
            enabled = true,
          }},
        }})

        -- Curves --------------------------------------------------------------------
        -- glassOut  expo-out: arrives fast, settles slowly, like a pebble sinking in still water
        -- tide      sine in-out: unhurried fades and colour shifts
        -- sink      ease-in: things leave quickly and get out of the way
        -- pebble    spring with a hint of overshoot for windows dropping into place
        -- drift     near-critically damped spring for windows gliding between tiles
        hl.curve("glassOut", {{ type = "bezier", points = {{ {{ 0.16, 1 }}, {{ 0.3, 1 }} }} }})
        hl.curve("tide", {{ type = "bezier", points = {{ {{ 0.45, 0.05 }}, {{ 0.55, 0.95 }} }} }})
        hl.curve("sink", {{ type = "bezier", points = {{ {{ 0.55, 0.06 }}, {{ 0.68, 0.19 }} }} }})
        hl.curve("pebble", {{ type = "spring", mass = 1, stiffness = 324, dampening = 23.4 }})
        hl.curve("drift", {{ type = "spring", mass = 1, stiffness = 225, dampening = 27 }})

        -- Animations ----------------------------------------------------------------
        hl.animation({{ leaf = "global", enabled = true, speed = 8, bezier = "glassOut" }})
        hl.animation({{ leaf = "windowsIn", enabled = true, speed = 4, spring = "pebble", style = "popin 86%" }})
        hl.animation({{ leaf = "windowsOut", enabled = true, speed = 1.7, bezier = "sink", style = "popin 92%" }})
        hl.animation({{ leaf = "windowsMove", enabled = true, speed = 4, spring = "drift" }})
        hl.animation({{ leaf = "border", enabled = true, speed = 5, bezier = "glassOut" }})
        -- When focus lands, the border gradient turns once, a glint travelling round the glass.
        -- Change style to "loop" for a slow continuous shimmer (costs a little power).
        hl.animation({{ leaf = "borderangle", enabled = true, speed = 22, bezier = "tide", style = "once" }})
        hl.animation({{ leaf = "fadeIn", enabled = true, speed = 2.4, bezier = "glassOut" }})
        hl.animation({{ leaf = "fadeOut", enabled = true, speed = 1.6, bezier = "sink" }})
        hl.animation({{ leaf = "fadeSwitch", enabled = true, speed = 3.2, bezier = "tide" }})
        hl.animation({{ leaf = "fadeShadow", enabled = true, speed = 3.2, bezier = "tide" }})
        hl.animation({{ leaf = "fadeGlow", enabled = true, speed = 3.2, bezier = "tide" }})
        hl.animation({{ leaf = "fadeDim", enabled = true, speed = 3.2, bezier = "tide" }})
        hl.animation({{ leaf = "layersIn", enabled = true, speed = 3, bezier = "glassOut", style = "popin 94%" }})
        hl.animation({{ leaf = "layersOut", enabled = true, speed = 1.6, bezier = "sink", style = "fade" }})
        hl.animation({{ leaf = "fadeLayersIn", enabled = true, speed = 2.2, bezier = "glassOut" }})
        hl.animation({{ leaf = "fadeLayersOut", enabled = true, speed = 1.5, bezier = "sink" }})
        hl.animation({{ leaf = "fadePopups", enabled = true, speed = 1.8, bezier = "glassOut" }})
        hl.animation({{ leaf = "workspaces", enabled = true, speed = 3.4, bezier = "glassOut", style = "slidefade 14%" }})
        hl.animation({{ leaf = "specialWorkspace", enabled = true, speed = 3.4, bezier = "glassOut", style = "slidefadevert 20%" }})
        hl.animation({{ leaf = "zoomFactor", enabled = true, speed = 5, bezier = "glassOut" }})

        -- Frosted shell -------------------------------------------------------------
        -- The theme's shell.toml makes the bar, menus, notifications and OSD translucent;
        -- these rules blur what shows through. ignore_alpha keeps the light dimming scrim
        -- behind menus clear, so only the cards themselves turn to frosted glass.
        hl.layer_rule({{ match = {{ namespace = "^omarchy-bar$" }}, blur = true, blur_popups = true, ignore_alpha = 0.2 }})
        hl.layer_rule({{
          match = {{ namespace = "^(omarchy-menu|omarchy-notifications|omarchy-osd|omarchy-polkit|omarchy-clipboard|omarchy-emojis|omarchy-reminders|omarchy-keyboard-panel)$" }},
          blur = true,
          ignore_alpha = 0.5,
        }})

        -- Terminals become panes of frosted glass over the wallpaper.
        if o and o.window then
          o.window({{ tag = "terminal" }}, {{ opacity = "{v['terminal_opacity']}" }})
        end
        """)


# ----------------------------------------------------------------------------- hyprland.conf (Omarchy 3.x)

def hyprland_conf(v):
    b = v["blur"]
    g = " ".join(f"rgba({c}ee)" for c in v["grad"])
    return textwrap.dedent(f"""\
        # {v['title']} · {v['mood']} · Hyprland look & motion for Omarchy 3.x (Hyprland 0.53/0.54)
        # Omarchy 4 reads hyprland.lua instead; this file is ignored there.

        $activeBorderColor = {g} 45deg
        $inactiveBorderColor = rgba({v['inactive_border']})

        general {{
            border_size = 2
            col.active_border = $activeBorderColor
            col.inactive_border = $inactiveBorderColor
        }}

        group {{
            col.border_active = $activeBorderColor
            col.border_inactive = $inactiveBorderColor
        }}

        decoration {{
            rounding = 12
            rounding_power = 3.0

            shadow {{
                enabled = true
                range = 26
                render_power = 3
                offset = 6 10
                color = rgba({v['shadow']})
                color_inactive = rgba({v['shadow_inactive']})
            }}

            blur {{
                enabled = true
                size = {b['size']}
                passes = {b['passes']}
                noise = {b['noise']}
                contrast = {b['contrast']}
                brightness = {b['brightness']}
                vibrancy = {b['vibrancy']}
                vibrancy_darkness = {b['vibrancy_darkness']}
                popups = true
            }}
        }}

        animations {{
            enabled = true

            bezier = glassOut, 0.16, 1, 0.3, 1
            bezier = tide, 0.45, 0.05, 0.55, 0.95
            bezier = sink, 0.55, 0.06, 0.68, 0.19
            bezier = pebble, 0.22, 1.16, 0.36, 1

            animation = global, 1, 8, glassOut
            animation = windowsIn, 1, 4, pebble, popin 86%
            animation = windowsOut, 1, 1.7, sink, popin 92%
            animation = windowsMove, 1, 4, glassOut
            animation = border, 1, 5, glassOut
            animation = borderangle, 1, 22, tide, once
            animation = fadeIn, 1, 2.4, glassOut
            animation = fadeOut, 1, 1.6, sink
            animation = fadeSwitch, 1, 3.2, tide
            animation = fadeShadow, 1, 3.2, tide
            animation = fadeDim, 1, 3.2, tide
            animation = layersIn, 1, 3, glassOut, popin 94%
            animation = layersOut, 1, 1.6, sink, fade
            animation = fadeLayersIn, 1, 2.2, glassOut
            animation = fadeLayersOut, 1, 1.5, sink
            animation = workspaces, 1, 3.4, glassOut, slidefade 14%
            animation = specialWorkspace, 1, 3.4, glassOut, slidefadevert 20%
        }}

        # Frosted Waybar, launcher and notifications
        layerrule = blur on, match:namespace waybar
        layerrule = ignore_alpha 0.2, match:namespace waybar
        layerrule = blur on, match:namespace walker
        layerrule = ignore_alpha 0.5, match:namespace walker
        layerrule = blur on, match:namespace notifications
        layerrule = ignore_alpha 0.5, match:namespace notifications

        # Terminals become panes of frosted glass
        windowrule = opacity {v['terminal_opacity']}, match:tag terminal
        """)


def hyprlock_conf(v):
    P = v["P"]
    g = " ".join(f"rgba({c}ff)" for c in v["grad"])
    return textwrap.dedent(f"""\
        # {v['title']} · {v['mood']} · hyprlock colours (Omarchy 3.x)
        $color = rgba({rgb(P['background'])}, 1.0)
        $inner_color = rgba({rgb(P['background'])}, 0.72)
        $outer_color = {g} 45deg
        $font_color = rgba({rgb(P['bright_foreground'])}, 1.0)
        $check_color = rgba({rgb(P['accent'])}, 1.0)
        """)


def waybar_css(v):
    P = v["P"]
    dark = P["mode"] == "dark"
    return textwrap.dedent(f"""\
        /* {v['title']} · {v['mood']} · Waybar (Omarchy 3.x) */
        @define-color foreground {P['foreground']};
        @define-color background {P['background']};
        @define-color seaglass {P['accent']};
        @define-color seaglass-alert {P['red']};

        /* Frosted bar: translucent fill, Hyprland blurs what shows through. */
        window#waybar {{
          background-color: alpha(@background, {v['bar_alpha']});
          transition: background-color 400ms ease-out;
        }}

        window#waybar .modules-left,
        window#waybar .modules-center,
        window#waybar .modules-right,
        window#waybar .modules-left *,
        window#waybar .modules-center *,
        window#waybar .modules-right * {{
          background-color: transparent;
        }}

        window#waybar #workspaces button {{
          border-radius: 7px;
          transition: color 320ms cubic-bezier(0.16, 1, 0.3, 1),
                      background-color 320ms cubic-bezier(0.16, 1, 0.3, 1),
                      box-shadow 320ms cubic-bezier(0.16, 1, 0.3, 1);
        }}

        window#waybar #workspaces button:hover {{
          background-color: alpha(@seaglass, {0.12 if dark else 0.10});
        }}

        window#waybar #workspaces button.active {{
          color: @seaglass;
          box-shadow: inset 0 -2px alpha(@seaglass, 0.95);
        }}

        window#waybar #clock,
        window#waybar #cpu,
        window#waybar #battery,
        window#waybar #pulseaudio,
        window#waybar #network,
        window#waybar #bluetooth {{
          transition: color 400ms ease-out;
        }}

        window#waybar #clock:hover,
        window#waybar #cpu:hover,
        window#waybar #battery:hover,
        window#waybar #pulseaudio:hover,
        window#waybar #network:hover,
        window#waybar #bluetooth:hover {{
          color: @seaglass;
        }}

        @keyframes seaglass-pulse {{
          from {{ opacity: 1; }}
          to {{ opacity: 0.45; }}
        }}

        window#waybar #custom-screenrecording-indicator.active,
        window#waybar #custom-voxtype.recording {{
          color: @seaglass-alert;
          animation: seaglass-pulse 1.4s ease-in-out infinite alternate;
        }}

        window#waybar #custom-idle-indicator.active,
        window#waybar #custom-notification-silencing-indicator.active {{
          color: @seaglass-alert;
        }}

        tooltip {{
          border-radius: 10px;
          border: 1px solid alpha(@seaglass, 0.45);
        }}
        """)


def walker_css(v):
    P = v["P"]
    dark = P["mode"] == "dark"
    return textwrap.dedent(f"""\
        /* {v['title']} · {v['mood']} · Walker launcher (Omarchy 3.x) */
        @define-color selected-text {P['accent']};
        @define-color text {P['foreground']};
        @define-color base {P['background']};
        @define-color border {P['accent']};
        @define-color foreground {P['foreground']};
        @define-color background {P['background']};

        window .box-wrapper {{
          background: alpha(@base, {0.88 if dark else 0.86});
          border: 1px solid alpha(@border, 0.55);
          border-radius: 14px;
        }}

        window .search-container {{
          background: transparent;
        }}

        window .list child {{
          border-radius: 9px;
          transition: background-color 180ms cubic-bezier(0.16, 1, 0.3, 1);
        }}

        window .list child:selected {{
          background: alpha(@selected-text, {0.14 if dark else 0.12});
        }}
        """)


def swayosd_css(v):
    P = v["P"]
    return textwrap.dedent(f"""\
        /* {v['title']} · {v['mood']} · SwayOSD (Omarchy 3.x) */
        @define-color background-color {P['background']};
        @define-color border-color {P['accent']};
        @define-color label {P['foreground']};
        @define-color image {P['foreground']};
        @define-color progress {P['accent']};
        """)


def mako_ini(v):
    P = v["P"]
    return textwrap.dedent(f"""\
        # {v['title']} · {v['mood']} · mako notifications (Omarchy 3.x)
        include=~/.local/share/omarchy/default/mako/core.ini

        text-color={P['foreground']}
        border-color={P['accent']}
        background-color={P['background']}e6
        progress-color=over {P['selection']}
        border-radius=12
        """)


# ----------------------------------------------------------------------------- btop

def btop_theme(v):
    P = v["P"]
    dark = P["mode"] == "dark"
    bg = P["background"]
    box = (lambda c: mix(c, bg, 0.40)) if dark else (lambda c: mix(c, bg, 0.35))
    rows = [
        ("main_bg", ""), ("main_fg", P["foreground"]), ("title", P["light_foreground"]), ("hi_fg", P["accent"]),
        ("selected_bg", P["selection"]), ("selected_fg", P["bright_foreground"]), ("inactive_fg", P["muted"]),
        ("graph_text", P["dark_foreground"]), ("meter_bg", P["selection"]), ("proc_misc", P["dark_foreground"]),
        ("cpu_box", box(P["accent"])), ("mem_box", box(P["cyan"])), ("net_box", box(P["blue"])),
        ("proc_box", box(P["magenta"])), ("div_line", P["selection"] if dark else P["darker_background"]),
        ("temp_start", P["accent"] if dark else P["green"]), ("temp_mid", P["yellow"]), ("temp_end", P["red"]),
        ("cpu_start", P["accent"] if dark else P["green"]), ("cpu_mid", P["cyan"]), ("cpu_end", P["blue"]),
        ("free_start", P["blue"]), ("free_mid", P["cyan"]), ("free_end", P["accent"] if dark else P["green"]),
        ("cached_start", P["magenta"]), ("cached_mid", P["blue"]), ("cached_end", P["cyan"]),
        ("available_start", P["bright_green"]), ("available_mid", P["yellow"]), ("available_end", P["orange"]),
        ("used_start", P["accent"] if dark else P["green"]), ("used_mid", P["cyan"]), ("used_end", P["blue"]),
        ("download_start", P["bright_blue"] if dark else P["blue"]), ("download_mid", P["cyan"]), ("download_end", P["accent"]),
        ("upload_start", P["yellow"]), ("upload_mid", P["orange"]), ("upload_end", P["red"]),
        ("process_start", P["accent"] if dark else P["green"]), ("process_mid", P["cyan"]), ("process_end", P["blue"]),
    ]
    ramp = [P["background"], P["lighter_background"], P["selection"], P["muted"], P["dark_foreground"],
            P["foreground"], P["light_foreground"], P["bright_foreground"]]
    out = [f"# {v['title']} · {v['mood']} · btop", "# Transparent background so frosted terminals show through.",
           'theme_background=false', ""]
    for k, val in rows:
        out.append(f'theme[{k}]="{val}"')
    out.append("")
    for i, c in enumerate(ramp):
        out.append(f'theme[gradient_color_{i}]="{c}"')
    return "\n".join(out) + "\n"


# ----------------------------------------------------------------------------- write

def write_variant(root, key):
    v = VARIANTS[key]
    os.makedirs(root, exist_ok=True)
    files = {
        "colors.toml": colors_toml(v),
        "shell.toml": shell_toml(v),
        "hyprland.lua": hyprland_lua(v),
        "hyprland.conf": hyprland_conf(v),
        "hyprlock.conf": hyprlock_conf(v),
        "waybar.css": waybar_css(v),
        "walker.css": walker_css(v),
        "swayosd.css": swayosd_css(v),
        "mako.ini": mako_ini(v),
        "btop.theme": btop_theme(v),
        "chromium.theme": rgb(v["P"]["background"]) + "\n",
        "icons.theme": v["icons"] + "\n",
    }
    if v["P"]["mode"] == "light":
        files["light.mode"] = ""
    for name, content in files.items():
        with open(os.path.join(root, name), "w") as fh:
            fh.write(content)
    return sorted(files)


if __name__ == "__main__":
    dist = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("tidepool:", write_variant(dist, "tidepool"))
    print("sunlit:  ", write_variant(os.path.join(dist, "variants", "sunlit"), "sunlit"))
