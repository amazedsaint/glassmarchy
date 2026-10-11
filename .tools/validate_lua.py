"""Validate a theme hyprland.lua against Hyprland's own option tables.

Runs the file in a real Lua interpreter with a mock `hl` / `o` API whose
checks are derived from the Hyprland source tree (ConfigValues.cpp, the
animation tree, styleValidInConfigVar, window/layer rule descriptors).

    python3 validate_lua.py <hyprland-src> <file.lua> [...]
"""
import re
import sys

from lupa import LuaRuntime


def load_options(src):
    text = open(f"{src}/src/config/values/ConfigValues.cpp").read()
    opts = {}
    for m in re.finditer(r'MS<(\w+)>\("([^"]+)"\s*,\s*"(?:[^"\\]|\\.)*"\s*(?:,\s*([^,{)]+))?(?:,\s*\{([^}]*)\})?', text):
        typ, path, default, extra = m.group(1), m.group(2), m.group(3), m.group(4) or ""
        lo = re.search(r"\.min\s*=\s*(-?[\d.]+)", extra)
        hi = re.search(r"\.max\s*=\s*(-?[\d.]+)", extra)
        opts[path] = (typ, float(lo.group(1)) if lo else None, float(hi.group(1)) if hi else None)
    return opts


def load_anim_leaves(src):
    text = open(f"{src}/src/config/shared/animation/AnimationTree.cpp").read()
    return set(re.findall(r'createNode\("([^"]+)"', text))


def load_rule_fields(src):
    hpp = open(f"{src}/src/config/lua/bindings/LuaBindingsInternal.hpp").read()
    win = set(re.findall(r'\{"([a-z_]+)",\s*\[\]\(\)', hpp))
    cpp = open(f"{src}/src/config/lua/bindings/LuaBindingsConfigRules.cpp").read()
    seg = cpp[cpp.index("LAYER_RULE_EFFECT_DESCS[]"):]
    seg = seg[:seg.index("};")]
    layer = set(re.findall(r'\{"([a-z_]+)"', seg))
    return win, layer


COLOR_RE = re.compile(r"^(rgba?\([0-9a-fA-F]{6,8}\)|rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(,\s*[\d.]+\s*)?\)|0x[0-9a-fA-F]{8}|#[0-9a-fA-F]{6,8})$")


def style_ok(leaf, style):
    if leaf.startswith("window"):
        return style.startswith("slide") or style in ("gnome", "gnomed") or style.startswith("popin")
    if leaf.startswith("workspaces") or leaf.startswith("specialWorkspace"):
        if style in ("slide", "slidevert", "fade"):
            return True
        if style.startswith("slide"):
            if "%" in style:
                int(style[style.rfind(" ") + 1:-1])
            return True
        return False
    if leaf == "borderangle":
        return style in ("loop", "once")
    if leaf.startswith("layers"):
        return True
    return False


