"""HTTP server: JSON API under /api and the shell UI as static files."""

import json
import mimetypes
import os
import signal
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

from . import __version__, OS_NAME, OS_VERSION
from . import games as games_mod
from .store import Store
from .system import Backend, DemoBackend, demo_games

MAX_BODY = 64 * 1024
GAMES_TTL = 10


class Runner:
    """Starts one game at a time and tracks play time."""

    def __init__(self, store, demo=False):
        self.store, self.demo = store, demo
        self._lock = threading.Lock()
        self.current = None  # {"game": {...}, "proc": Popen|None, "started": t}

    def status(self):
        with self._lock:
            if not self.current:
                return {"running": False}
            g = self.current["game"]
            return {"running": True, "id": g["id"], "name": g["name"],
                    "started": int(self.current["started"])}

    def launch(self, game):
        with self._lock:
            if self.current:
                raise RuntimeError("a game is already running")
            proc = None
            if not self.demo:
                proc = subprocess.Popen(games_mod.launch_argv(game), stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        start_new_session=True)
            self.current = {"game": game, "proc": proc, "started": time.time()}
        self.store.record_start(game["id"])
        if proc is not None:
            threading.Thread(target=self._wait, args=(proc,), daemon=True).start()
        return self.status()

    def _wait(self, proc):
        proc.wait()
        self._finish(proc)

    def _finish(self, proc):
        with self._lock:
            cur = self.current
            if not cur or cur["proc"] is not proc:
                return
            self.current = None
        # Steam hands the game off and exits at once; don't count that as play time.
        if cur["game"]["source"] != "steam":
            self.store.record_seconds(cur["game"]["id"], time.time() - cur["started"])

    def stop(self):
        with self._lock:
            cur = self.current
        if not cur:
            return {"running": False}
        proc = cur["proc"]
        if proc is None:  # demo
            self._finish(None)
            return self.status()
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self._finish(proc)
        return self.status()


class App:
    def __init__(self, ui_dir, store=None, demo=False, desktop_dirs=None, steam_roots=None, port=7700):
        self.ui_dir = os.path.realpath(ui_dir) if ui_dir else None
        self.store = store or Store()
        self.demo = demo
        self.backend = DemoBackend() if demo else Backend()
        self.runner = Runner(self.store, demo=demo)
        self.desktop_dirs, self.steam_roots = desktop_dirs, steam_roots
        self.port = port
        self._games, self._games_at = [], 0.0
        self._games_lock = threading.Lock()

    def games(self, refresh=False):
        with self._games_lock:
            if refresh or time.time() - self._games_at > GAMES_TTL:
                if self.demo:
                    self._games = demo_games()
                else:
                    self._games = games_mod.scan_all(self.desktop_dirs, self.steam_roots,
                                                     self.store.settings()["compat"])
                self._games_at = time.time()
            return list(self._games)

    def find_game(self, gid):
        return next((g for g in self.games() if g["id"] == gid), None)

    def public_game(self, g, plays):
        p = plays.get(g["id"], {})
        return {"id": g["id"], "name": g["name"], "genre": g["genre"], "source": g["source"],
                "hue": g["hue"], "hasArt": bool(g.get("art")),
                "seconds": p.get("seconds", 0), "lastPlayed": p.get("last", 0)}


