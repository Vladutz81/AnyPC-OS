import { el, esc, background, backButton, clock, bytes, avatar, hints } from "../ui.js";
import { icon } from "../icons.js";
import { t, LANGS, getLang } from "../i18n.js";
import { api } from "../api.js";

const CATS = [
  ["display", "monitor"], ["sound", "volume"], ["network", "wifi"], ["controllers", "pad"],
  ["storage", "storage"], ["users", "user"], ["compat", "chip"], ["system", "refresh"],
  ["access", "access"], ["language", "globe"],
];

export class SettingsScreen {
  constructor(app) {
    this.app = app;
    this.cat = "compat";
    this.cache = {};
    this.el = el(`<section class="screen" aria-label="${esc(t("settings"))}">
${background(31, true)}
<header class="topbar">${backButton(t("settings"))}${clock()}</header>
<div class="set"><nav class="cats" aria-label="${esc(t("settings"))}" data-vtrap></nav><section class="pane" aria-live="polite" data-group data-vtrap></section></div>
${hints([["A", t("select")], ["B", t("back")]])}
</section>`);
    this.renderCats();
    this.renderPane();
    this.el.addEventListener("focusin", (e) => {
      const c = e.target.closest(".cat");
      if (c && c.dataset.cat !== this.cat) { this.cat = c.dataset.cat; this.markCats(); this.renderPane(); }
    });
  }

  renderCats() {
    this.el.querySelector(".cats").innerHTML = CATS.map(([id, ic]) =>
      `<button type="button" class="cat" data-act="cat" data-cat="${id}" ${id === this.cat ? 'aria-current="true" data-autofocus' : ""}>${icon(ic)}${esc(t("cat_" + id))}</button>`).join("");
  }

  markCats() {
    this.el.querySelectorAll(".cat").forEach((c) => c.setAttribute("aria-current", String(c.dataset.cat === this.cat)));
  }

  async fetch(key, path) {
    try { this.cache[key] = await api.get(path); } catch (e) { this.cache[key] = null; }
    return this.cache[key];
  }

  row(label, value) { return `<div class="srow"><span>${esc(label)}</span><span class="v">${value}</span></div>`; }
  toggle(act, label, on, extra = "") {
    return `<button type="button" class="srow" role="switch" aria-checked="${!!on}" data-act="${act}" ${extra}><span>${esc(label)}</span><span class="sw"><i></i></span></button>`;
  }