def main():
    src = sys.argv[1]
    opts = load_options(src)
    leaves = load_anim_leaves(src)
    win_fields, layer_fields = load_rule_fields(src)
    print(f"loaded {len(opts)} options, {len(leaves)} animation leaves, {len(win_fields)} window-rule and {len(layer_fields)} layer-rule fields")
    ok_all = True
    for path in sys.argv[2:]:
        errors, notes = [], []
        curves = {"default": "bezier"}
        springs = {"default"}
        lua = LuaRuntime(unpack_returned_tuples=True)
        g = lua.globals()

        def lua_table_to_py(t):
            if lua.eval("type")(t) != "table":
                return t
            keys = list(t.keys())
            if keys and all(isinstance(k, int) for k in keys):
                return [lua_table_to_py(t[k]) for k in sorted(keys)]
            return {k: lua_table_to_py(t[k]) for k in keys}

        def check_value(key, val):
            typ, lo, hi = opts[key]
            if typ in ("Int", "Float"):
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    errors.append(f"{key}: expected number, got {val!r}")
                    return
                if lo is not None and val < lo or hi is not None and val > hi:
                    errors.append(f"{key}: {val} outside [{lo}, {hi}]")
            elif typ == "Bool":
                if not isinstance(val, bool):
                    errors.append(f"{key}: expected boolean, got {val!r}")
            elif typ == "Color":
                if not (isinstance(val, str) and COLOR_RE.match(val)):
                    errors.append(f"{key}: bad colour {val!r}")
            elif typ == "Vec2":
                good = isinstance(val, list) and len(val) == 2 and all(isinstance(x, (int, float)) for x in val)
                good = good or (isinstance(val, str) and len(val.replace(",", " ").split()) == 2)
                if not good:
                    errors.append(f"{key}: bad vec2 {val!r}")
            elif typ == "FontWeight":
                if not isinstance(val, (str, int)):
                    errors.append(f"{key}: bad font weight {val!r}")
            elif typ == "Gradient":
                if isinstance(val, str):
                    if not COLOR_RE.match(val):
                        errors.append(f"{key}: bad colour {val!r}")
                elif isinstance(val, dict):
                    for c in val.get("colors", []):
                        if not COLOR_RE.match(c):
                            errors.append(f"{key}: bad gradient stop {c!r}")
                    if not val.get("colors"):
                        errors.append(f"{key}: gradient without colors")
                else:
                    errors.append(f"{key}: bad gradient {val!r}")
            notes.append(f"{key} = {val!r}")

        def walk(prefix, node):
            for k, val in node.items():
                if prefix.endswith(":col"):
                    key = f"{prefix[:-4]}:col.{k}"
                else:
                    key = f"{prefix}:{k}" if prefix else k
                if key in opts:
                    check_value(key, val)
                elif isinstance(val, dict):
                    walk(key, val)
                else:
                    errors.append(f"unknown option {key}")

        def hl_config(t):
            walk("", lua_table_to_py(t))

        def hl_curve(name, t):
            t = lua_table_to_py(t)
            if t.get("type") == "bezier":
                pts = t.get("points")
                if not (isinstance(pts, list) and len(pts) == 2 and all(len(p) == 2 for p in pts)):
                    errors.append(f"curve {name}: bad points")
                elif not all(-1 <= c <= 2 for p in pts for c in p):
                    errors.append(f"curve {name}: point outside [-1, 2]")
                curves[name] = "bezier"
            elif t.get("type") == "spring":
                for f in ("stiffness", "mass"):
                    if not isinstance(t.get(f), (int, float)) or t[f] <= 0.5:
                        errors.append(f"spring {name}: {f} must be a number > 0.5")
                damp = t.get("dampening", t.get("damping"))
                if "dampening" not in t:
                    errors.append(f"spring {name}: 0.55 only reads 'dampening'")
                if not isinstance(damp, (int, float)) or damp <= 0.5:
                    errors.append(f"spring {name}: damping must be > 0.5")
                springs.add(name)
                k, c, m = t["stiffness"], damp, t["mass"]
                zeta = c / (2 * (k * m) ** 0.5)
                notes.append(f"spring {name}: zeta={zeta:.2f} omega0={(k / m) ** 0.5:.1f}")
            else:
                errors.append(f"curve {name}: unknown type {t.get('type')}")

        def hl_animation(t):
            t = lua_table_to_py(t)
            leaf = t.get("leaf")
            if leaf not in leaves:
                errors.append(f"animation: no such leaf {leaf!r}")
                return
            if t.get("enabled", True) is False:
                return
            sp = t.get("speed")
            if not isinstance(sp, (int, float)) or not (0 < sp <= 100):
                errors.append(f"animation {leaf}: speed {sp!r}")
            if "bezier" in t:
                if t["bezier"] not in curves:
                    errors.append(f"animation {leaf}: no such bezier {t['bezier']!r}")
            elif "spring" in t:
                if t["spring"] not in springs:
                    errors.append(f"animation {leaf}: no such spring {t['spring']!r}")
            else:
                errors.append(f"animation {leaf}: bezier or spring required")
            if "style" in t and not style_ok(leaf, t["style"]):
                errors.append(f"animation {leaf}: invalid style {t['style']!r}")

        def hl_layer_rule(t):
            t = lua_table_to_py(t)
            for k, val in t.items():
                if k in ("match", "name", "enabled"):
                    continue
                if k not in layer_fields:
                    errors.append(f"layer_rule: unknown field {k}")
                if k == "ignore_alpha" and not (0 <= val <= 1):
                    errors.append("layer_rule: ignore_alpha out of range")
            if "namespace" not in t.get("match", {}):
                errors.append("layer_rule without namespace match")
            else:
                re.compile(t["match"]["namespace"])

        def hl_window_rule(t):
            t = lua_table_to_py(t)
            for k in t:
                if k in ("match", "name", "enabled"):
                    continue
                if k not in win_fields:
                    errors.append(f"window_rule: unknown field {k}")
            if "opacity" in t:
                parts = str(t["opacity"]).split()
                if not (1 <= len(parts) <= 3 and all(0 <= float(p) <= 1 for p in parts)):
                    errors.append(f"window_rule: bad opacity {t['opacity']!r}")

        hl = lua.table()
        hl["config"] = hl_config
        hl["curve"] = hl_curve
        hl["animation"] = hl_animation
        hl["layer_rule"] = hl_layer_rule
        hl["window_rule"] = hl_window_rule
        g["hl"] = hl
        # Omarchy's o.window helper, verbatim semantics
        lua.execute("""
            o = o or {}
            function o.window(match, rules)
              rules.match = rules.match or {}
              if type(match) == "string" then rules.match.class = match
              else for key, value in pairs(match) do rules.match[key] = value end end
              hl.window_rule(rules)
            end
        """)
        try:
            lua.execute(open(path).read())
        except Exception as e:  # syntax or runtime error
            errors.append(f"Lua error: {e}")
        status = "OK" if not errors else "FAIL"
        print(f"\n[{status}] {path}")
        for n in notes:
            if n.startswith("spring"):
                print("   ", n)
        for e in errors:
            print("   !!", e)
        ok_all &= not errors
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