def make_handler(app):
    allowed_hosts = {f"127.0.0.1:{app.port}", f"localhost:{app.port}", "127.0.0.1", "localhost"}

    class Handler(BaseHTTPRequestHandler):
        server_version = f"anypc-shelld/{__version__}"

        def log_message(self, fmt, *args):  # keep the journal quiet
            pass

        # -- helpers ----------------------------------------------------------
        def _send(self, status, body=b"", ctype="application/json", extra=None):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, obj, status=HTTPStatus.OK):
            self._send(status, json.dumps(obj, ensure_ascii=False).encode())

        def _error(self, status, msg):
            self._json({"error": msg}, status)

        def _host_ok(self):
            # Reject DNS-rebinding: only answer requests addressed to localhost.
            return (self.headers.get("Host") or "") in allowed_hosts

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise ValueError("body too large")
            raw = self.rfile.read(n) if n else b"{}"
            data = json.loads(raw.decode() or "{}")
            if not isinstance(data, dict):
                raise ValueError("body must be a JSON object")
            return data

        # -- verbs ------------------------------------------------------------
        def do_GET(self):
            if not self._host_ok():
                return self._error(HTTPStatus.FORBIDDEN, "bad host")
            url = urlsplit(self.path)
            if url.path.startswith("/api/"):
                return self._api_get(url.path, parse_qs(url.query))
            return self._static(url.path)

        do_HEAD = do_GET

        def do_POST(self):
            if not self._host_ok():
                return self._error(HTTPStatus.FORBIDDEN, "bad host")
            # A custom header can't be sent cross-origin without a CORS preflight,
            # which we never approve, so other websites cannot drive this API.
            if self.headers.get("X-AnyPC") != "1":
                return self._error(HTTPStatus.FORBIDDEN, "missing X-AnyPC header")
            try:
                body = self._body()
            except (ValueError, UnicodeDecodeError):
                return self._error(HTTPStatus.BAD_REQUEST, "invalid JSON body")
            try:
                return self._api_post(urlsplit(self.path).path, body)
            except ValueError as e:
                return self._error(HTTPStatus.BAD_REQUEST, str(e))
            except RuntimeError as e:
                return self._error(HTTPStatus.CONFLICT, str(e))

        # -- API --------------------------------------------------------------
        def _api_get(self, path, q):
            plays = app.store.plays()
            if path == "/api/state":
                return self._json({"os": OS_NAME, "version": OS_VERSION, "daemon": __version__,
                                   "demo": app.demo, "running": app.runner.status()})
            if path == "/api/users":
                return self._json(app.store.users())
            if path == "/api/games":
                gs = app.games(refresh="refresh" in q)
                return self._json([app.public_game(g, plays) for g in gs])
            if path.startswith("/api/games/") and path.endswith("/art"):
                g = app.find_game(path.split("/")[3])
                return self._file(g.get("art") if g else None)
            if path == "/api/running":
                return self._json(app.runner.status())
            if path == "/api/settings":
                return self._json(app.store.settings())
            if path == "/api/system":
                return self._json(app.backend.info())
            if path == "/api/audio":
                return self._json(app.backend.audio())
            if path == "/api/network":
                return self._json(app.backend.network())
            return self._error(HTTPStatus.NOT_FOUND, "not found")

        def _api_post(self, path, body):
            if path == "/api/users":
                return self._json(app.store.add_user(body.get("name"), body.get("color")), HTTPStatus.CREATED)
            parts = path.split("/")
            if len(parts) == 5 and parts[2] == "games" and parts[4] == "launch":
                g = app.find_game(parts[3])
                if not g:
                    return self._error(HTTPStatus.NOT_FOUND, "unknown game")
                return self._json(app.runner.launch(g))
            if path == "/api/running/stop":
                return self._json(app.runner.stop())
            if path == "/api/settings":
                s = app.store.update_settings(body)
                return self._json(s)
            if path == "/api/audio":
                vol = body.get("volume")
                if vol is not None and not isinstance(vol, (int, float)):
                    raise ValueError("volume must be a number")
                muted = body.get("muted")
                if muted is not None and not isinstance(muted, bool):
                    raise ValueError("muted must be true or false")
                return self._json(app.backend.set_audio(vol, muted))
            if len(parts) == 4 and parts[2] == "power":
                return self._json(app.backend.power(parts[3]))
            return self._error(HTTPStatus.NOT_FOUND, "not found")

        # -- files ------------------------------------------------------------
        def _file(self, path):
            if not path or not path.lower().endswith(games_mod.ART_EXT) or not os.path.isfile(path):
                return self._error(HTTPStatus.NOT_FOUND, "no art")
            try:
                with open(path, "rb") as f:
                    data = f.read()
            except OSError:
                return self._error(HTTPStatus.NOT_FOUND, "no art")
            ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
            self._send(HTTPStatus.OK, data, ctype)

        def _static(self, path):
            if not app.ui_dir:
                return self._error(HTTPStatus.NOT_FOUND, "no ui")
            rel = path.lstrip("/") or "index.html"
            full = os.path.realpath(os.path.join(app.ui_dir, rel))
            if not (full == app.ui_dir or full.startswith(app.ui_dir + os.sep)) or not os.path.isfile(full):
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            with open(full, "rb") as f:
                data = f.read()
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
                ctype += "; charset=utf-8"
            self._send(HTTPStatus.OK, data, ctype,
                       {"Content-Security-Policy": "default-src 'self'; img-src 'self' data:; "
                                                   "style-src 'self' 'unsafe-inline'; frame-ancestors 'none'"})

    return Handler


def serve(app, host="127.0.0.1", port=7700):
    httpd = ThreadingHTTPServer((host, port), make_handler(app))
    httpd.daemon_threads = True
    return httpd
