import { el } from "../ui.js";
import { motes } from "../ui.js";
import { t } from "../i18n.js";

// The startup animation. Any button (after a short moment) skips it.
export class BootScreen {
  constructor(app) {
    this.app = app;
    this.noMenu = true;
    this.t0 = performance.now();
    let burst = "";
    for (let i = 0; i < 28; i++) {
      const a = (i / 28) * Math.PI * 2 + Math.sin(i * 7) * 0.3;
      const r = 11 + ((i * 37) % 21);
      burst += `<i style="width:${(2 + (i % 3)) / 16}rem;height:${(2 + (i % 3)) / 16}rem;--dx:${(Math.cos(a) * r).toFixed(1)}rem;--dy:${(Math.sin(a) * r * 0.7).toFixed(1)}rem;animation-delay:${((i % 5) * 0.05).toFixed(2)}s"></i>`;
    }
    this.el = el(`<section class="screen boot" aria-label="AnyPC OS">
<div class="scene">
<div class="bg" aria-hidden="true"></div>
${motes(11, 48)}
<div class="sweep" aria-hidden="true"></div>
<div aria-hidden="true"><div class="shock"></div><div class="shock two"></div><div class="flare"></div><div class="burst">${burst}</div></div>
<div class="center">
<svg class="mark" viewBox="0 0 240 240" role="img" aria-label="AnyPC OS">
<defs><linearGradient id="bootg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#B9CCF5"/></linearGradient></defs>
<path class="arc" pathLength="100" d="M162.5 56.4 A85 85 0 1 1 77.5 56.4" fill="none" stroke="url(#bootg)" stroke-width="8" stroke-linecap="round"/>
<path class="chev" pathLength="100" d="M90 158 L120 30 L150 158" fill="none" stroke="url(#bootg)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
<circle class="dot" cx="120" cy="126" r="7" fill="#FFFFFF"/>
</svg>
<div style="display:flex;flex-direction:column;align-items:center;gap:1.1rem"><span class="word">AnyPC OS</span><span class="rule"></span></div>
</div>
<div class="press">${t("press_any")}</div>
</div>
<div class="vignette" aria-hidden="true"></div>
<div class="black" aria-hidden="true"></div>
</section>`);
    this.timer = setTimeout(() => this.done(), 9500);
  }

  // Swallow input during boot; after 1.5 s any input continues.
  onAny() {
    if (performance.now() - this.t0 > 1500) this.done();
    return true;
  }

  done() {
    if (this.finished) return;
    this.finished = true;
    clearTimeout(this.timer);
    this.app.afterBoot();
  }

  dispose() { clearTimeout(this.timer); }
}
