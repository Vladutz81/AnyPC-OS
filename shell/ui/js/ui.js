// Shared rendering helpers.
import { icon, GLYPHS } from "./icons.js";
import { t } from "./i18n.js";
import { api } from "./api.js";

export function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export function el(html) {
  const tpl = document.createElement("template");
  tpl.innerHTML = html.trim();
  return tpl.content.firstElementChild;
}

function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}

export function motes(seed = 3, n = 34) {
  const r = rng(seed);
  let out = "";
  for (let i = 0; i < n; i++) {
    const s = [1, 2, 2, 3, 3, 4][Math.floor(r() * 6)] / 16;
    out += `<i class="mote" style="left:${(r() * 100).toFixed(1)}%;top:${(20 + r() * 100).toFixed(1)}%;width:${s}rem;height:${s}rem;opacity:${(0.2 + r() * 0.5).toFixed(2)};animation-duration:${(14 + r() * 16).toFixed(1)}s;animation-delay:-${(r() * 30).toFixed(1)}s"></i>`;
  }
  return `<div class="motes" aria-hidden="true">${out}</div>`;
}

export function background(seed = 3, dim = false) {
  return `<div class="bg" aria-hidden="true"></div>
<svg class="ribbons" viewBox="0 0 1500 720" aria-hidden="true">
<path d="M0 520 C 260 430, 480 630, 750 520 S 1230 430, 1500 520" fill="none" stroke="rgba(170,205,255,0.16)" stroke-width="2"/>
<path d="M0 556 C 300 476, 520 666, 780 556 S 1260 476, 1500 566" fill="none" stroke="rgba(170,205,255,0.10)" stroke-width="1.2"/>
<path d="M0 620 C 320 570, 600 700, 820 625 S 1280 570, 1500 630" fill="none" stroke="rgba(140,185,255,0.10)" stroke-width="18" style="filter:blur(8px)"/>
</svg>${motes(seed)}${dim ? '<div class="bg-dim" aria-hidden="true"></div>' : ""}`;
}

export function hues(g) {
  const h = g.hue || 0;
  return { c1: `hsl(${h} 90% 62%)`, c2: `hsl(${h} 80% 14%)` };
}

export function glyphFor(g) {
  let n = 0;
  for (const ch of g.name) n = (n * 31 + ch.charCodeAt(0)) >>> 0;
  return GLYPHS[n % GLYPHS.length];
}

// Cover art: real artwork from the service when there is some, else an abstract cover.
export function cover(g, extra = "") {
  const { c1, c2 } = hues(g);
  const fallback = `<svg viewBox="0 0 100 100" aria-hidden="true">${glyphFor(g)}</svg>`;
  const img = g.hasArt && !api.offline
    ? `<img src="${api.artUrl(g.id)}" alt="" loading="lazy">` : "";
  const cls = g.hasArt && g.source !== "steam" ? "art icon" : "art";
  return `<span class="${cls}" style="background:linear-gradient(140deg, ${c1}, ${c2})" ${extra}>${img ? img : fallback}</span>`;
}

export function heroBackground(g) {
  if (!g) return "";
  const { c1, c2 } = hues(g);
  return `radial-gradient(ellipse 62% 95% at 80% 45%, ${c1} 0%, ${c2} 42%, #020718 92%)`;
}

export function playtime(g) {
  if (!g.seconds && !g.lastPlayed) return t("not_played");
  const s = g.seconds || 0;
  if (s >= 3600) return t("played_h", { h: Math.round(s / 3600) });
  if (s >= 60) return t("played_m", { m: Math.round(s / 60) });
  return t("last_played") + ": " + date(g.lastPlayed);
}

export function date(ts) {
  if (!ts) return t("never");
  return new Date(ts * 1000).toLocaleDateString(document.documentElement.lang || "en", { day: "numeric", month: "short", year: "numeric" });
}

export function sourceLabel(g) {
  return t({ steam: "src_steam", flatpak: "src_flatpak" }[g.source] || "src_native");
}

export function avatar(u, size = "3rem") {
  const initial = esc((u.name || "?").trim().charAt(0).toUpperCase() || "?");
  return `<span class="avatar c-${esc(u.color || "blue")}" style="width:${size};height:${size};font-size:calc(${size} * 0.36)">${initial}</span>`;
}

export function clock() {
  return `<span class="clock" data-clock>${timeNow()}</span>`;
}

let clock24 = true;
export function setClock24(on) { clock24 = !!on; }

export function timeNow() {
  return new Date().toLocaleTimeString(document.documentElement.lang || "en", { hour: "2-digit", minute: "2-digit", hour12: !clock24 });
}

export function bytes(n) {
  if (n == null) return "—";
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n >= 100 || i === 0 ? Math.round(n) : n.toFixed(1)} ${u[i]}`;
}

export function hints(list) {
  return `<div class="hints" aria-hidden="true">${list.map(([k, label]) => `<span><span class="key" data-key="${k}">${k}</span>${esc(label)}</span>`).join("")}</div>`;
}

export function backButton(label) {
  return `<button type="button" class="back" data-act="back">${icon("back")}${esc(label)}</button>`;
}
