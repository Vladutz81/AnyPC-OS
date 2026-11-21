import { el, esc, background, backButton, clock, bytes, avatar, hints, timeNow } from "../ui.js";
import { icon } from "../icons.js";
import { t, LANGS, getLang } from "../i18n.js";
import { api } from "../api.js";
import { dialog, choose, keyboard } from "../layers.js";

const CATS = [
  ["display", "monitor"], ["sound", "volume"], ["network", "wifi"], ["bluetooth", "bluetooth"],
  ["controllers", "pad"], ["storage", "storage"], ["users", "user"], ["compat", "chip"],
  ["datetime", "clock"], ["power", "power"], ["system", "refresh"], ["access", "access"], ["language", "globe"],
];
const COLORS = ["blue", "teal", "violet", "orange"];
const OVERSCAN = [100, 97, 95, 93, 90];
const REST = [0, 10, 20, 30, 60];
const HOSTNAME_RE = /^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/;

function sig(n) {
  const on = n >= 75 ? 4 : n >= 50 ? 3 : n >= 25 ? 2 : 1;
  return `<span class="sig" aria-label="${n}%">${[0, 1, 2, 3].map((i) => `<i class="${i < on ? "on" : ""}" style="height:${(i + 1) * 25}%"></i>`).join("")}</span>`;
}

export class SettingsScreen {
  constructor(app, params = {}) {
    this.app = app;
    this.cat = params.cat || "display";
    this.d = {};      // data loaded per category
    this.timer = null;
    this.el = el(`<section class="screen" aria-label="${esc(t("settings"))}">
${background(31, true)}
<header class="topbar">${backButton(t("settings"))}${clock()}</header>
<div class="set"><nav class="cats" aria-label="${esc(t("settings"))}" data-vtrap data-scroll></nav><section class="pane" aria-live="polite" data-group data-vtrap data-scroll></section></div>
${hints([["A", t("select")], ["B", t("back")]])}
</section>`);
    this.renderCats();
    this.load();
    this.el.addEventListener("focusin", (e) => {
      const c = e.target.closest(".cat");
      if (c && c.dataset.cat !== this.cat) { this.cat = c.dataset.cat; this.markCats(); this.load(); }
    });
  }

  dispose() { clearInterval(this.timer); }
  onShow() { this.load(); }
  on(evt) { if (evt === "pads" && this.cat === "controllers" && !this.app.layers.length) this.paint(); }

  renderCats() {
    this.el.querySelector(".cats").innerHTML = CATS.map(([id, ic]) =>
      `<button type="button" class="cat" data-act="cat" data-cat="${id}" aria-current="${id === this.cat}" ${id === this.cat ? "data-autofocus" : ""}>${icon(ic)}${esc(t("cat_" + id))}</button>`).join("");
  }

  markCats() {
    this.el.querySelectorAll(".cat").forEach((c) => c.setAttribute("aria-current", String(c.dataset.cat === this.cat)));
  }

  // ---------- data ----------
  async get(key, path) {
    try { this.d[key] = await api.get(path); } catch (e) { this.d[key] = null; }
    return this.d[key];
  }

  async post(path, body, key) {
    try {
      const r = await api.post(path, body);
      if (key) this.d[key] = r;
      return r;
    } catch (e) {
      this.app.toast(e.message || t("error"));
      return null;
    }
  }

  async load() {
    const cat = this.cat;
    clearInterval(this.timer);
    this.timer = null;
    const need = {
      display: [["displays", "/api/displays"]], sound: [["audio", "/api/audio"]], network: [["net", "/api/network"]],
      bluetooth: [["bt", "/api/bluetooth"]], storage: [["storage", "/api/storage"]], compat: [["modules", "/api/modules"]],
      datetime: [["td", "/api/timedate"]], system: [["info", "/api/system"], ["upd", "/api/updates"]],
    }[cat] || [];
    if (need.some(([k]) => !(k in this.d))) this.paint(true);
    await Promise.all(need.map(([k, p]) => this.get(k, p)));
    if (cat !== this.cat) return;
    this.paint();
    if (cat === "datetime") this.timer = setInterval(() => this.paint(), 15000);
    if (cat === "bluetooth" || cat === "system") this.timer = setInterval(() => this.poll(), 2500);
  }

