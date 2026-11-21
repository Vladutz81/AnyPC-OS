"""Small JSON store for users, settings and play statistics."""

import json
import os
import tempfile
import threading
import time
import uuid

DEFAULT_SETTINGS = {
    "language": "en",
    "reduce_motion": False,
    "high_contrast": False,
    "startup_sound": True,
    "ui_sounds": True,
    "boot_animation": True,
    "auto_updates": True,
    "clock_24h": True,
    "rest_after": 30,
    "overscan": 100,
    "compat": {"steam": True, "native": True, "emulators": True, "anyps5": True},
}

# Only these keys may be written through the API, with these types.
SETTING_TYPES = {
    "language": str,
    "reduce_motion": bool,
    "high_contrast": bool,
    "startup_sound": bool,
    "ui_sounds": bool,
    "boot_animation": bool,
    "auto_updates": bool,
    "clock_24h": bool,
    "rest_after": int,
    "overscan": int,
}
# Settings limited to a fixed set of values.
SETTING_CHOICES = {
    "rest_after": (0, 10, 20, 30, 60),
    "overscan": (100, 97, 95, 93, 90),
}
COMPAT_KEYS = ("steam", "native", "emulators", "anyps5")
INITIAL_PROFILE = "/etc/anypc/initial-profile.json"
USER_COLORS = ("blue", "teal", "violet", "orange")


def config_dir():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "anypc")


class Store:
    def __init__(self, path=None):
        self.path = path or os.path.join(config_dir(), "state.json")
        self._lock = threading.Lock()
        seed = self._initial_profile() if path is None and not os.path.exists(self.path) else None
        self._data = self._load(seed)
        if seed:
            self._save()

    @staticmethod
    def _initial_profile():
        try:
            with open(INITIAL_PROFILE, encoding="utf-8") as stream:
                seed = json.load(stream)
            if (isinstance(seed, dict) and isinstance(seed.get("profile"), str)
                    and 1 <= len(seed["profile"]) <= 16 and seed.get("language") in ("en", "ro")):
                return {
                    "users": [{"id": "installed", "name": seed["profile"], "color": USER_COLORS[0]}],
                    "settings": {"language": seed["language"]},
                }
        except (OSError, ValueError):
            pass
        return None

    # -- persistence -------------------------------------------------------
    def _load(self, seed):
        data = {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = seed or {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("users", [])
        data.setdefault("plays", {})
        settings = dict(DEFAULT_SETTINGS)
        settings["compat"] = dict(DEFAULT_SETTINGS["compat"])
        saved = data.get("settings") if isinstance(data.get("settings"), dict) else {}
        for k, t in SETTING_TYPES.items():
            v = saved.get(k)
            if isinstance(v, t) and not (t is int and isinstance(v, bool)) and v in SETTING_CHOICES.get(k, (v,)):
                settings[k] = v
        if isinstance(saved.get("compat"), dict):
            for k in COMPAT_KEYS:
                if isinstance(saved["compat"].get(k), bool):
                    settings["compat"][k] = saved["compat"][k]
        data["settings"] = settings
        return data

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), prefix=".state-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # -- users -------------------------------------------------------------
    def users(self):
        with self._lock:
            return [dict(u) for u in self._data["users"]]

    def add_user(self, name, color):
        name = (name or "").strip()[:16]
        if not name:
            raise ValueError("name is required")
        if color not in USER_COLORS:
            color = USER_COLORS[0]
        user = {"id": uuid.uuid4().hex[:12], "name": name, "color": color}
        with self._lock:
            if len(self._data["users"]) >= 16:
                raise ValueError("too many users")
            self._data["users"].append(user)
            self._save()
        return dict(user)

    def update_user(self, user_id, name=None, color=None):
        with self._lock:
            u = next((x for x in self._data["users"] if x["id"] == user_id), None)
            if not u:
                raise KeyError("unknown user")
            if name is not None:
                name = str(name).strip()[:16]
                if not name:
                    raise ValueError("name is required")
                u["name"] = name
            if color is not None:
                if color not in USER_COLORS:
                    raise ValueError("unknown colour")
                u["color"] = color
            self._save()
            return dict(u)

    def delete_user(self, user_id):
        with self._lock:
            before = len(self._data["users"])
            self._data["users"] = [x for x in self._data["users"] if x["id"] != user_id]
            if len(self._data["users"]) == before:
                raise KeyError("unknown user")
            self._save()

    # -- settings ----------------------------------------------------------
    def reset_settings(self):
        with self._lock:
            self._data["settings"] = json.loads(json.dumps(DEFAULT_SETTINGS))
            self._save()
        return self.settings()

    def settings(self):
        with self._lock:
            s = dict(self._data["settings"])
            s["compat"] = dict(s["compat"])
            return s

    def update_settings(self, patch):
        if not isinstance(patch, dict):
            raise ValueError("settings patch must be an object")
        with self._lock:
            s = self._data["settings"]
            for k, v in patch.items():
                if k == "compat":
                    if not isinstance(v, dict):
                        raise ValueError("compat must be an object")
                    for ck, cv in v.items():
                        if ck not in COMPAT_KEYS or not isinstance(cv, bool):
                            raise ValueError(f"invalid compat setting: {ck}")
                        s["compat"][ck] = cv
                elif k in SETTING_TYPES:
                    t = SETTING_TYPES[k]
                    if not isinstance(v, t) or (t is int and isinstance(v, bool)):
                        raise ValueError(f"invalid type for {k}")
                    if k in SETTING_CHOICES and v not in SETTING_CHOICES[k]:
                        raise ValueError(f"invalid value for {k}")
                    if k == "language":
                        v = v[:8]
                    s[k] = v
                else:
                    raise ValueError(f"unknown setting: {k}")
            self._save()
        return self.settings()

    # -- play statistics ---------------------------------------------------
    def plays(self):
        with self._lock:
            return {k: dict(v) for k, v in self._data["plays"].items()}

    def record_start(self, game_id):
        with self._lock:
            p = self._data["plays"].setdefault(game_id, {"seconds": 0, "last": 0})
            p["last"] = int(time.time())
            self._save()

    def record_seconds(self, game_id, seconds):
        with self._lock:
            p = self._data["plays"].setdefault(game_id, {"seconds": 0, "last": 0})
            p["seconds"] = int(p.get("seconds", 0)) + max(0, int(seconds))
            self._save()
