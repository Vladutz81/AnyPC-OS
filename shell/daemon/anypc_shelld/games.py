"""Discover installed games: desktop entries (native + Flatpak) and Steam."""

import configparser
import hashlib
import os
import re
import shlex

FIELD_CODE = re.compile(r"%[fFuUdDnNickvm]")
STEAM_SKIP = re.compile(r"(proton|steam linux runtime|steamworks common|steamvr)", re.I)
ART_EXT = (".png", ".jpg", ".jpeg", ".webp", ".svg")


def _home():
    return os.path.expanduser("~")


def default_desktop_dirs():
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.join(_home(), ".local", "share")
    dirs = [os.path.join(data_home, "applications")]
    for d in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":"):
        if d:
            dirs.append(os.path.join(d, "applications"))
    dirs += [
        "/var/lib/flatpak/exports/share/applications",
        os.path.join(data_home, "flatpak", "exports", "share", "applications"),
    ]
    seen, out = set(), []
    for d in dirs:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def default_steam_roots():
    h = _home()
    return [
        os.path.join(h, ".local", "share", "Steam"),
        os.path.join(h, ".steam", "steam"),
        os.path.join(h, ".var", "app", "com.valvesoftware.Steam", ".local", "share", "Steam"),
    ]


def game_id(source, key):
    return hashlib.sha1(f"{source}:{key}".encode()).hexdigest()[:12]


def hue_for(name):
    return int(hashlib.md5(name.encode()).hexdigest()[:4], 16) % 360


# -- desktop entries ---------------------------------------------------------

def parse_desktop_file(path):
    cp = configparser.RawConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            cp.read_file(f)
    except (OSError, configparser.Error):
        return None
    if not cp.has_section("Desktop Entry"):
        return None
    e = cp["Desktop Entry"]
    if e.get("Type", "Application") != "Application":
        return None
    if e.get("NoDisplay", "false").lower() == "true" or e.get("Hidden", "false").lower() == "true":
        return None
    cats = [c for c in e.get("Categories", "").split(";") if c]
    if "Game" not in cats:
        return None
    exec_line = e.get("Exec", "").strip()
    name = e.get("Name", "").strip()
    if not exec_line or not name:
        return None
    try:
        argv = [a for a in (FIELD_CODE.sub("", t) for t in shlex.split(exec_line)) if a]
    except ValueError:
        return None
    if not argv:
        return None
    genre = next((c for c in cats if c not in ("Game", "Application")), "Game")
    is_flatpak = "/flatpak/" in path or argv[0].endswith("flatpak")
    return {
        "name": name,
        "genre": _pretty_genre(genre),
        "argv": argv,
        "icon": e.get("Icon", "").strip(),
        "source": "flatpak" if is_flatpak else "native",
        "key": os.path.basename(path),
    }


def _pretty_genre(cat):
    names = {
        "ActionGame": "Action", "AdventureGame": "Adventure", "ArcadeGame": "Arcade",
        "BoardGame": "Board", "BlocksGame": "Puzzle", "CardGame": "Cards", "KidsGame": "Kids",
        "LogicGame": "Logic", "RolePlaying": "RPG", "Shooter": "Shooter", "Simulation": "Simulation",
        "SportsGame": "Sports", "StrategyGame": "Strategy",
    }
    return names.get(cat, re.sub(r"(?<!^)(?=[A-Z])", " ", cat).replace(" Game", ""))


def resolve_icon(icon):
    if not icon:
        return None
    if os.path.isabs(icon):
        return icon if os.path.isfile(icon) else None
    candidates = []
    for base in ("/usr/share/icons/hicolor", os.path.join(_home(), ".local/share/icons/hicolor"),
                 "/var/lib/flatpak/exports/share/icons/hicolor"):
        for size in ("512x512", "256x256", "scalable", "128x128"):
            for ext in (".png", ".svg"):
                candidates.append(os.path.join(base, size, "apps", icon + ext))
    candidates += [os.path.join("/usr/share/pixmaps", icon + ext) for ext in (".png", ".svg", ".xpm")]
    return next((c for c in candidates if os.path.isfile(c)), None)