  async renderPane() {
    const cat = this.cat;
    const pane = this.el.querySelector(".pane");
    const s = this.app.data.settings;
    let html = "";
    if (cat === "display") {
      html = this.row(t("resolution"), `${screen.width * devicePixelRatio | 0} × ${screen.height * devicePixelRatio | 0}`) +
        this.row(t("screen"), `${innerWidth} × ${innerHeight}`);
    } else if (cat === "sound") {
      const a = await this.fetch("audio", "/api/audio");
      html = a && a.available
        ? `<div class="srow"><span>${esc(t("volume"))}</span><span style="display:flex;align-items:center;gap:.75rem">
<button type="button" class="mini" data-act="vol-" aria-label="${esc(t("volume"))} −">−</button><span class="v" style="min-width:3.5rem;text-align:center">${a.volume}%</span>
<button type="button" class="mini" data-act="vol+" aria-label="${esc(t("volume"))} +">+</button></span></div>` + this.toggle("mute", t("mute"), a.muted)
        : this.row(t("sound"), esc(t("unavailable")));
    } else if (cat === "network") {
      const n = await this.fetch("net", "/api/network");
      if (!n || !n.available) html = this.row(t("network"), esc(t("unavailable")));
      else {
        html = (n.devices || []).map((d) => this.row(`${d.type === "wifi" ? "Wi-Fi" : "Ethernet"} · ${d.device}`,
          esc(d.state === "connected" ? `${t("connected")}: ${d.connection || ""}` : t("not_connected")))).join("");
        html += (n.wifi || []).length ? (n.wifi || []).map((w) => this.row(w.ssid, `${w.active ? esc(t("connected")) + " · " : ""}${w.signal}%`)).join("")
          : this.row("Wi-Fi", esc(t("no_wifi")));
      }
    } else if (cat === "controllers") {
      const pads = this.app.input.connectedPads();
      html = pads.map((p, i) => this.row(`${t("controllers")} ${i + 1}`, esc(p.id.slice(0, 48)))).join("") + this.row(t("kbd_mouse"), esc(t("connected")));
    } else if (cat === "storage") {
      const info = this.cache.info || await this.fetch("info", "/api/system");
      const d = info && info.disk;
      html = this.row(t("internal_drive"), d ? esc(t("used_of", { used: bytes(d.used), total: bytes(d.total) })) : "—");
    } else if (cat === "users") {
      html = this.app.data.users.map((u) => `<div class="srow"><span style="display:flex;align-items:center;gap:.9rem">${avatar(u, "2.4rem")}${esc(u.name)}</span></div>`).join("") +
        `<button type="button" class="srow" data-act="add-user"><span style="display:flex;align-items:center;gap:.9rem">${icon("plus")}${esc(t("add_user"))}</span>${icon("chevron")}</button>`;
    } else if (cat === "compat") {
      const c = s.compat;
      html = ["steam", "native", "emulators", "anyps5"].map((k) => this.toggle("compat", t("compat_" + k), c[k], `data-k="${k}"`)).join("") +
        `<p class="note">${esc(t("compat_note"))}</p>`;
    } else if (cat === "system") {
      const i = await this.fetch("info", "/api/system");
      const st = this.app.data.state || {};
      html = i ? [
        [t("os_version"), i.os], [t("hostname"), i.hostname], [t("kernel"), i.kernel], [t("cpu"), i.cpu || "—"],
        [t("gpu"), (i.gpus || []).join(", ") || "—"], [t("memory"), bytes(i.memory)],
      ].map(([k, v]) => this.row(k, esc(v))).join("") : "";
      if (st.demo) html += `<p class="note">${esc(t("demo_mode"))}</p>`;
    } else if (cat === "access") {
      html = this.toggle("set", t("reduce_motion"), s.reduce_motion, 'data-k="reduce_motion"') +
        this.toggle("set", t("high_contrast"), s.high_contrast, 'data-k="high_contrast"') +
        this.toggle("set", t("boot_animation"), s.boot_animation, 'data-k="boot_animation"');
    } else if (cat === "language") {
      html = LANGS.map(([code, label]) => `<button type="button" class="srow" data-act="lang" data-v="${code}" aria-pressed="${code === getLang()}"><span>${esc(label)}</span>${code === getLang() ? icon("check") : ""}</button>`).join("");
    }
    if (cat !== this.cat) return; // user moved on while we were loading
    pane.innerHTML = `<h1>${esc(t("cat_" + cat))}</h1>${html}`;
    const first = pane.querySelector("button");
    if (first) first.setAttribute("data-entry", "");
  }

  async act(a, b) {
    const keep = (sel) => { const n = this.el.querySelector(sel); n && n.focus({ preventScroll: true }); };
    if (a === "cat") {
      const first = this.el.querySelector(".pane button");
      return first && first.focus({ preventScroll: true });
    }
    if (a === "compat") {
      await this.app.saveSettings({ compat: { [b.dataset.k]: b.getAttribute("aria-checked") !== "true" } });
      await this.app.loadGames(true);
      await this.renderPane();
      return keep(`[data-act="compat"][data-k="${b.dataset.k}"]`);
    }
    if (a === "set") {
      await this.app.saveSettings({ [b.dataset.k]: b.getAttribute("aria-checked") !== "true" });
      await this.renderPane();
      return keep(`[data-act="set"][data-k="${b.dataset.k}"]`);
    }
    if (a === "lang") {
      await this.app.saveSettings({ language: b.dataset.v });
      // Rebuild the whole screen in the new language.
      const fresh = new SettingsScreen(this.app);
      fresh.cat = "language";
      fresh.renderCats();
      await fresh.renderPane();
      this.el.replaceWith(fresh.el);
      this.app.stack[this.app.stack.indexOf(this)] = fresh;
      return fresh.el.querySelector(`[data-act="lang"][data-v="${b.dataset.v}"]`).focus({ preventScroll: true });
    }
    if (a === "vol-" || a === "vol+" || a === "mute") {
      const cur = this.cache.audio || { volume: 0, muted: false };
      const body = a === "mute" ? { muted: !cur.muted } : { volume: cur.volume + (a === "vol+" ? 5 : -5) };
      this.cache.audio = await api.post("/api/audio", body).catch(() => cur);
      await this.renderPane();
      return keep(`[data-act="${a}"]`);
    }
    if (a === "add-user") return this.app.show("setup", { addOnly: true });
  }

  onShow() { this.renderPane(); }
}
