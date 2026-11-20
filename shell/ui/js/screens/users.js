import { el, esc, background, avatar, clock, hints } from "../ui.js";
import { icon, mark } from "../icons.js";
import { t } from "../i18n.js";

export class UsersScreen {
  constructor(app) {
    this.app = app;
    this.noMenu = true;
    const users = app.data.users.map((u, i) => `<button type="button" class="user" data-act="pick" data-id="${esc(u.id)}" ${i === 0 ? "data-autofocus" : ""}>
${avatar(u, "")}<span>${esc(u.name)}</span></button>`).join("");
    this.el = el(`<section class="screen users" aria-label="${esc(t("whos_playing"))}">
${background(5)}
<header class="topbar"><span class="brand">${mark("2.1rem")}AnyPC OS</span><span class="right">${clock()}</span></header>
<div class="center">
<h1 class="title-wide">${esc(t("whos_playing"))}</h1>
<div class="user-row">${users}
<button type="button" class="user" data-act="add"><span class="add">${icon("plus")}</span><span>${esc(t("add_user"))}</span></button>
</div>
</div>
${hints([["A", t("select")]])}
</section>`);
    // avatar() sizes inline; users screen sizes them with CSS instead.
    this.el.querySelectorAll(".user .avatar").forEach((a) => a.removeAttribute("style"));
  }

  act(a, b) {
    if (a === "pick") this.app.signIn(this.app.data.users.find((u) => u.id === b.dataset.id));
    if (a === "add") this.app.show("setup", { addOnly: true });
  }

  onBack() { return true; }
}
