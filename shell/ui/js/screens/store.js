import { api } from "../api.js";
import { t } from "../i18n.js";
import { el, esc, background, hints } from "../ui.js";
import { icon } from "../icons.js";
import { topbar, topbarAct } from "./home.js";

export class StoreScreen {
  constructor(app) {
    this.app = app;
    this.name = "store";
    this.el = el('<section class="screen storefront"></section>');
    this.el.innerHTML = background(19, true) + topbar(app, "store") +
      '<main class="store-body" data-scroll></main>' + hints([["A", t("select")], ["B", t("back")]]);
    this.body = this.el.querySelector("main");
    this.body.setAttribute("aria-label", t("store"));
    this.loading = false;
    this.refresh();
    this.timer = setInterval(() => this.refresh(), 2200);
  }

  async refresh() {
    if (this.loading || this.disposed) return;
    this.loading = true;
    try {
      const data = await api.get("/api/catalog");
      const signature = JSON.stringify(data);
      if (this.disposed || signature === this.signature) return;
      const focus = this.body.contains(document.activeElement) ? document.activeElement.dataset.key : null;
      this.signature = signature;
      const busy = data.job.state === "working";
      const button = (key, action, caption) =>
        `<button type="button" class="btn" data-act="catalog" data-key="${esc(key + "/" + action)}" data-id="${esc(key)}" data-op="${action}" ${busy ? "disabled" : ""}>${esc(t(caption))}</button>`;
      const card = item => `<article class="store-item store-${esc(item.id)}">
        <span class="store-glyph" aria-hidden="true">${icon(({steam:"library", kart:"play", vlc:"volume"})[item.id] || "play")}</span>
        <h2>${esc(item.name)}</h2><p>${esc(t(item.description))}</p><div class="actions">
        ${item.installed ? button(item.id, "open", "store_open") + button(item.id, "update", "store_update") :
          button(item.id, "install", "store_install")}</div></article>`;
      const progress = data.job.state !== "idle" ? `<p role="status">${esc(t("store_" + data.job.state))}</p>` : "";
      this.body.innerHTML = `<h1>${esc(t("store"))}</h1><h2>${esc(t("store_apps"))}</h2>
        <div class="store-grid">${data.items.filter(item => !["store_engine", "store_tool"].includes(item.description)).map(card).join("")}</div>${progress}
        <h2>${esc(t("compat_anyps5"))}</h2><p>${esc(t("store_import_help"))}</p>${button("usb","scan","store_usb")}
        ${data.imports.map(item => `<div class="store-import"><span>${esc(item.name)}</span>${button(item.id,"import","store_import")}</div>`).join("")}
        <h2>${esc(t("store_compat"))}</h2>
        <div class="store-grid">${data.items.filter(item => ["store_engine", "store_tool"].includes(item.description)).map(card).join("")}</div>`;
      if (focus) this.body.querySelector(`[data-key="${CSS.escape(focus)}"]`)?.focus({preventScroll:true});
      if (data.job.state === "done") await this.app.loadGames(true);
    } catch {
      if (!this.disposed) this.body.textContent = t("store_failed");
      this.signature = null;
    } finally { this.loading = false; }
  }

  async act(action, button) {
    if (topbarAct(this.app, action)) return;
    if (action !== "catalog") return;
    button.disabled = true;
    try {
      await api.post("/api/catalog/action", {id:button.dataset.id, action:button.dataset.op});
      this.signature = null;
      await this.refresh();
    } catch {
      button.disabled = false;
      this.app.toast(t("store_failed"));
    }
  }

  dispose() { this.disposed = true; clearInterval(this.timer); }
}
