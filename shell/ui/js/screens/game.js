import { el, esc, cover, heroBackground, glyphFor, playtime, date, sourceLabel, backButton, clock, hints } from "../ui.js";
import { icon } from "../icons.js";
import { t } from "../i18n.js";

export class GameScreen {
  constructor(app, { id }) {
    this.app = app;
    this.id = id;
    this.el = el(`<section class="screen hub"></section>`);
    this.render();
  }

  game() { return this.app.data.games.find((g) => g.id === this.id); }

  render() {
    const g = this.game();
    if (!g) { this.el.innerHTML = `<div class="bg"></div><header class="topbar">${backButton(t("back"))}</header>`; return; }
    const r = this.app.data.running;
    const running = r.running && r.id === g.id;
    const other = r.running && r.id !== g.id;
    this.el.setAttribute("aria-label", g.name);
    this.el.innerHTML = `<div class="hero-bg" aria-hidden="true" style="background:${heroBackground(g).replace("80% 45%", "82% 30%")}"></div>
<svg class="hero-glyph" viewBox="0 0 100 100" aria-hidden="true" style="top:2.5rem;right:3.75rem;width:27.5rem;height:27.5rem">${glyphFor(g).replace(/0\.55/g, "0.35")}</svg>
<div class="hub-fade" aria-hidden="true"></div>
<header class="topbar">${backButton(t("home"))}${clock()}</header>
<section class="hub-head">
<div class="hub-title"><span class="cover">${cover(g)}</span>
<div style="display:flex;flex-direction:column;gap:.4rem"><p class="eyebrow">${esc(g.genre)} · ${esc(sourceLabel(g))}</p><h1>${esc(g.name)}</h1></div></div>
<div class="actions">
${running ? `<button type="button" class="btn primary" data-act="quit" data-autofocus>${icon("stop")}${esc(t("quit_game"))}</button>`
    : `<button type="button" class="btn primary" data-act="play" data-autofocus ${other ? "disabled" : ""}>${icon("play")}${esc(t("play"))}</button>`}
</div>
<p class="status" role="status">${running ? esc(t("launched", { name: g.name })) : other ? esc(t("now_playing") + ": " + r.name) : ""}</p>
</section>
<section class="panels">
<div class="panel"><h2>${esc(t("time_played"))}</h2><span class="big">${esc(playtime(g))}</span></div>
<div class="panel"><h2>${esc(t("last_played"))}</h2><span class="big" style="font-size:2rem">${esc(date(g.lastPlayed))}</span></div>
<div class="panel"><h2>${esc(t("source"))}</h2><div class="kv"><div><span>${esc(t("source"))}</span><span>${esc(sourceLabel(g))}</span></div><div><span>${esc(t("genre"))}</span><span>${esc(g.genre)}</span></div></div></div>
</section>
${hints([["A", t("select")], ["B", t("back")]])}`;
  }

  on(evt) { if (evt === "running") { this.render(); this.app.focusIn(this); } }
  onShow() { this.render(); }

  act(a) {
    const g = this.game();
    if (a === "play" && g) this.app.launch(g);
    if (a === "quit") this.app.quitGame();
  }
}