  async poll() {
    if (this.app.layers.length) return;
    if (this.cat === "bluetooth" && this.d.bt && this.d.bt.scanning) { await this.get("bt", "/api/bluetooth"); this.paint(); }
    if (this.cat === "system" && this.d.upd && /^(checking|downloading|working)$/.test(this.d.upd.state)) { await this.get("upd", "/api/updates"); this.paint(); }
  }

  // ---------- rendering ----------
  row(label, value) { return `<div class="srow"><span>${esc(label)}</span><span class="v">${value}</span></div>`; }
  btn(act, label, value = "", extra = "") {
    return `<button type="button" class="srow" data-act="${act}" ${extra}><span>${label}</span><span class="v">${value}${icon("chevron")}</span></button>`;
  }
  toggle(act, label, on, extra = "") {
    return `<button type="button" class="srow" role="switch" aria-checked="${!!on}" data-act="${act}" ${extra}><span>${esc(label)}</span><span class="sw"><i></i></span></button>`;
  }
  h2(text) { return `<h2>${esc(text)}</h2>`; }

  paint(loading) {
    const pane = this.el.querySelector(".pane");
    const a = document.activeElement;
    const focusKey = pane.contains(a) && a.dataset ? a.dataset.key : null;
    const html = loading ? `<p class="note">…</p>` : this.body();
    pane.innerHTML = `<h1>${esc(t("cat_" + this.cat))}</h1>${html}`;
    pane.querySelectorAll("button").forEach((b) => { b.dataset.key = `${b.dataset.act}:${b.dataset.v || b.dataset.k || ""}`; });
    const first = pane.querySelector("button");
    if (first) first.setAttribute("data-entry", "");
    if (focusKey) {
      const again = [...pane.querySelectorAll("button")].find((b) => b.dataset.key === focusKey) || first;
      again && again.focus({ preventScroll: true });
    }
  }

