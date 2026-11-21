import { el, esc, background, cover, heroBackground, glyphFor, playtime, avatar, clock, hints } from "../ui.js";
import { icon, mark } from "../icons.js";
import { t } from "../i18n.js";

export function sortRecent(games) {
  return [...games].sort((a, b) => (b.lastPlayed || 0) - (a.lastPlayed || 0) || a.name.localeCompare(b.name));
}

export function topbar(app, current) {
  const u = app.user || app.data.users[0] || { name: "?", color: "blue" };
  return `<header class="topbar">
<nav aria-label="Main">
<span aria-hidden="true">${mark("1.9rem")}</span>
<button type="button" class="tab" data-act="go-home" ${current === "home" ? 'aria-current="page"' : ""}>${esc(t("games"))}</button>
<button type="button" class="tab" data-act="go-library" ${current === "library" ? 'aria-current="page"' : ""}>${esc(t("library"))}</button>
<button type="button" class="tab" data-act="go-store" ${current === "store" ? 'aria-current="page"' : ""}>${esc(t("store"))}</button>
</nav>
<div class="right">
<button type="button" class="icon-btn" data-act="go-settings" aria-label="${esc(t("settings"))}">${icon("gear")}</button>
<button type="button" class="icon-btn" data-act="control" aria-label="${esc(t("control_center"))}">${icon("bell")}</button>
<button type="button" class="icon-btn" data-act="go-users" aria-label="${esc(u.name)}" style="padding:0;border:0;background:none">${avatar(u, "3rem")}</button>
${clock()}
</div></header>`;
}

export function topbarAct(app, a) {
  if (a === "go-home") { app.goHome(); return true; }
  if (a === "go-library") { app.top().name === "library" ? null : app.show("library"); return true; }
  if (a === "go-store") { if (app.top().name !== "store") app.show("store"); return true; }
  if (a === "go-settings") { app.show("settings"); return true; }
  if (a === "go-users") { app.show("users", {}, { reset: true }); return true; }
  return false;
}

export class HomeScreen {
  constructor(app) {
    this.app = app;
    this.name = "home";
    this.el = el(`<section class="screen home" aria-label="${esc(t("home"))}"></section>`);
    this.selected = null;
    this.render();
    this.el.addEventListener("focusin", (e) => {
      const tile = e.target.closest(".tile[data-id]");
      if (tile) this.select(tile.dataset.id);
      if (e.target.closest(".tile")) this.scrollTiles(e.target.closest(".tile"));
    });
  }

  games() { return sortRecent(this.app.data.games).slice(0, 10); }

  render() {
    const games = this.games();
    if (!this.selected || !games.find((g) => g.id === this.selected)) this.selected = games[0] && games[0].id;
    const tiles = games.map((g, i) => `<button type="button" class="tile${g.id === this.selected ? " sel" : ""}" data-act="open" data-id="${esc(g.id)}" aria-label="${esc(g.name)}" ${i === 0 ? "data-autofocus" : ""}>${cover(g)}</button>`).join("");
    const body = games.length ? `<section class="hero" aria-live="polite" data-group></section>` : `<div class="empty"><h1>${esc(t("no_games_title"))}</h1><p>${esc(t("no_games_text"))}</p></div>`;
    this.el.innerHTML = `<div class="hero-bg" aria-hidden="true"></div>
<svg class="hero-glyph" viewBox="0 0 100 100" aria-hidden="true"></svg>
<div class="hero-fade" aria-hidden="true"></div>
<div style="position:absolute;inset:0;opacity:.6" aria-hidden="true">${background(9).replace('<div class="bg" aria-hidden="true"></div>', "")}</div>
${topbar(this.app, "home")}
<div class="tiles" role="list">
<button type="button" class="tile lib" data-act="go-library" aria-label="${esc(t("library"))}" ${games.length ? "" : "data-autofocus"}>${icon("library")}</button>
${tiles}</div>
${body}
<section class="cards" aria-label="Activity"></section>
${hints([["A", t("select")], ["☰", t("menu")]])}`;
    if (!games.length) this.el.querySelector(".hero-bg").style.background = "radial-gradient(ellipse 70% 80% at 50% 40%, #2A62D6 0%, #0D2C78 36%, #041241 66%, #020718 100%)";
    this.renderHero();
    this.renderCards();
  }

