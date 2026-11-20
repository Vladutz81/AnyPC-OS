import { api } from "./api.js";
import { Input, moveFocus, focusables } from "./input.js";
import { setLang, t } from "./i18n.js";
import { el, esc, timeNow, setClock24 } from "./ui.js";
import { BootScreen } from "./screens/boot.js";
import { UsersScreen } from "./screens/users.js";
import { SetupScreen } from "./screens/setup.js";
import { HomeScreen } from "./screens/home.js";
import { LibraryScreen } from "./screens/library.js";
import { GameScreen } from "./screens/game.js";
import { SettingsScreen } from "./screens/settings.js";
import { ControlCenter } from "./screens/control.js";

export const SCREENS = { home: HomeScreen, library: LibraryScreen, game: GameScreen, settings: SettingsScreen, users: UsersScreen, setup: SetupScreen };

class App {
  constructor(stage) {
    this.stage = stage;
    this.stack = [];   // full screens
    this.layers = [];  // overlays on top (control center, dialogs, keyboard)
    this.data = { state: null, users: [], games: [], settings: null, running: { running: false } };
    this.user = null;
    this.lastInput = Date.now();
    this.input = new Input({
      move: (d) => moveFocus(this.root(), d),
      activate: () => this.activate(),
      back: () => this.back(),
      menu: () => this.toggleControl(),
      tab: (d) => { const o = this.layers.length ? this.topLayer() : this.top(); o && o.onTab && o.onTab(d); },
      any: (e) => this.onAny(e),
      anyPad: (p) => { const o = this.top(); o && o.onPad && o.onPad(p); this.emit("pads"); },
      activity: () => { this.lastInput = Date.now(); },
    });
    document.body.dataset.input = "mouse";
    // Missing artwork: drop the <img> and keep the abstract cover underneath.
    document.addEventListener("error", (e) => {
      if (e.target.tagName === "IMG" && e.target.closest(".art")) e.target.remove();
    }, true);
    stage.addEventListener("click", (e) => this.onClick(e));
    stage.addEventListener("focusin", (e) => ensureVisible(e.target));
    setInterval(() => this.tickClock(), 10000);
    setInterval(() => this.pollRunning(), 3000);
    setInterval(() => this.checkIdle(), 30000);
  }

  // ---------- data ----------
  async load() {
    const [state, users, settings] = await Promise.all([api.get("/api/state"), api.get("/api/users"), api.get("/api/settings")]);
    this.data.state = state;
    this.data.users = users;
    this.data.running = state.running || { running: false };
    this.applySettings(settings);
    await this.loadGames();
  }

  async loadGames(refresh = false) {
    this.data.games = await api.get("/api/games" + (refresh ? "?refresh=1" : ""));
    return this.data.games;
  }

  applySettings(s) {
    this.data.settings = s;
    setLang(s.language);
    setClock24(s.clock_24h !== false);
    this.tickClock();
    document.body.classList.toggle("reduce-motion", !!s.reduce_motion);
    document.body.classList.toggle("high-contrast", !!s.high_contrast);
    document.documentElement.style.setProperty("--safe", String((s.overscan || 100) / 100));
  }

  async saveSettings(patch) {
    try {
      this.applySettings(await api.post("/api/settings", patch));
      return true;
    } catch (e) {
      this.toast(e.message || t("error"));
      return false;
    }
  }

  tickClock() {
    document.querySelectorAll("[data-clock]").forEach((c) => (c.textContent = timeNow()));
  }

  async pollRunning() {
    try {
      const r = await api.get("/api/running");
      const was = this.data.running.running;
      this.data.running = r;
      if (was !== r.running) {
        if (!r.running) await this.loadGames();
        this.emit("running");
      }
    } catch (e) { /* service restarting; try again next tick */ }
  }

  // Rest mode after the chosen idle time, unless a game is running.
  checkIdle() {
    const s = this.data.settings;
    if (!s || !s.rest_after || this.data.running.running || (this.data.state && this.data.state.demo)) return;
    if (Date.now() - this.lastInput > s.rest_after * 60000) {
      this.lastInput = Date.now();
      api.post("/api/power/suspend", {}).catch(() => {});
    }
  }

  emit(name) {
    for (const s of this.stack) s.on && s.on(name);
    for (const l of this.layers) l.on && l.on(name);
  }

  // ---------- launching ----------
  async launch(game) {
    this.toast(t("starting"));
    try {
      this.data.running = await api.post(`/api/games/${encodeURIComponent(game.id)}/launch`, {});
      await this.loadGames();
      this.toast(t("launched", { name: game.name }));
      this.emit("running");
    } catch (e) {
      this.toast(e.message === "a game is already running" ? t("now_playing") + ": " + (this.data.running.name || "") : t("launch_failed"));
    }
  }

  async quitGame() {
    this.data.running = await api.post("/api/running/stop", {});
    await this.loadGames();
    this.emit("running");
  }

  // ---------- screens ----------
  top() { return this.stack[this.stack.length - 1]; }
  topLayer() { return this.layers[this.layers.length - 1]; }
  get overlay() { return this.layers.find((l) => l instanceof ControlCenter) || null; }
  root() { return this.layers.length ? this.topLayer().el : (this.top() ? this.top().el : this.stage); }