  body() {
    const s = this.app.data.settings, d = this.d;
    switch (this.cat) {
      case "display": {
        const ds = d.displays || { outputs: [], mode: "auto" };
        const mode = ds.mode === "auto" ? t("automatic") : ds.mode.replace("x", " × ");
        return this.btn("resolution", esc(t("resolution")), esc(mode)) +
          this.btn("overscan", esc(t("screen_fit")), `${s.overscan || 100}%`) +
          `<p class="note">${esc(t("screen_fit_note"))}</p>` +
          (ds.outputs.length ? this.h2(t("connected_displays")) + ds.outputs.map((o) => this.row(o.connector, esc((o.modes[0] || "").replace("x", " × ")))).join("") : "");
      }
      case "sound": {
        const a = d.audio;
        if (!a || !a.available) return this.row(t("sound"), esc(t("unavailable")));
        const out = (a.outputs || []).find((o) => o.default);
        return `<div class="srow"><span>${esc(t("volume"))}</span><span style="display:flex;align-items:center;gap:.75rem">
<button type="button" class="mini" data-act="vol-" aria-label="${esc(t("volume"))} −">−</button><span class="v" style="min-width:3.5rem;justify-content:center">${a.muted ? esc(t("muted")) : a.volume + "%"}</span>
<button type="button" class="mini" data-act="vol+" aria-label="${esc(t("volume"))} +">+</button></span></div>` +
          this.toggle("mute", t("mute"), a.muted) +
          this.toggle("set", t("sound_start"), s.startup_sound, 'data-k="startup_sound"') +
          this.toggle("set", t("sound_ui"), s.ui_sounds, 'data-k="ui_sounds"') +
          ((a.outputs || []).length ? this.btn("output", esc(t("output_device")), esc(out ? out.name : "—")) : "");
      }
      case "network": {
        const n = d.net;
        if (!n || !n.available) return this.row(t("network"), esc(t("unavailable")));
        let h = "";
        const hasWifi = n.devices.some((x) => x.type === "wifi");
        for (const dev of n.devices.filter((x) => x.type === "ethernet")) {
          h += this.row(`Ethernet · ${dev.device}`, `${icon("ethernet")}${esc(dev.state === "connected" ? t("connected") : t("not_connected"))}`);
        }
        if (hasWifi) {
          h += this.toggle("wifi-radio", "Wi-Fi", n.wifiEnabled);
          if (n.wifiEnabled) {
            h += this.h2(t("wifi_networks")) + this.btn("rescan", `${icon("refresh")} ${esc(t("search_again"))}`);
            h += n.wifi.length ? n.wifi.map((w) => `<button type="button" class="srow" data-act="wifi" data-v="${esc(w.ssid)}"><span style="display:flex;align-items:center;gap:.7rem">${sig(w.signal)}${esc(w.ssid)}</span><span class="v">${w.active ? `<span class="tag ok">${esc(t("connected"))}</span>` : w.saved ? `<span class="tag">${esc(t("saved"))}</span>` : ""}${w.secure ? icon("lock") : ""}</span></button>`).join("")
              : `<p class="note">${esc(t("no_wifi"))}</p>`;
          }
        }
        if (n.saved.length) {
          h += this.h2(t("saved_networks")) + n.saved.map((c) => this.btn("forget", esc(c.name), esc(t("forget")), `data-v="${esc(c.name)}"`)).join("");
        }
        return h;
      }
      case "bluetooth": {
        const b = d.bt;
        if (!b || !b.available) return this.row("Bluetooth", esc(t("unavailable")));
        let h = this.toggle("bt-power", "Bluetooth", b.powered);
        if (!b.powered) return h;
        h += this.btn("bt-scan", `${icon("search")} ${esc(b.scanning ? t("searching") : t("search_devices"))}`, "", b.scanning ? 'aria-busy="true"' : "");
        h += this.h2(t("devices"));
        h += b.devices.length ? b.devices.map((x) => {
          const ic = /gaming|joystick/.test(x.icon) ? "pad" : /audio|headset|headphone/.test(x.icon) ? "headset" : "bluetooth";
          const tags = (x.connected ? `<span class="tag ok">${esc(t("connected"))}</span>` : x.paired ? `<span class="tag">${esc(t("paired"))}</span>` : `<span class="tag">${esc(t("pair"))}</span>`) +
            (x.battery != null ? `<span>${icon("battery")} ${x.battery}%</span>` : "");
          return `<button type="button" class="srow" data-act="bt" data-v="${esc(x.mac)}"><span style="display:flex;align-items:center;gap:.8rem">${icon(ic)}${esc(x.name)}</span><span class="v">${tags}</span></button>`;
        }).join("") : `<p class="note">${esc(t("no_devices"))}</p>`;
        return h;
      }
      case "controllers": {
        const pads = this.app.input.connectedPads();
        return (pads.length ? pads.map((p, i) => this.btn("padtest", `${icon("pad")} ${esc(p.id.replace(/\s*\(.*$/, "").slice(0, 40) || t("controllers") + " " + (i + 1))}`, esc(t("test")), `data-v="${p.index}"`)).join("")
          : `<p class="note">${esc(t("no_pads"))}</p>`) +
          this.btn("go-bt", `${icon("bluetooth")} ${esc(t("pair_controller"))}`) +
          this.row(t("kbd_mouse"), esc(t("connected")));
      }
      case "storage": {
        const st = d.storage || [];
        if (!st.length) return this.row(t("cat_storage"), "—");
        return st.map((x) => {
          const name = x.removable ? `${x.mount.split("/").pop()} · ${t("external_drive")}` : t("internal_drive");
          const pct = Math.round((x.used / x.total) * 100);
          return `<div class="srow drive"><div class="top"><span style="display:flex;align-items:center;gap:.7rem">${icon(x.removable ? "usb" : "storage")}${esc(name)}</span><span class="v">${esc(t("free_of", { free: bytes(x.free), total: bytes(x.total) }))}</span></div><div class="meter" role="img" aria-label="${pct}%"><i style="width:${pct}%"></i></div></div>`;
        }).join("");
      }
      case "users":
        return this.app.data.users.map((u) => `<button type="button" class="srow" data-act="user" data-v="${esc(u.id)}"><span style="display:flex;align-items:center;gap:.9rem">${avatar(u, "2.4rem")}${esc(u.name)}</span><span class="v">${this.app.user && this.app.user.id === u.id ? `<span class="tag ok">${esc(t("signed_in"))}</span>` : ""}${icon("chevron")}</span></button>`).join("") +
          this.btn("add-user", `${icon("plus")} ${esc(t("add_user"))}`);
      case "compat": {
        const c = s.compat, m = d.modules || { anyps5: { installed: false } };
        return this.toggle("compat", t("compat_steam"), c.steam, 'data-k="steam"') +
          this.toggle("compat", t("compat_native"), c.native, 'data-k="native"') +
          this.toggle("compat", t("compat_emulators"), c.emulators, 'data-k="emulators"') +
          (m.anyps5.installed ? this.toggle("compat", t("compat_anyps5"), c.anyps5, 'data-k="anyps5"') : this.row(t("compat_anyps5"), esc(t("not_installed")))) +
          `<p class="note">${esc(t("compat_note"))}</p>`;
      }
      case "datetime": {
        const td = d.td;
        let h = this.row(t("current_time"), esc(timeNow()));
        if (td && td.available) h += this.toggle("ntp", t("auto_time"), td.ntp) + this.btn("timezone", esc(t("time_zone")), esc(td.timezone || "—"));
        else h += this.row(t("time_zone"), esc(t("unavailable")));
        return h + this.toggle("set", t("clock_24h"), s.clock_24h, 'data-k="clock_24h"');
      }
      case "power": {
        const rest = s.rest_after ? t("after_min", { m: s.rest_after }) : t("never");
        return this.btn("rest", esc(t("rest_after")), esc(rest)) +
          this.btn("restart-shell", esc(t("restart_shell"))) +
          this.btn("reboot", esc(t("restart"))) +
          this.btn("poweroff", esc(t("turn_off")));
      }
      case "system": {
        const i = d.info || {}, u = d.upd || { managed: false };
        let upd;
        if (!u.managed) upd = this.row(t("updates"), esc(t("updates_unmanaged")));
        else {
          const busy = /^(checking|downloading|working)$/.test(u.state);
          let label = t("check_updates"), act = "upd-check";
          let val = u.checked ? t("last_checked", { d: new Date(u.checked * 1000).toLocaleString(getLang(), { dateStyle: "short", timeStyle: "short" }) }) : "";
          if (busy) { label = t(u.state === "checking" ? "checking" : "downloading"); act = "noop"; val = ""; }
          else if (u.staged || u.state === "restart-needed") { label = t("restart_to_update", { v: (u.staged && u.staged.version) || "" }); act = "reboot"; val = ""; }
          else if (u.available) { label = t("download_update", { v: u.available.version || "" }); act = "upd-apply"; val = ""; }
          upd = this.btn(act, esc(label), esc(val), busy ? 'aria-busy="true"' : "") +
            (u.state === "failed" && u.error ? `<p class="note">${esc(t("update_failed"))}</p>` : "") +
            this.toggle("set", t("auto_updates"), s.auto_updates, 'data-k="auto_updates"') +
            (u.rollback ? this.btn("rollback", esc(t("rollback")), esc(u.rollback.version || "")) : "");
        }
        return this.row(t("os_version"), esc(u.booted && u.booted.version ? `AnyPC OS ${u.booted.version}` : i.os || "AnyPC OS")) + upd +
          this.h2(t("device")) + this.btn("hostname", esc(t("hostname")), esc(i.hostname || "—")) +
          this.row(t("cpu"), esc(i.cpu || "—")) + this.row(t("gpu"), esc((i.gpus || []).join(", ") || "—")) +
          this.row(t("memory"), esc(bytes(i.memory))) +
          this.h2(t("reset")) + this.btn("reset", esc(t("reset_settings"))) +
          ((this.app.data.state || {}).demo ? `<p class="note">${esc(t("demo_mode"))}</p>` : "");
      }
      case "access":
        return this.toggle("set", t("reduce_motion"), s.reduce_motion, 'data-k="reduce_motion"') +
          this.toggle("set", t("high_contrast"), s.high_contrast, 'data-k="high_contrast"') +
          this.toggle("set", t("boot_animation"), s.boot_animation, 'data-k="boot_animation"');
      case "language":
        return LANGS.map(([code, label]) => `<button type="button" class="srow" data-act="lang" data-v="${code}" aria-pressed="${code === getLang()}"><span>${esc(label)}</span>${code === getLang() ? icon("check") : ""}</button>`).join("");
    }
    return "";
  }

