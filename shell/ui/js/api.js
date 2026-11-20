// Talks to anypc-shelld. When the service is unreachable (for example when the
// UI is opened as a static preview) it falls back to an in-memory demo.

const DEMO = (() => {
  const names = [["SuperTuxKart", "Racing", 24], ["0 A.D.", "Strategy", 42], ["Xonotic", "Shooter", 170],
    ["Veloren", "RPG", 110], ["Luanti", "Sandbox", 265], ["OpenTTD", "Simulation", 345],
    ["Hedgewars", "Strategy", 48], ["Mindustry", "Strategy", 28], ["Endless Sky", "Simulation", 215],
    ["The Battle for Wesnoth", "Strategy", 36]];
  const now = Math.floor(Date.now() / 1000);
  const games = names.map(([name, genre, hue], i) => ({
    id: "demo" + i, name, genre, hue, source: i % 4 === 2 ? "flatpak" : "native", hasArt: false,
    seconds: [50400, 115200, 28800, 0, 162000, 0, 0, 0, 10800, 0][i],
    lastPlayed: [now - 3600, now - 86400, now - 400000, 0, now - 7200, 0, 0, 0, now - 900000, 0][i],
  }));
  return {
    state: { os: "AnyPC OS", version: "0.1", daemon: "preview", demo: true, running: { running: false } },
    users: [{ id: "u1", name: "Player 1", color: "blue" }],
    games,
    settings: { language: "en", reduce_motion: false, high_contrast: false, boot_animation: true, auto_updates: true,
      compat: { steam: true, native: true, emulators: true, anyps5: false } },
    system: { os: "AnyPC OS 0.1 (preview)", hostname: "anypc-preview", kernel: "—", cpu: "—", gpus: [], memory: null, disk: null },
    audio: { available: true, volume: 70, muted: false },
    network: { available: true, devices: [{ device: "eth0", type: "ethernet", state: "connected", connection: "Wired" }], wifi: [] },
    running: { running: false },
  };
})();

let offline = false;

async function call(method, path, body) {
  if (!offline) {
    try {
      const r = await fetch(path, {
        method,
        headers: method === "POST" ? { "Content-Type": "application/json", "X-AnyPC": "1" } : {},
        body: method === "POST" ? JSON.stringify(body || {}) : undefined,
      });
      const ctype = r.headers.get("Content-Type") || "";
      if (!ctype.includes("application/json")) throw new TypeError("not the shell service");
      const data = await r.json();
      if (!r.ok) throw Object.assign(new Error(data.error || r.statusText), { api: true });
      return data;
    } catch (e) {
      if (e.api) throw e;
      offline = true; // no service: switch to the preview demo for the rest of the session
    }
  }
  return demo(method, path, body);
}

function demo(method, path, body) {
  const d = DEMO;
  if (method === "GET") {
    if (path === "/api/state") return { ...d.state, running: d.running };
    if (path.startsWith("/api/games")) return d.games;
    const key = path.slice(5);
    if (key in d) return JSON.parse(JSON.stringify(d[key]));
    return {};
  }
  if (path === "/api/users") {
    const u = { id: "u" + (d.users.length + 1), name: String(body.name || "").trim().slice(0, 16) || "Player", color: body.color || "blue" };
    d.users.push(u);
    return u;
  }
  const m = path.match(/^\/api\/games\/([^/]+)\/launch$/);
  if (m) {
    const g = d.games.find((x) => x.id === m[1]);
    if (d.running.running) throw Object.assign(new Error("a game is already running"), { api: true });
    g.lastPlayed = Math.floor(Date.now() / 1000);
    d.running = { running: true, id: g.id, name: g.name, started: g.lastPlayed };
    return d.running;
  }
  if (path === "/api/running/stop") { d.running = { running: false }; return d.running; }
  if (path === "/api/settings") {
    const c = body.compat ? { ...d.settings.compat, ...body.compat } : d.settings.compat;
    d.settings = { ...d.settings, ...body, compat: c };
    return d.settings;
  }
  if (path === "/api/audio") {
    if (typeof body.volume === "number") d.audio.volume = Math.max(0, Math.min(100, Math.round(body.volume)));
    if (typeof body.muted === "boolean") d.audio.muted = body.muted;
    return d.audio;
  }
  if (path.startsWith("/api/power/")) return { ok: true, demo: true };
  return {};
}

export const api = {
  get: (p) => call("GET", p),
  post: (p, b) => call("POST", p, b),
  get offline() { return offline; },
  artUrl: (id) => `/api/games/${encodeURIComponent(id)}/art`,
};