  show(name, params = {}, opts = {}) {
    while (this.layers.length) this.closeLayer(this.topLayer(), null, true);
    const Screen = SCREENS[name];
    const scr = new Screen(this, params);
    const prev = this.top();
    if (opts.reset) {
      while (this.stack.length) { const s = this.stack.pop(); s.dispose && s.dispose(); s.el.remove(); }
    } else if (prev) {
      prev.el.setAttribute("inert", "");
      prev.el.style.visibility = "hidden";
    }
    this.stack.push(scr);
    this.stage.appendChild(scr.el);
    this.focusIn(scr);
    return scr;
  }

  focusIn(scr) {
    requestAnimationFrame(() => {
      const target = (scr.restoreFocus && scr.el.contains(scr.restoreFocus) && scr.restoreFocus)
        || scr.el.querySelector("[data-autofocus]") || focusables(scr.el)[0];
      if (target) target.focus({ preventScroll: true });
    });
  }

  back() {
    if (this.layers.length) {
      const l = this.topLayer();
      if (l.onBack && l.onBack()) return;
      return this.closeLayer(l, null);
    }
    const top = this.top();
    if (top && top.onBack && top.onBack()) return;
    if (this.stack.length > 1) {
      const s = this.stack.pop();
      s.dispose && s.dispose();
      s.el.remove();
      const now = this.top();
      now.el.removeAttribute("inert");
      now.el.style.visibility = "";
      now.onShow && now.onShow();
      this.focusIn(now);
    }
  }

  activate() {
    const l = this.topLayer();
    if (l && l.padOnly && document.body.dataset.input === "pad") return; // e.g. controller test
    const a = document.activeElement;
    if (!a || a === document.body) return moveFocus(this.root(), "down");
    if (a.tagName === "INPUT" && document.body.dataset.input === "kbd") return moveFocus(this.root(), "down");
    a.click();
  }

  onAny(e) {
    const l = this.topLayer();
    if (l) return e && l.onKey ? l.onKey(e) : false;
    const top = this.top();
    return top && top.onAny ? top.onAny(e) : false;
  }

  onClick(e) {
    const b = e.target.closest("[data-act]");
    if (!b) return;
    const act = b.dataset.act;
    const owner = this.layers.slice().reverse().find((l) => l.el.contains(b)) || this.top();
    if (act === "back") return this.back();
    if (act === "control") return this.toggleControl();
    owner && owner.act && owner.act(act, b, e);
  }

  // ---------- layers ----------
  openLayer(layer) {
    const under = this.layers.length ? this.topLayer() : this.top();
    if (under) {
      under.restoreFocus = document.activeElement;
      under.el.setAttribute("inert", "");
      if (!this.layers.length) under.el.classList.add("under");
    }
    this.layers.push(layer);
    this.stage.appendChild(layer.el);
    this.focusIn(layer);
  }

  closeLayer(layer, value, silent) {
    const i = this.layers.indexOf(layer);
    if (i < 0) return;
    this.layers.splice(i, 1);
    layer.dispose && layer.dispose();
    layer.el.remove();
    const under = this.layers.length ? this.topLayer() : this.top();
    if (under) {
      under.el.removeAttribute("inert");
      if (!this.layers.length) under.el.classList.remove("under");
      if (!silent) this.focusIn(under);
    }
    layer.done && layer.done(value);
  }

  toggleControl() {
    if (!this.data.state || (this.top() && this.top().noMenu)) return;
    const cc = this.overlay;
    if (cc) return this.closeLayer(cc, null);
    if (this.layers.length) return; // a dialog is open; finish it first
    this.openLayer(new ControlCenter(this));
  }

  closeControl() { const cc = this.overlay; if (cc) this.closeLayer(cc, null); }

  goHome() { this.show("home", {}, { reset: true }); }

  afterBoot() {
    if (!this.data.users.length) this.show("setup", {}, { reset: true });
    else this.show("users", {}, { reset: true });
  }

  signIn(user) {
    this.user = user;
    this.show("home", {}, { reset: true });
  }

  // Leave the shell; the session restarts it or switches to the desktop.
  async exitShell(action) {
    const res = await api.post(`/api/power/${action}`, {}).catch((e) => ({ error: e.message }));
    if (res && res.demo) return this.toast(t("demo_only"));
    if (res && res.note === "exit-shell") return window.close();
    if (res && res.error) this.toast(res.error);
  }

  toast(msg) {
    this.stage.querySelectorAll(".toast").forEach((n) => n.remove());
    const n = el(`<div class="toast" role="status">${esc(msg)}</div>`);
    this.stage.appendChild(n);
    setTimeout(() => n.remove(), 3000);
  }
}

// Keep the focused element inside its scrolling list visible.
function ensureVisible(target) {
  const box = target.closest && target.closest("[data-scroll]");
  if (!box || box === target) return;
  const b = box.getBoundingClientRect(), r = target.getBoundingClientRect();
  const pad = parseFloat(getComputedStyle(document.documentElement).fontSize);
  if (r.top < b.top + pad) box.scrollTop -= b.top + pad - r.top;
  else if (r.bottom > b.bottom - pad) box.scrollTop += r.bottom - (b.bottom - pad);
}

async function start() {
  const stage = document.getElementById("stage");
  const app = new App(stage);
  window.__anypc = app; // handy for debugging from the console
  await app.load();
  const s = app.data.settings;
  if (s.boot_animation && !s.reduce_motion && !new URLSearchParams(location.search).has("noboot")) {
    const boot = new BootScreen(app);
    app.stack.push(boot);
    stage.appendChild(boot.el);
  } else {
    app.afterBoot();
  }
}

start();