  // ---------- actions ----------
  async act(a, b) {
    const app = this.app, s = app.data.settings, d = this.d, v = b.dataset.v;
    const confirm = (title, text, label, danger) => dialog(app, { title, text, buttons: [{ label, value: true, primary: !danger, danger }, { label: t("cancel"), value: false }] });
    switch (a) {
      case "cat": { const first = this.el.querySelector(".pane button"); return first && first.focus({ preventScroll: true }); }
      case "noop": return;
      // display
      case "resolution": {
        const ds = d.displays || { outputs: [], mode: "auto" };
        const modes = [...new Set(ds.outputs.flatMap((o) => o.modes))];
        const pick = await choose(app, { title: t("resolution"), current: ds.mode,
          items: [{ value: "auto", label: t("automatic") }, ...modes.map((m) => ({ value: m, label: m.replace("x", " × ") }))] });
        if (pick == null || pick === ds.mode) return;
        if (!(await this.post("/api/displays", { mode: pick }, "displays"))) return;
        this.paint();
        if (await confirm(t("resolution"), t("restart_to_apply"), t("restart_shell"))) app.exitShell("restart-shell");
        return;
      }
      case "overscan": {
        const pick = await choose(app, { title: t("screen_fit"), current: s.overscan || 100, items: OVERSCAN.map((x) => ({ value: x, label: `${x}%` })) });
        if (pick != null) await app.saveSettings({ overscan: pick });
        return this.paint();
      }
      // sound
      case "vol-": case "vol+": case "mute": {
        const cur = d.audio || { volume: 0, muted: false };
        const body = a === "mute" ? { muted: !cur.muted } : { volume: cur.volume + (a === "vol+" ? 5 : -5) };
        await this.post("/api/audio", body, "audio");
        return this.paint();
      }
      case "output": {
        const outs = (d.audio && d.audio.outputs) || [];
        const pick = await choose(app, { title: t("output_device"), current: (outs.find((o) => o.default) || {}).id, items: outs.map((o) => ({ value: o.id, label: o.name })) });
        if (pick != null) await this.post("/api/audio", { output: pick }, "audio");
        return this.paint();
      }
      // network
      case "wifi-radio": await this.post("/api/network/wifi", { on: !(d.net && d.net.wifiEnabled) }, "net"); return this.paint();
      case "rescan": app.toast(t("searching")); await this.get("net", "/api/network?rescan=1"); return this.paint();
      case "wifi": {
        const w = d.net.wifi.find((x) => x.ssid === v);
        if (!w) return;
        if (w.active || w.saved) {
          const dev = d.net.devices.find((x) => x.type === "wifi");
          const choice = await dialog(app, { title: w.ssid, buttons: [
            w.active ? { label: t("disconnect"), value: "disconnect", primary: true } : { label: t("connect"), value: "connect", primary: true },
            { label: t("forget"), value: "forget", danger: true }, { label: t("cancel"), value: null }] });
          if (choice === "disconnect" && dev) await this.post("/api/network/disconnect", { device: dev.device }, "net");
          if (choice === "forget") await this.post("/api/network/forget", { name: w.ssid }, "net");
          if (choice === "connect") await this.connect(w.ssid, null);
          return this.paint();
        }
        let pw = null;
        if (w.secure) {
          pw = await keyboard(app, { title: t("wifi_password", { ssid: w.ssid }), secret: true, minLength: 8, maxLength: 63 });
          if (pw == null) return;
        }
        await this.connect(w.ssid, pw);
        return this.paint();
      }
      case "forget": {
        if (await confirm(t("forget_q", { name: v }), "", t("forget"), true)) await this.post("/api/network/forget", { name: v }, "net");
        return this.paint();
      }
      // bluetooth
      case "bt-power": await this.post("/api/bluetooth/power", { on: !(d.bt && d.bt.powered) }, "bt"); return this.paint();
      case "bt-scan": await this.post("/api/bluetooth/scan", {}, "bt"); return this.paint();
      case "bt": {
        const x = d.bt.devices.find((y) => y.mac === v);
        if (!x) return;
        if (!x.paired) {
          app.toast(t("pairing", { name: x.name }));
          if (await this.post("/api/bluetooth/pair", { mac: x.mac }, "bt")) app.toast(t("paired_ok", { name: x.name }));
          return this.paint();
        }
        const choice = await dialog(app, { title: x.name, buttons: [
          x.connected ? { label: t("disconnect"), value: "disconnect", primary: true } : { label: t("connect"), value: "connect", primary: true },
          { label: t("remove"), value: "remove", danger: true }, { label: t("cancel"), value: null }] });
        if (choice) await this.post(`/api/bluetooth/${choice}`, { mac: x.mac }, "bt");
        return this.paint();
      }
      // controllers
      case "padtest": return padTester(app, +v);
      case "go-bt": {
        this.cat = "bluetooth";
        this.markCats();
        await this.load();
        const f = this.el.querySelector(".pane button");
        return f && f.focus({ preventScroll: true });
      }
      // users
      case "add-user": return app.show("setup", { addOnly: true });
      case "user": return this.editUser(v);
      // compatibility & plain toggles
      case "compat": {
        await app.saveSettings({ compat: { [b.dataset.k]: b.getAttribute("aria-checked") !== "true" } });
        await app.loadGames(true);
        return this.paint();
      }
      case "set": await app.saveSettings({ [b.dataset.k]: b.getAttribute("aria-checked") !== "true" }); return this.paint();
      // date & time
      case "ntp": await this.post("/api/timedate", { ntp: !(d.td && d.td.ntp) }, "td"); return this.paint();
      case "timezone": {
        const zones = await api.get("/api/timezones").catch(() => []);
        const pick = await choose(app, { title: t("time_zone"), current: d.td.timezone, items: zones.map((z) => ({ value: z, label: z.replace(/_/g, " ") })) });
        if (pick != null) await this.post("/api/timedate", { timezone: pick }, "td");
        return this.paint();
      }
      // power
      case "rest": {
        const pick = await choose(app, { title: t("rest_after"), current: s.rest_after, items: REST.map((m) => ({ value: m, label: m ? t("after_min", { m }) : t("never") })) });
        if (pick != null) await app.saveSettings({ rest_after: pick });
        return this.paint();
      }
      case "restart-shell": if (await confirm(t("restart_shell"), t("restart_shell_text"), t("restart_shell"))) app.exitShell("restart-shell"); return;
      case "reboot": case "poweroff": {
        const label = a === "reboot" ? t("restart") : t("turn_off");
        if (!(await confirm(label, app.data.running.running ? t("game_will_close") : "", label, a === "poweroff"))) return;
        const r = await this.post(`/api/power/${a}`, {});
        if (r && r.demo) app.toast(t("demo_only"));
        return;
      }
      // system
      case "upd-check": app.toast(t("checking")); await this.post("/api/updates/check", {}, "upd"); return this.paint();
      case "upd-apply": await this.post("/api/updates/apply", {}, "upd"); return this.paint();
      case "rollback": if (await confirm(t("rollback"), t("rollback_text"), t("rollback"), true)) await this.post("/api/updates/rollback", {}, "upd"); return this.paint();
      case "hostname": {
        const name = await keyboard(app, { title: t("hostname"), value: (d.info && d.info.hostname) || "", maxLength: 63, minLength: 1 });
        if (name == null) return;
        if (!HOSTNAME_RE.test(name)) return app.toast(t("hostname_rule"));
        if (await this.post("/api/hostname", { name })) await this.get("info", "/api/system");
        return this.paint();
      }
      case "reset": {
        if (!(await confirm(t("reset_settings"), t("reset_text"), t("reset"), true))) return;
        const r = await this.post("/api/settings/reset", {});
        if (r) { app.applySettings(r); await app.loadGames(true); this.renderCats(); }
        return this.paint();
      }
      // language
      case "lang": {
        await app.saveSettings({ language: v });
        const fresh = new SettingsScreen(app, { cat: "language" });
        this.dispose();
        this.el.replaceWith(fresh.el);
        app.stack[app.stack.indexOf(this)] = fresh;
        setTimeout(() => { const n = fresh.el.querySelector(`[data-act="lang"][data-v="${v}"]`); n && n.focus({ preventScroll: true }); }, 200);
        return;
      }
    }
  }

