import { el, esc, cover } from "../ui.js";
import { icon, mark } from "../icons.js";
import { t } from "../i18n.js";
import { api } from "../api.js";
import { clock } from "../ui.js";

// Overlay opened with the Home / guide button from anywhere.
export class ControlCenter {
  constructor(app) {
    this.app = app;
    this.audio = { available: false, volume: 0, muted: false };
    this.net = null;
    this.el = el(`<section class="overlay" role="dialog" aria-modal="true" aria-label="${esc(t("control_center"))}">
<div class="shade" aria-hidden="true"></div>
<header class="topbar"><span class="brand">${mark("1.6rem")}${esc(t("control_center"))}</span>${clock()}</header>
<div class="cc"><div class="cc-cards"></div><div class="cc-row"></div></div></section>`);
    this.render();
    this.refresh();
  }

  async refresh() {
    try {
      const [a, n] = await Promise.all([api.get("/api/audio"), api.get("/api/network")]);
      this.audio = a;
      this.net = n;
    } catch (e) { /* show what we have */ }
    const keep = document.activeElement && document.activeElement.dataset.act;
    this.renderCards();
    if (keep) {
      const again = this.el.querySelector(`[data-act="${keep}"]`);
      again && again.focus({ preventScroll: true });
    }
  }

  render() {
    this.renderCards();
    const btn = (act, ic, label, auto) => `<button type="button" class="cc-b" data-act="${act}" ${auto ? "data-autofocus" : ""}><span class="ring">${icon(ic)}</span>${esc(label)}</button>`;
    this.el.querySelector(".cc-row").innerHTML = btn("home", "home", t("home"), true) + btn("library", "library", t("library")) +
      btn("settings", "gear", t("settings")) +
      `<div style="position:relative">${btn("power", "power", t("power"))}<div class="menu" role="menu" hidden data-vtrap>
<button type="button" role="menuitem" data-act="pw" data-v="suspend">${icon("moon")}${esc(t("rest"))}</button>
<button type="button" role="menuitem" data-act="pw" data-v="reboot">${icon("refresh")}${esc(t("restart"))}</button>
<button type="button" role="menuitem" data-act="pw" data-v="poweroff">${icon("power")}${esc(t("turn_off"))}</button>
</div></div>`;
  }

  renderCards() {
    const r = this.app.data.running;
    let first;
    if (r.running) {
      const g = this.app.data.games.find((x) => x.id === r.id) || { name: r.name, hue: 220, id: r.id };
      first = `<div class="cc-card running-card"><h2>${esc(t("now_playing"))}</h2>
<span style="display:flex;align-items:center;gap:.75rem"><span class="thumb" style="width:2.75rem;height:2.75rem;border-radius:.6rem;position:relative;overflow:hidden">${cover(g)}</span>${esc(r.name)}</span>
<button type="button" class="btn" data-act="quit" style="height:2.75rem;align-self:flex-start">${icon("stop")}${esc(t("quit_game"))}</button></div>`;
    } else {
      first = `<div class="cc-card"><h2>${esc(t("notifications"))}</h2><span class="sub">${esc(t("no_notifications"))}</span></div>`;
    }
    const a = this.audio;
    const sound = a.available ? `<div class="vol">
<button type="button" class="mini" data-act="vol-" aria-label="${esc(t("volume"))} −">−</button>
<span class="bar" role="img" aria-label="${esc(t("volume"))} ${a.volume}%"><i style="width:${a.muted ? 0 : a.volume}%"></i></span>
<button type="button" class="mini" data-act="vol+" aria-label="${esc(t("volume"))} +">+</button>
<button type="button" class="mini" data-act="mute" aria-label="${esc(t("mute"))}" aria-pressed="${a.muted}">${icon(a.muted ? "mute" : "volume")}</button></div>
<span class="sub">${a.muted ? esc(t("muted")) : a.volume + "%"}</span>` : `<span class="sub">${esc(t("unavailable"))}</span>`;
    let net = `<span class="sub">${esc(t("unavailable"))}</span>`;
    if (this.net && this.net.available) {
      const on = (this.net.devices || []).find((d) => d.state === "connected");
      net = on ? `<span style="display:flex;align-items:center;gap:.6rem">${icon(on.type === "wifi" ? "wifi" : "ethernet")}${esc(on.connection || on.device)}</span><span class="sub">${esc(t("connected"))}</span>`
        : `<span class="sub">${esc(t("not_connected"))}</span>`;
    }
    const pads = this.app.input.connectedPads().length;
    this.el.querySelector(".cc-cards").innerHTML = `${first}
<div class="cc-card"><h2>${esc(t("sound"))}</h2>${sound}</div>
<div class="cc-card"><h2>${esc(t("network"))}</h2>${net}</div>
<div class="cc-card"><h2>${esc(t("controllers"))}</h2><span style="display:flex;align-items:center;gap:.6rem">${icon("pad")}${esc(t("n_controllers", { n: pads }))}</span><span class="sub">${esc(t("kbd_mouse"))}</span></div>`;
  }

  on(evt) { if (evt === "running") this.renderCards(); }

  async act(a, b) {
    const app = this.app;
    if (a === "home") return app.goHome();
    if (a === "library") return app.show("library");
    if (a === "settings") return app.show("settings");
    if (a === "quit") { await app.quitGame(); return this.renderCards(); }
    if (a === "power") {
      const m = this.el.querySelector(".menu");
      m.hidden = !m.hidden;
      if (!m.hidden) m.querySelector("button").focus({ preventScroll: true });
      return;
    }
    if (a === "pw") {
      const v = b.dataset.v;
      const res = await api.post(`/api/power/${v}`, {}).catch((e) => ({ error: e.message }));
      if (res && res.demo) app.toast(`${b.textContent.trim()} · ${t("demo_only")}`);
      else if (res && res.error) app.toast(res.error);
      return;
    }
    if (a === "vol-" || a === "vol+" || a === "mute") {
      const body = a === "mute" ? { muted: !this.audio.muted } : { volume: this.audio.volume + (a === "vol+" ? 5 : -5) };
      this.audio = await api.post("/api/audio", body).catch(() => this.audio);
      this.renderCards();
      const again = this.el.querySelector(`[data-act="${a}"]`);
      again && again.focus({ preventScroll: true });
    }
  }
}
