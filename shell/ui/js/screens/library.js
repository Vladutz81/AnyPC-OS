import { el, esc, background, cover, playtime, hints } from "../ui.js";
import { t } from "../i18n.js";
import { topbar, topbarAct, sortRecent } from "./home.js";

const FILTERS = [
  ["all", "all", () => true],
  ["recent", "recent", (g) => g.lastPlayed > 0],
  ["steam", "steam", (g) => g.source === "steam"],
  ["native", "native", (g) => g.source !== "steam"],
];

export class LibraryScreen {
  constructor(app) {
    this.app = app;
    this.name = "library";
    this.f = 0;
    this.el = el(`<section class="screen library" aria-label="${esc(t("library"))}"></section>`);
    this.el.addEventListener("focusin", (e) => this.scrollTo(e.target));
    this.render();
  }

  list() {
    const [, , fn] = FILTERS[this.f];
    const gs = this.app.data.games.filter(fn);
    return FILTERS[this.f][0] === "recent" ? sortRecent(gs) : [...gs].sort((a, b) => a.name.localeCompare(b.name));
  }

  render(keepFocusOnChip = false) {
    const gs = this.list();
    this.el.innerHTML = `${background(41, true)}
${topbar(this.app, "library")}
<div class="filters"><div class="row" role="tablist" aria-label="Filter">${FILTERS.map(([id, key], i) =>
      `<button type="button" role="tab" class="chip" data-act="filter" data-i="${i}" aria-selected="${i === this.f}">${esc(t(key))}</button>`).join("")}</div>
<span class="count">${esc(t("n_games", { n: gs.length }))}</span></div>
<div class="grid-wrap"><div class="grid">${gs.map((g, i) => `<button type="button" class="gcard" data-act="open" data-id="${esc(g.id)}" ${i === 0 ? "data-autofocus" : ""}>
<span class="cover">${cover(g)}</span><span class="n">${esc(g.name)}</span><span class="s">${esc(playtime(g))}</span></button>`).join("")}</div></div>
${hints([["LB", ""], ["RB", t("switch_tab")], ["A", t("select")], ["B", t("back")]])}`;
    if (keepFocusOnChip) {
      const chip = this.el.querySelector(`.chip[data-i="${this.f}"]`);
      requestAnimationFrame(() => chip && chip.focus({ preventScroll: true }));
    }
  }

  // Keep the focused card in view by sliding the grid.
  scrollTo(target) {
    const card = target.closest(".gcard");
    const grid = this.el.querySelector(".grid");
    if (!card || !grid) return;
    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const rowH = card.offsetHeight + 1.6 * rem;
    const row = Math.round(card.offsetTop / rowH);
    grid.style.transform = `translateY(${-Math.max(0, row - 1) * rowH}px)`;
  }

  act(a, b) {
    if (topbarAct(this.app, a)) return;
    if (a === "filter") { this.f = +b.dataset.i; this.render(true); }
    if (a === "open") this.app.show("game", { id: b.dataset.id });
  }

  onTab(d) {
    this.f = (this.f + d + FILTERS.length) % FILTERS.length;
    this.render();
    this.app.focusIn(this);
  }
}