  async connect(ssid, password) {
    this.app.toast(t("connecting", { ssid }));
    const r = await this.post("/api/network/connect", { ssid, password }, "net");
    if (r) this.app.toast(t("connected_to", { ssid }));
  }

  async editUser(id) {
    const app = this.app;
    const u = app.data.users.find((x) => x.id === id);
    if (!u) return;
    const choice = await dialog(app, { title: u.name, buttons: [
      { label: t("rename"), value: "rename", primary: true }, { label: t("colour"), value: "color" },
      { label: t("delete"), value: "delete", danger: true }, { label: t("cancel"), value: null }] });
    if (choice === "rename") {
      const name = await keyboard(app, { title: t("player_name"), value: u.name, maxLength: 16, minLength: 1 });
      if (name && name.trim()) await this.post(`/api/users/${encodeURIComponent(id)}`, { name: name.trim() });
    } else if (choice === "color") {
      const c = await choose(app, { title: t("colour"), current: u.color, items: COLORS.map((x) => ({ value: x, label: t("color_" + x) })) });
      if (c) await this.post(`/api/users/${encodeURIComponent(id)}`, { color: c });
    } else if (choice === "delete") {
      const ok = await dialog(app, { title: t("delete_user_q", { name: u.name }), text: t("delete_user_text"),
        buttons: [{ label: t("delete"), value: true, danger: true }, { label: t("cancel"), value: false }] });
      if (ok && await this.post(`/api/users/${encodeURIComponent(id)}/delete`, {})) {
        app.data.users = await api.get("/api/users");
        if (app.user && app.user.id === id) { app.user = null; return app.afterBoot(); }
      }
    }
    app.data.users = await api.get("/api/users");
    if (app.user) app.user = app.data.users.find((x) => x.id === app.user.id) || app.user;
    this.paint();
  }
}

