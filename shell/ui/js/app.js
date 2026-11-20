import { api } from "./api.js";
import { Input, moveFocus, focusables } from "./input.js";
import { setLang, t } from "./i18n.js";
import { el, esc, timeNow } from "./ui.js";
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
    this.stack = [];
    this.overlay = null;
    this.data = { state: null, users: [], games: [], settings: null, running: { running: false } };
    this.user = null;
    this.input = new Input({
      move: (d) => moveFocus(this.root(), d),
      activate: () => this.activate(),
      back: () => this.back(),
      menu: () => this.toggleControl(),
      tab: (d) => this.top() && this.top().onTab && this.top().onTab(d),
      any: (e) => !this.overlay && this.top() && this.top().onAny ? this.top().onAny(e) : false,
      anyPad: (p) => this.top() && this.top().onPad && this.top().onPad(p),
    });
    document.body.dataset.input = "mouse";
    // Missing artwork: drop the <img> and keep the abstract cover underneath.
    document.addEventListener("error", (e) => {
      if (e.target.tagName === "IMG" && e.target.closest(".art")) e.target.remove();
    }, true);
    stage.addEventListener("click", (e) => this.onClick(e));
    setInterval(() => document.querySelectorAll("[data-clock]").forEach((c) => (c.textContent = timeNow())), 10000);
    setInterval(() => this.pollRunning(), 3000);
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
    document.body.classList.toggle("reduce-motion", !!s.reduce_motion);
    document.body.classList.toggle("high-contrast", !!s.high_contrast);
  }

  async saveSettings(patch) {
    try {
      this.applySettings(await api.post("/api/settings", patch));
    } catch (e) {
      this.toast(t("error"));
    }
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

  emit(name) {
    for (const s of this.stack) s.on && s.on(name);
    this.overlay && this.overlay.on && this.overlay.on(name);
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

  // ---------- navigation ----------
  top() { return this.stack[this.stack.length - 1]; }
  root() { return this.overlay ? this.overlay.el : (this.top() ? this.top().el : this.stage); }

  show(name, params = {}, opts = {}) {
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
    if (this.overlay) return this.closeControl();
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
    const a = document.activeElement;
    if (!a || a === document.body) return moveFocus(this.root(), "down");
    if (a.tagName === "INPUT" && a.type === "text") return moveFocus(this.root(), "down");
    a.click();
  }

  onClick(e) {
    const b = e.target.closest("[data-act]");
    if (!b) return;
    const act = b.dataset.act;
    if (act === "back") return this.back();
    if (act === "control") return this.toggleControl();
    const owner = this.overlay && this.overlay.el.contains(b) ? this.overlay : this.top();
    owner && owner.act && owner.act(act, b, e);
  }

  toggleControl() {
    if (!this.data.state || (this.top() && this.top().noMenu)) return;
    this.overlay ? this.closeControl() : this.openControl();
  }

  openControl() {
    const top = this.top();
    if (top) { top.restoreFocus = document.activeElement; top.el.setAttribute("inert", ""); top.el.classList.add("under"); }
    this.overlay = new ControlCenter(this);
    this.stage.appendChild(this.overlay.el);
    this.focusIn(this.overlay);
  }

  closeControl() {
    if (!this.overlay) return;
    this.overlay.dispose && this.overlay.dispose();
    this.overlay.el.remove();
    this.overlay = null;
    const top = this.top();
    if (top) { top.el.removeAttribute("inert"); top.el.classList.remove("under"); this.focusIn(top); }
  }

  goHome() {
    this.closeControl();
    this.show("home", {}, { reset: true });
  }

  afterBoot() {
    if (!this.data.users.length) this.show("setup", {}, { reset: true });
    else this.show("users", {}, { reset: true });
  }

  signIn(user) {
    this.user = user;
    this.show("home", {}, { reset: true });
  }

  toast(msg) {
    this.stage.querySelectorAll(".toast").forEach((n) => n.remove());
    const n = el(`<div class="toast" role="status">${esc(msg)}</div>`);
    this.stage.appendChild(n);
    setTimeout(() => n.remove(), 2600);
  }
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
