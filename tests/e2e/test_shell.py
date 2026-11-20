"""End-to-end test of the shell UI in headless Chromium.

Starts anypc-shelld in demo mode on a free port, then drives the UI with a
simulated gamepad and the keyboard, the way a player would.

    pip install playwright && python3 -m playwright install chromium
    python3 tests/e2e/test_shell.py            # CHROME=/path/to/chrome to use another browser
    python3 tests/e2e/test_shell.py --shots out/   # also save screenshots
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

from playwright.async_api import async_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SHOTS = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else None

# A fake standard-mapping gamepad the test presses buttons on.
FAKE_PAD = """
window.__pad = {buttons: Array.from({length: 17}, () => ({pressed: false, value: 0})), axes: [0, 0, 0, 0],
  connected: true, index: 0, id: 'Test Pad (STANDARD GAMEPAD)', mapping: 'standard'};
navigator.getGamepads = () => [window.__pad];
"""
A, B, LB, RB, UP, DOWN, LEFT, RIGHT, GUIDE = 0, 1, 4, 5, 12, 13, 14, 15, 16
FOCUS = "(() => { const a = document.activeElement; return (a.dataset.key || a.dataset.act || '') + '|' + a.textContent.trim(); })()"

failures = []


def check(cond, what):
    print(("  ok   " if cond else "  FAIL ") + what)
    if not cond:
        failures.append(what)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def press(pg, button, hold=70):
    await pg.evaluate(f"window.__pad.buttons[{button}].pressed = true")
    await pg.wait_for_timeout(hold)
    await pg.evaluate(f"window.__pad.buttons[{button}].pressed = false")
    await pg.wait_for_timeout(120)


async def shot(pg, name):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        await pg.screenshot(path=os.path.join(SHOTS, name + ".png"))


async def api(pg, path):
    return await pg.evaluate(f"fetch('{path}').then(r => r.json())")


async def open_settings(pg, cat):
    await pg.evaluate(f"""(() => {{ const a = window.__anypc;
      if (a.top().cat === undefined) a.show('settings');
      const s = a.top(); s.cat = '{cat}'; s.markCats(); return s.load(); }})()""")
    await pg.wait_for_timeout(400)


async def run(port):
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
        pg = await browser.new_page(viewport={"width": 1280, "height": 720})
        await pg.add_init_script(FAKE_PAD)
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "404" not in m.text else None)

        print("boot and first-time setup")
        await pg.goto(f"http://127.0.0.1:{port}/")
        await pg.wait_for_timeout(2500)
        await shot(pg, "01-boot")
        await press(pg, A)
        await pg.wait_for_timeout(700)
        check(await pg.evaluate("!!document.querySelector('.setup')"), "boot leads to setup when there are no profiles")
        for _ in range(3):  # language, network, controller
            await pg.evaluate("document.querySelector('[data-act=\"next\"]').focus()")
            await press(pg, A)
            await pg.wait_for_timeout(400)
        await pg.evaluate("document.querySelector('#pname').focus()")
        await press(pg, A)  # opens the on-screen keyboard
        await pg.wait_for_timeout(300)
        check(await pg.evaluate("!!document.querySelector('.osk')"), "gamepad A on a text field opens the on-screen keyboard")
        await pg.keyboard.type("Tester")
        await pg.keyboard.press("Enter")
        await pg.wait_for_timeout(300)
        await pg.evaluate("document.querySelector('[data-act=\"next\"]').focus()")
        await press(pg, A)
        await pg.wait_for_timeout(500)
        users = await api(pg, "/api/users")
        check([u["name"] for u in users] == ["Tester"], "profile created with the typed name")
        await press(pg, A)  # Start
        await pg.wait_for_timeout(800)

        print("home and launching")
        check(await pg.evaluate("window.__anypc.top().name") == "home", "setup ends on the home screen")
        await shot(pg, "02-home")
        await press(pg, RIGHT)
        await press(pg, RIGHT)
        await press(pg, DOWN)
        check((await pg.evaluate(FOCUS)).startswith("play"), "down from a game tile lands on Play")
        await press(pg, A)
        await pg.wait_for_timeout(600)
        check((await api(pg, "/api/running"))["running"], "Play starts the game")
        await press(pg, GUIDE)
        await pg.wait_for_timeout(500)
        check(await pg.evaluate("!!window.__anypc.overlay"), "guide button opens the control center")
        await shot(pg, "03-control-center")
        await pg.evaluate("document.querySelector('.overlay [data-act=\"quit\"]').focus()")
        await press(pg, A)
        await pg.wait_for_timeout(500)
        check(not (await api(pg, "/api/running"))["running"], "Quit game in the control center stops it")
        await press(pg, B)
        await pg.wait_for_timeout(300)

        print("library")
        await press(pg, RB)
        await pg.wait_for_timeout(600)
        check(await pg.evaluate("window.__anypc.top().name") == "library", "RB on home opens the library")
        count = await pg.evaluate("document.querySelectorAll('.gcard').length")
        check(count == len(await api(pg, "/api/games")), "library shows every game")
        await press(pg, RB)
        await pg.wait_for_timeout(300)
        check(await pg.evaluate("document.querySelector('.chip[aria-selected=\"true\"]').dataset.i") == "1", "RB switches the library filter")
        await press(pg, B)
        await pg.wait_for_timeout(400)

        print("settings")
        for cat in ["display", "sound", "network", "bluetooth", "controllers", "storage", "users", "compat",
                    "datetime", "power", "system", "access", "language"]:
            await open_settings(pg, cat)
            rows = await pg.evaluate("document.querySelectorAll('.pane .srow').length")
            check(rows > 0, f"settings page '{cat}' has content")
            await shot(pg, f"10-settings-{cat}")

        await open_settings(pg, "network")
        await pg.evaluate("document.querySelector('[data-v=\"Home Network\"]').focus()")
        await press(pg, A)
        await pg.wait_for_timeout(300)
        await pg.keyboard.type("password123")
        await pg.keyboard.press("Enter")
        await pg.wait_for_timeout(600)
        net = await api(pg, "/api/network")
        check(any(w["ssid"] == "Home Network" and w["active"] for w in net["wifi"]), "Wi-Fi joins with the typed password")

        await open_settings(pg, "bluetooth")
        await pg.evaluate("document.querySelector('[data-act=\"bt-scan\"]').focus()")
        await press(pg, A)
        await pg.wait_for_timeout(500)
        await pg.evaluate("document.querySelector('[data-v=\"AA:BB:CC:00:00:02\"]').focus()")
        await press(pg, A)
        await pg.wait_for_timeout(600)
        bt = await api(pg, "/api/bluetooth")
        check(any(d["mac"] == "AA:BB:CC:00:00:02" and d["paired"] for d in bt["devices"]), "Bluetooth device pairs")

        await open_settings(pg, "system")
        await pg.evaluate("document.querySelector('[data-act=\"upd-check\"]').focus()")
        await press(pg, A)
        await pg.wait_for_timeout(500)
        check((await api(pg, "/api/updates"))["available"] is not None, "update check finds the demo update")

        await open_settings(pg, "datetime")
        await pg.evaluate("document.querySelector('[data-act=\"timezone\"]').focus()")
        await press(pg, A)
        await pg.wait_for_timeout(400)
        await press(pg, UP)
        await press(pg, A)
        await pg.wait_for_timeout(400)
        check((await api(pg, "/api/timedate"))["timezone"] != "Europe/Bucharest", "time zone can be changed")

        await open_settings(pg, "controllers")
        await pg.evaluate("document.querySelector('[data-act=\"padtest\"]').focus()")
        await press(pg, A)
        await pg.wait_for_timeout(300)
        await press(pg, A)
        check(await pg.evaluate("window.__anypc.layers.length") == 1, "A is tested, not used, inside the controller test")
        await press(pg, B, hold=1900)
        check(await pg.evaluate("window.__anypc.layers.length") == 0, "holding B leaves the controller test")

        await open_settings(pg, "language")
        await pg.evaluate("document.querySelector('[data-act=\"lang\"][data-v=\"ro\"]').click()")
        await pg.wait_for_timeout(500)
        check(await pg.evaluate("document.querySelector('.pane h1').textContent") == "Limbă", "language switches to Romanian")

        print("layouts")
        for w, h in [(1920, 1080), (1280, 1024), (844, 390)]:
            await pg.set_viewport_size({"width": w, "height": h})
            await pg.wait_for_timeout(300)
            box = await pg.evaluate("(() => { const r = document.getElementById('stage').getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })()")
            check(box[0] >= -1 and box[1] >= -1 and box[2] <= w + 1 and box[3] <= h + 1, f"screen fits at {w}x{h}")
            await shot(pg, f"20-layout-{w}x{h}")

        check(not errors, "no JavaScript errors" + (f": {errors}" if errors else ""))
        await browser.close()


def main():
    port = free_port()
    cfg = tempfile.mkdtemp()
    env = dict(os.environ, XDG_CONFIG_HOME=cfg, PYTHONPATH=os.path.join(ROOT, "shell", "daemon"))
    daemon = subprocess.Popen([sys.executable, "-m", "anypc_shelld", "--demo", "--port", str(port),
                               "--ui", os.path.join(ROOT, "shell", "ui")], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), 0.2).close()
                break
            except OSError:
                time.sleep(0.1)
        asyncio.run(run(port))
    finally:
        daemon.terminate()
        daemon.wait(5)
    if failures:
        print(f"\n{len(failures)} check(s) failed")
        sys.exit(1)
    print("\nEnd-to-end test passed")


if __name__ == "__main__":
    main()
