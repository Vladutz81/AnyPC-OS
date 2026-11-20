import { el, esc, background } from "../ui.js";
import { icon, mark } from "../icons.js";
import { t, LANGS, getLang } from "../i18n.js";
import { api } from "../api.js";
import { keyboard } from "../layers.js";

const COLORS = ["blue", "teal", "violet", "orange"];

// First start: language, network, controller, profile. With {addOnly} only the profile step.
export class SetupScreen {
  constructor(app, params = {}) {
    this.app = app;
    this.noMenu = !params.addOnly;
    this.addOnly = !!params.addOnly;
    this.steps = this.addOnly ? ["profile"] : ["language", "network", "controller", "profile", "ready"];
    this.i = 0;
    this.name = "";
    this.color = COLORS[app.data.users.length % COLORS.length];
    this.el = el(`<section class="screen" aria-label="Setup">${background(51)}<div class="setup"></div></section>`);
    this.box = this.el.querySelector(".setup");
    this.render();
  }

  get step() { return this.steps[this.i]; }

  async render() {
    const stepList = this.addOnly ? "" : `<ol aria-label="Steps">${this.steps.map((s, i) =>
      `<li class="${i < this.i ? "done" : i === this.i ? "now" : ""}" ${i === this.i ? 'aria-current="step"' : ""}><b>${i < this.i ? icon("check") : i + 1}</b>${esc(t("step_" + s))}</li>`).join("")}</ol>`;
    this.box.innerHTML = `<aside class="steps"><span class="brand">${mark("2.5rem")}AnyPC OS</span>${stepList}</aside>
<div class="sbox">${await this.body()}</div>`;
    this.app.focusIn(this);
  }

  nav(nextLabel = t("next")) {
    const showBack = this.i > 0 || this.addOnly;
    return `<div class="navrow"><button type="button" class="btn" data-act="prev" style="visibility:${showBack ? "visible" : "hidden"}">${esc(t("back"))}</button>
<button type="button" class="btn primary" data-act="next" ${this.step === "language" ? "" : "data-autofocus"}>${esc(nextLabel)}</button></div>`;
  }

  async body() {
    const cur = getLang();
    if (this.step === "language") {
      return `<h1>${esc(t("setup_language"))}</h1><div class="opts">${LANGS.map(([code, label]) =>
        `<button type="button" class="opt" data-act="lang" data-v="${code}" aria-pressed="${code === cur}" ${code === cur ? "data-autofocus" : ""}><span>${esc(label)}</span>${code === cur ? icon("check") : ""}</button>`).join("")}</div>${this.nav()}`;
    }
    if (this.step === "network") {
      let status = t("unavailable");
      try {
        const n = await api.get("/api/network");
        const on = (n.devices || []).find((d) => d.state === "connected");
        status = on ? `${t("connected")}: ${esc(on.connection || on.device)}` : t("not_connected");
      } catch (e) { /* keep "unavailable" */ }
      return `<h1>${esc(t("setup_network"))}</h1><p>${esc(t("setup_network_text"))}</p>
<div class="srow"><span style="display:flex;align-items:center;gap:.8rem">${icon("ethernet")}${esc(t("network"))}</span><span class="v">${status}</span></div>${this.nav()}`;
    }
    if (this.step === "controller") {
      const n = this.app.input.connectedPads().length;
      return `<h1>${esc(t("setup_controller"))}</h1>
<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.4rem;text-align:center">
<span class="padpulse">${icon("pad")}</span><p>${esc(t("setup_controller_text"))}</p><p data-pads>${esc(t("gamepads_found", { n }))}</p></div>${this.nav()}`;
    }
    if (this.step === "profile") {
      return `<h1>${esc(t("setup_profile"))}</h1>
<div style="display:flex;align-items:center;gap:2.25rem">
<span class="avatar c-${this.color}" data-av style="width:8.75rem;height:8.75rem;font-size:3rem;box-shadow:var(--focus)">${esc((this.name.trim()[0] || "P").toUpperCase())}</span>
<div style="flex:1;display:flex;flex-direction:column;gap:1rem">
<label for="pname" style="font-size:1rem;color:var(--muted)">${esc(t("player_name"))}</label>
<input id="pname" class="field" type="text" maxlength="16" autocomplete="off" value="${esc(this.name)}" data-act="name" data-autofocus>
<span style="font-size:1rem;color:var(--muted)">${esc(t("colour"))}</span>
<div class="swatches">${COLORS.map((c) => `<button type="button" class="swatch c-${c}" data-act="color" data-v="${c}" aria-label="${c}" aria-pressed="${c === this.color}"></button>`).join("")}</div>
</div></div>${this.nav(this.addOnly ? t("finish") : t("next"))}`;
    }
    return `<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.4rem;text-align:center">
<span style="filter:drop-shadow(0 0 2rem rgba(170,205,255,.8))">${mark("7.5rem")}</span>
<h1>${esc(t("welcome", { name: this.user ? this.user.name : "" }))}</h1><p>${esc(t("ready"))}</p>
<button type="button" class="btn primary" data-act="start" data-autofocus>${icon("play")}${esc(t("start"))}</button></div>`;
  }

  onPad() {
    const p = this.el.querySelector("[data-pads]");
    if (p) p.textContent = t("gamepads_found", { n: this.app.input.connectedPads().length });
  }

  async act(a, b) {
    if (a === "name") {
      if (document.body.dataset.input !== "pad") return; // typing on a real keyboard
      const input = this.el.querySelector("#pname");
      const v = await keyboard(this.app, { title: t("player_name"), value: input.value, maxLength: 16 });
      if (v != null) {
        input.value = v;
        this.name = v;
        this.el.querySelector("[data-av]").textContent = (v.trim()[0] || "P").toUpperCase();
      }
      return;
    }
    if (a === "lang") {
      await this.app.saveSettings({ language: b.dataset.v });
      return this.render();
    }
    if (a === "color") {
      this.name = this.el.querySelector("#pname").value;
      this.color = b.dataset.v;
      this.el.querySelectorAll(".swatch").forEach((s) => s.setAttribute("aria-pressed", String(s.dataset.v === this.color)));
      const av = this.el.querySelector("[data-av]");
      av.className = `avatar c-${this.color}`;
      return;
    }
    if (a === "prev") {
      if (this.i === 0 && this.addOnly) return this.app.back();
      this.i = Math.max(0, this.i - 1);
      return this.render();
    }
    if (a === "next") {
      if (this.step === "profile") {
        const name = this.el.querySelector("#pname").value.trim() || "Player";
        try {
          this.user = await api.post("/api/users", { name, color: this.color });
          this.app.data.users = await api.get("/api/users");
        } catch (e) {
          return this.app.toast(t("error"));
        }
        if (this.addOnly) return this.app.signIn(this.user);
      }
      this.i = Math.min(this.steps.length - 1, this.i + 1);
      return this.render();
    }
    if (a === "start") this.app.signIn(this.user || this.app.data.users[0]);
  }

  onBack() {
    if (this.addOnly && this.i === 0) return false;
    if (this.i > 0) { this.i--; this.render(); }
    return true;
  }
}

// Keep the avatar initial in sync while typing.
document.addEventListener("input", (e) => {
  if (e.target.id !== "pname") return;
  const av = document.querySelector("[data-av]");
  if (av) av.textContent = (e.target.value.trim()[0] || "P").toUpperCase();
});