  // Slide the tile row so the focused tile stays on screen.
  scrollTiles(tile) {
    const row = this.el.querySelector(".tiles");
    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const visible = 80 * rem - 3.5 * rem * 2;
    const big = 10.5 * rem;
    const idx = [...row.children].indexOf(tile);
    const left = idx * (7 + 1.1) * rem; // tiles before it are small
    const shift = Math.max(0, left + big - visible);
    row.style.transform = `translateX(${-shift}px)`;
  }

  select(id) {
    if (id === this.selected) return;
    this.selected = id;
    this.el.querySelectorAll(".tile.sel").forEach((x) => x.classList.remove("sel"));
    const tile = this.el.querySelector(`.tile[data-id="${CSS.escape(id)}"]`);
    tile && tile.classList.add("sel");
    this.renderHero();
  }

  current() { return this.app.data.games.find((g) => g.id === this.selected); }

  renderHero() {
    const g = this.current();
    const hero = this.el.querySelector(".hero");
    if (!g || !hero) return;
    this.el.querySelector(".hero-bg").style.background = heroBackground(g);
    this.el.querySelector(".hero-glyph").innerHTML = glyphFor(g).replace(/0\.55/g, "0.35");
    const running = this.app.data.running.running && this.app.data.running.id === g.id;
    hero.innerHTML = `<p class="eyebrow">${esc(g.genre)} · ${esc(playtime(g))}</p>
<h1>${esc(g.name)}</h1>
<div class="actions">
${running ? `<button type="button" class="btn primary" data-act="quit" data-entry>${icon("stop")}${esc(t("quit_game"))}</button>`
    : `<button type="button" class="btn primary" data-act="play" data-entry>${icon("play")}${esc(t("play"))}</button>`}
<button type="button" class="btn" data-act="hub">${esc(t("game_hub"))}</button>
</div>`;
  }

  renderCards() {
    const cards = this.el.querySelector(".cards");
    const r = this.app.data.running;
    const last = sortRecent(this.app.data.games).find((g) => g.lastPlayed);
    const st = this.app.data.state || {};
    let html = "";
    if (r.running) {
      const g = this.app.data.games.find((x) => x.id === r.id) || { name: r.name, hue: 220, id: r.id };
      html += `<button type="button" class="card" data-act="control"><span class="thumb">${cover(g)}</span><span class="txt"><span class="label">${esc(t("now_playing"))}</span><span>${esc(r.name)}</span></span></button>`;
    }
    if (last && (!r.running || last.id !== r.id)) {
      html += `<button type="button" class="card" data-act="open" data-id="${esc(last.id)}"><span class="thumb">${cover(last)}</span><span class="txt"><span class="label">${esc(t("continue"))}</span><span>${esc(last.name)}</span></span></button>`;
    }
    html += `<button type="button" class="card" data-act="go-settings"><span class="thumb">${icon("refresh")}</span><span class="txt"><span class="label">${esc(t("system"))}</span><span>${esc(t("up_to_date", { os: st.os || "AnyPC OS", v: st.version || "" }))}${st.demo ? " · demo" : ""}</span></span></button>`;
    cards.innerHTML = html;
  }

  on(evt) {
    if (evt === "running") { this.renderHero(); this.renderCards(); }
  }

  onShow() {
    // Play time may have changed while a game ran.
    const focusId = document.activeElement && document.activeElement.dataset && document.activeElement.dataset.id;
    this.render();
    if (focusId) this.restoreFocus = this.el.querySelector(`.tile[data-id="${CSS.escape(focusId)}"]`);
  }

  act(a, b) {
    if (topbarAct(this.app, a)) return;
    const g = this.current();
    if (a === "open") return this.app.show("game", { id: b.dataset.id });
    if (a === "hub" && g) return this.app.show("game", { id: g.id });
    if (a === "play" && g) return this.app.launch(g);
    if (a === "quit") return this.app.quitGame();
  }

  onTab(d) { if (d > 0) this.app.show("library"); }
  onBack() { return true; }
}
