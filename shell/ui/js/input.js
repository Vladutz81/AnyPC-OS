// One input layer for gamepad, keyboard and mouse, plus spatial navigation.

const FOCUSABLE = 'button:not([disabled]), a[href], input:not([disabled]), [tabindex="0"]';

export function focusables(root) {
  return [...root.querySelectorAll(FOCUSABLE)].filter((el) => {
    if (el.closest("[inert]")) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  });
}

// Move focus to the nearest focusable element in a direction.
export function moveFocus(root, dir) {
  let list = focusables(root);
  if (!list.length) return false;
  const cur = document.activeElement;
  // Vertical moves stay inside a column marked data-vtrap (settings pane, menus).
  const trap = cur && (dir === "up" || dir === "down") && cur.closest && cur.closest("[data-vtrap]");
  if (trap && root.contains(trap)) list = list.filter((e) => trap.contains(e));
  if (!cur || !root.contains(cur) || cur === document.body) {
    (root.querySelector("[data-autofocus]") || list[0]).focus({ preventScroll: true });
    return true;
  }
  const a = cur.getBoundingClientRect();
  const ax = a.left + a.width / 2, ay = a.top + a.height / 2;
  const horiz = dir === "left" || dir === "right";
  let best = null, bestScore = Infinity;
  for (const el of list) {
    if (el === cur) continue;
    const b = el.getBoundingClientRect();
    const bx = b.left + b.width / 2, by = b.top + b.height / 2;
    let primary, ortho, overlap;
    if (horiz) {
      if (dir === "right" ? bx <= ax + 1 : bx >= ax - 1) continue;
      primary = dir === "right" ? b.left - a.right : a.left - b.right;
      overlap = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      ortho = Math.abs(by - ay);
    } else {
      if (dir === "down" ? by <= ay + 1 : by >= ay - 1) continue;
      primary = dir === "down" ? b.top - a.bottom : a.top - b.bottom;
      overlap = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      ortho = Math.abs(bx - ax);
    }
    const score = Math.max(0, primary) + (overlap > 0 ? ortho * 0.3 : ortho * 2 + 200);
    if (score < bestScore) { bestScore = score; best = el; }
  }
  if (best) {
    // Entering a group (e.g. the hero actions) lands on its main control.
    const group = best.closest("[data-group]");
    if (group && !group.contains(cur)) {
      const entry = group.querySelector("[data-entry]");
      if (entry && list.includes(entry)) best = entry;
    }
    best.focus({ preventScroll: true });
    return true;
  }
  return false;
}

const DIRS = { ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right" };

export class Input {
  constructor(h) {
    this.h = h; // { move(dir), activate(), back(), menu(), tab(delta), any() }
    this.mode = "mouse";
    this.pads = {};
    this._frame = this._frame.bind(this);
    addEventListener("keydown", (e) => this._key(e));
    addEventListener("pointermove", (e) => this._pointer(e), { passive: true });
    addEventListener("pointerdown", () => { this._setMode("mouse"); h.any && h.any(); }, { passive: true });
    addEventListener("gamepadconnected", () => this._ensureLoop());
    this._ensureLoop();
  }

  _setMode(m) {
    if (this.mode !== m) { this.mode = m; document.body.dataset.input = m; }
  }

  _key(e) {
    const h = this.h;
    const inText = e.target && e.target.tagName === "INPUT" && /^(text|search)$/.test(e.target.type);
    this._setMode("kbd");
    if (h.any && h.any(e)) { e.preventDefault(); return; }
    if (DIRS[e.key]) {
      if (inText && (e.key === "ArrowLeft" || e.key === "ArrowRight")) return;
      if (e.target && e.target.type === "range" && (e.key === "ArrowLeft" || e.key === "ArrowRight")) return;
      e.preventDefault();
      h.move(DIRS[e.key]);
    } else if (e.key === "Enter" || (e.key === " " && !inText)) {
      e.preventDefault();
      h.activate();
    } else if (e.key === "Escape" || (e.key === "Backspace" && !inText)) {
      e.preventDefault();
      h.back();
    } else if (e.key === "Home" || e.key === "F1" || e.key === "ContextMenu") {
      e.preventDefault();
      h.menu();
    } else if (e.key === "PageUp" || e.key === "PageDown") {
      e.preventDefault();
      h.tab(e.key === "PageDown" ? 1 : -1);
    }
  }

  _pointer(e) {
    if (Math.abs(e.movementX) + Math.abs(e.movementY) < 2) return;
    this._setMode("mouse");
    const el = e.target.closest && e.target.closest(FOCUSABLE);
    if (el && document.activeElement !== el && !el.closest("[inert]")) el.focus({ preventScroll: true });
  }

  _ensureLoop() {
    if (!this._looping && navigator.getGamepads) { this._looping = true; requestAnimationFrame(this._frame); }
  }

  // Standard gamepad mapping: 0 A, 1 B, 4/5 bumpers, 8 back/select, 9 start, 12-15 d-pad, 16 guide.
  _frame(ts) {
    requestAnimationFrame(this._frame);
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    for (const p of pads) {
      if (!p || !p.connected) continue;
      const st = this.pads[p.index] || (this.pads[p.index] = { btn: [], dir: null, next: 0 });
      const pressed = (i) => !!(p.buttons[i] && p.buttons[i].pressed);
      const edge = (i) => { const now = pressed(i), was = st.btn[i]; st.btn[i] = now; return now && !was; };
      let any = false;
      if (edge(0)) { any = true; this._pad(() => this.h.activate()); }
      if (edge(1)) { any = true; this._pad(() => this.h.back()); }
      if (edge(16) || edge(9) || edge(8)) { any = true; this._pad(() => this.h.menu()); }
      if (edge(4)) { any = true; this._pad(() => this.h.tab(-1)); }
      if (edge(5)) { any = true; this._pad(() => this.h.tab(1)); }
      for (const i of [2, 3, 6, 7, 10, 11]) if (edge(i)) any = true;
      const ax = p.axes[0] || 0, ay = p.axes[1] || 0, dead = 0.5;
      let dir = null;
      if (pressed(12) || ay < -dead) dir = "up";
      else if (pressed(13) || ay > dead) dir = "down";
      else if (pressed(14) || ax < -dead) dir = "left";
      else if (pressed(15) || ax > dead) dir = "right";
      if (dir !== st.dir) {
        st.dir = dir;
        if (dir) { any = true; st.next = ts + 380; this._pad(() => this.h.move(dir)); }
      } else if (dir && ts >= st.next) {
        st.next = ts + 110;
        this._pad(() => this.h.move(dir));
      }
      if (any && this.h.anyPad) this.h.anyPad(p);
    }
  }

  _pad(fn) {
    this._setMode("pad");
    if (this.h.any && this.h.any()) return;
    fn();
  }

  connectedPads() {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    return [...pads].filter((p) => p && p.connected);
  }
}
