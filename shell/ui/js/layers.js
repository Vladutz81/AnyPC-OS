// Modal layers on top of the screens: dialogs, choice lists and the
// on-screen keyboard. Each returns a Promise and closes itself.
import { el, esc } from "./ui.js";
import { icon } from "./icons.js";
import { t } from "./i18n.js";

// A message with buttons. Resolves with the chosen button's value, or null on Back.
export function dialog(app, { title, text = "", buttons = [{ label: "OK", value: true, primary: true }] }) {
  return new Promise((resolve) => {
    const layer = {
      el: el(`<section class="overlay layer" role="alertdialog" aria-modal="true" aria-label="${esc(title)}">
<div class="shade" aria-hidden="true"></div>
<div class="dlg"><h1>${esc(title)}</h1>${text ? `<p>${esc(text)}</p>` : ""}
<div class="dlg-btns">${buttons.map((b, i) => `<button type="button" class="btn${b.primary ? " primary" : ""}${b.danger ? " danger" : ""}" data-act="pick" data-i="${i}" ${i === 0 ? "data-autofocus" : ""}>${esc(b.label)}</button>`).join("")}</div></div>
</section>`),
      act(a, btn) { if (a === "pick") app.closeLayer(layer, buttons[+btn.dataset.i].value); },
      done: resolve,
    };
    app.openLayer(layer);
  });
}

// Pick one item from a (possibly long) list. Resolves with the value or null.
export function choose(app, { title, items, current }) {
  return new Promise((resolve) => {
    const layer = {
      el: el(`<section class="overlay layer" role="dialog" aria-modal="true" aria-label="${esc(title)}">
<div class="shade" aria-hidden="true"></div>
<div class="dlg list"><h1>${esc(title)}</h1><div class="dlg-list" data-scroll data-vtrap>${items.map((it, i) =>
        `<button type="button" class="srow" data-act="pick" data-i="${i}" aria-pressed="${it.value === current}" ${it.value === current ? "data-autofocus" : ""}><span>${esc(it.label)}</span>${it.value === current ? icon("check") : (it.hint ? `<span class="v">${esc(it.hint)}</span>` : "")}</button>`).join("")}</div></div>
</section>`),
      act(a, btn) { if (a === "pick") app.closeLayer(layer, items[+btn.dataset.i].value); },
      done: resolve,
    };
    app.openLayer(layer);
  });
}

const ROWS = {
  abc: ["1234567890", "qwertyuiop", "asdfghjkl'", "zxcvbnm,.-"],
  sym: ["1234567890", "!@#$%^&*()", "_=+[]{};:\"", "<>/?\\|`~€£"],
};

// On-screen keyboard for gamepad users. Resolves with the text, or null on Back.
export function keyboard(app, { title, value = "", secret = false, maxLength = 63, minLength = 0 }) {
  return new Promise((resolve) => {
    let text = value, shift = false, page = "abc", show = !secret;
    const layer = {
      el: el(`<section class="overlay layer" role="dialog" aria-modal="true" aria-label="${esc(title)}">
<div class="shade" aria-hidden="true"></div>
<div class="osk"><h1>${esc(title)}</h1><div class="osk-field" aria-live="polite"></div><div class="osk-keys" data-rows></div></div>
</section>`),
      done: resolve,
      act(a, b) {
        if (a === "key") { if (text.length < maxLength) { text += b.dataset.k; if (shift) { shift = false; render(true); } } }
        else if (a === "del") text = text.slice(0, -1);
        else if (a === "space") { if (text.length < maxLength) text += " "; }
        else if (a === "shift") { shift = !shift; return render(true); }
        else if (a === "page") { page = page === "abc" ? "sym" : "abc"; return render(true); }
        else if (a === "show") { show = !show; }
        else if (a === "ok") { if (text.length >= minLength) app.closeLayer(layer, text); return; }
        field();
      },
      // A real keyboard types straight into the field.
      onKey(e) {
        if (e.ctrlKey || e.altKey || e.metaKey) return false;
        if (e.key === "Backspace") { text = text.slice(0, -1); field(); return true; }
        if (e.key === "Enter") {
          if (text.length >= minLength) app.closeLayer(layer, text);
          return true;
        }
        if (e.key.length === 1) {
          if (text.length < maxLength) text += e.key;
          field();
          return true;
        }
        return false;
      },
      // Bumpers: LB deletes, RB adds a space, like most console keyboards.
      onTab(d) { if (d < 0) text = text.slice(0, -1); else if (text.length < maxLength) text += " "; field(); },
    };
    const field = () => {
      const shown = show ? esc(text) : "•".repeat(text.length);
      layer.el.querySelector(".osk-field").innerHTML = `<span>${shown}</span><i class="caret"></i>`;
      const ok = layer.el.querySelector('[data-act="ok"]');
      if (ok) ok.disabled = text.length < minLength;
    };
    const render = (keepFocus) => {
      const focused = keepFocus && document.activeElement && document.activeElement.dataset;
      const fk = focused ? (focused.k ? `[data-k="${CSS.escape(shift ? focused.k.toUpperCase() : focused.k.toLowerCase())}"]` : `[data-act="${focused.act}"]`) : null;
      const rows = ROWS[page].map((r) => `<div class="osk-row">${[...r].map((c) => {
        const k = page === "abc" && shift ? c.toUpperCase() : c;
        return `<button type="button" class="osk-k" data-act="key" data-k="${esc(k)}">${esc(k)}</button>`;
      }).join("")}</div>`).join("");
      layer.el.querySelector(".osk-keys").innerHTML = rows + `<div class="osk-row">
<button type="button" class="osk-k wide" data-act="shift" aria-pressed="${shift}">⇧</button>
<button type="button" class="osk-k wide" data-act="page">${page === "abc" ? "#+=" : "abc"}</button>
<button type="button" class="osk-k space" data-act="space" aria-label="Space">␣</button>
<button type="button" class="osk-k wide" data-act="del" aria-label="Delete">⌫</button>
${secret ? `<button type="button" class="osk-k wide" data-act="show" aria-label="Show">${icon("search")}</button>` : ""}
<button type="button" class="osk-k ok" data-act="ok">${esc(t("done"))}</button></div>`;
      field();
      const again = fk && layer.el.querySelector(fk);
      (again || layer.el.querySelector('[data-act="key"]')).focus({ preventScroll: true });
    };
    app.openLayer(layer);
    render(false);
  });
}