// Live view of every button and stick on one controller.
// Hold B (or press Esc on a keyboard) to leave, so B itself can be tested.
function padTester(app, index) {
  const names = ["A", "B", "X", "Y", "LB", "RB", "LT", "RT", "View", "Menu", "L3", "R3", "↑", "↓", "←", "→"];
  return new Promise((resolve) => {
    let raf, heldSince = 0;
    const layer = {
      el: el(`<section class="overlay layer" role="dialog" aria-modal="true" aria-label="${esc(t("test_controller"))}">
<div class="shade" aria-hidden="true"></div>
<div class="dlg" style="width:46rem"><h1>${esc(t("test_controller"))}</h1>
<div class="padtest">${names.map((n, i) => `<span data-b="${i}">${esc(n)}</span>`).join("")}</div>
<div class="sticks"><span class="stick"><i data-s="0"></i></span><span class="stick"><i data-s="1"></i></span></div>
<p>${esc(t("test_hint"))}</p>
<div class="dlg-btns"><button type="button" class="btn" data-act="rumble">${esc(t("vibrate"))}</button><button type="button" class="btn primary" data-act="close" data-autofocus>${esc(t("done"))}</button></div></div>
</section>`),
      done: resolve,
      dispose() { cancelAnimationFrame(raf); },
      padOnly: true, // A and B on the pad are under test, not used for the UI
      onBack() { return document.body.dataset.input === "pad"; },
      act(a) {
        if (a === "close") app.closeLayer(layer, null);
        if (a === "rumble") {
          const p = (navigator.getGamepads() || [])[index];
          const v = p && p.vibrationActuator;
          if (v && v.playEffect) v.playEffect("dual-rumble", { duration: 400, strongMagnitude: 1, weakMagnitude: 0.6 }).catch(() => {});
          else app.toast(t("no_vibration"));
        }
      },
    };
    const frame = (ts) => {
      raf = requestAnimationFrame(frame);
      const p = (navigator.getGamepads() || [])[index];
      if (!p) return;
      layer.el.querySelectorAll("[data-b]").forEach((n) => n.classList.toggle("on", !!(p.buttons[+n.dataset.b] && p.buttons[+n.dataset.b].pressed)));
      [[0, 1], [2, 3]].forEach(([x, y], i) => {
        const dot = layer.el.querySelector(`[data-s="${i}"]`);
        dot.style.transform = `translate(${(p.axes[x] || 0) * 1.9}rem, ${(p.axes[y] || 0) * 1.9}rem)`;
      });
      const held = p.buttons[1] && p.buttons[1].pressed;
      if (held) { heldSince = heldSince || ts; if (ts - heldSince > 1500) app.closeLayer(layer, null); } else heldSince = 0;
    };
    app.openLayer(layer);
    raf = requestAnimationFrame(frame);
  });
}