def scan_desktop(dirs=None):
    found = {}
    for d in dirs or default_desktop_dirs():
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for n in names:
            if not n.endswith(".desktop") or n in found:
                continue  # earlier dirs (user) override later ones (system)
            entry = parse_desktop_file(os.path.join(d, n))
            if entry:
                found[n] = entry
    games = []
    for entry in found.values():
        gid = game_id(entry["source"], entry["key"])
        games.append({
            "id": gid,
            "name": entry["name"],
            "genre": entry["genre"],
            "source": entry["source"],
            "launch": {"argv": entry["argv"]},
            "art": resolve_icon(entry["icon"]),
            "hue": hue_for(entry["name"]),
        })
    return games


# -- Steam ---------------------------------------------------------------------

_VDF_TOKEN = re.compile(r'"((?:[^"\\]|\\.)*)"|([{}])')


def parse_vdf(text):
    """Parse Valve's KeyValues text format into nested dicts."""
    tokens = [(m.group(1), m.group(2)) for m in _VDF_TOKEN.finditer(text)]
    pos = 0

    def parse_obj():
        nonlocal pos
        obj = {}
        while pos < len(tokens):
            s, brace = tokens[pos]
            if brace == "}":
                pos += 1
                return obj
            pos += 1
            if pos >= len(tokens):
                break
            vs, vb = tokens[pos]
            pos += 1
            if vb == "{":
                obj[s] = parse_obj()
            elif vs is not None:
                obj[s] = vs
        return obj

    return parse_obj()


def _steam_library_dirs(root):
    libs = [os.path.join(root, "steamapps")]
    vdf = os.path.join(root, "steamapps", "libraryfolders.vdf")
    try:
        with open(vdf, "r", encoding="utf-8", errors="replace") as f:
            data = parse_vdf(f.read())
        folders = data.get("libraryfolders", {})
        for v in folders.values():
            p = v.get("path") if isinstance(v, dict) else v
            if isinstance(p, str):
                libs.append(os.path.join(p, "steamapps"))
    except OSError:
        pass
    return libs


def scan_steam(roots=None):
    games, seen = [], set()
    for root in roots or default_steam_roots():
        if not os.path.isdir(root):
            continue
        cache = os.path.join(root, "appcache", "librarycache")
        for lib in _steam_library_dirs(root):
            try:
                names = os.listdir(lib)
            except OSError:
                continue
            for n in names:
                if not (n.startswith("appmanifest_") and n.endswith(".acf")):
                    continue
                try:
                    with open(os.path.join(lib, n), "r", encoding="utf-8", errors="replace") as f:
                        st = parse_vdf(f.read()).get("AppState", {})
                except OSError:
                    continue
                appid, name = st.get("appid", ""), st.get("name", "")
                if not appid.isdigit() or not name or appid in seen or STEAM_SKIP.search(name):
                    continue
                seen.add(appid)
                art = None
                for cand in (f"{appid}_library_600x900.jpg", f"{appid}_header.jpg",
                             os.path.join(appid, "library_600x900.jpg")):
                    p = os.path.join(cache, cand)
                    if os.path.isfile(p):
                        art = p
                        break
                games.append({
                    "id": game_id("steam", appid),
                    "name": name,
                    "genre": "Steam",
                    "source": "steam",
                    "launch": {"steam_appid": appid},
                    "art": art,
                    "hue": hue_for(name),
                })
    return games


def scan_all(desktop_dirs=None, steam_roots=None, compat=None):
    compat = compat or {}
    games = []
    if compat.get("native", True):
        games += [g for g in scan_desktop(desktop_dirs) if g["source"] != "steam"]
    if compat.get("steam", True):
        steam = scan_steam(steam_roots)
        names = {g["name"].lower() for g in steam}
        # Steam also writes desktop shortcuts ("steam steam://rungameid/..."); keep one copy.
        games = [g for g in games if not _is_steam_shortcut(g) or g["name"].lower() not in names]
        games += steam
    games.sort(key=lambda g: g["name"].lower())
    return games


def _is_steam_shortcut(g):
    argv = g.get("launch", {}).get("argv") or []
    return any("steam://" in a for a in argv)


def launch_argv(game):
    l = game["launch"]
    if "steam_appid" in l:
        return ["steam", f"steam://rungameid/{l['steam_appid']}"]
    return list(l["argv"])
