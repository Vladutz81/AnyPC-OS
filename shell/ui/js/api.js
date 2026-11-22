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
  games.push({ id: "demo-anyps5", name: "Homebrew Sample", genre: "Game", hue: 240,
    source: "anyps5", hasArt: false, seconds: 0, lastPlayed: 0 });
  return {
    state: { os: "AnyPC OS", version: "0.1", daemon: "preview", demo: true, running: { running: false } },
    users: [{ id: "u1", name: "Player 1", color: "blue" }],
    games,
    settings: { language: "en", reduce_motion: false, high_contrast: false, boot_animation: true, startup_sound: true, ui_sounds: true, auto_updates: true,
      clock_24h: true, rest_after: 30, overscan: 100,
      compat: { steam: true, native: true, emulators: true, anyps5: true } },
    system: { os: "AnyPC OS 0.1 (preview)", hostname: "anypc-preview", kernel: "preview", cpu: "Preview CPU", gpus: ["Preview GPU"], memory: 16 * 1024 ** 3 },
    audio: { available: true, volume: 70, muted: false, outputs: [{ id: 48, name: "HDMI / DisplayPort", default: true }, { id: 52, name: "Speakers", default: false }] },
    network: { available: true, wifiEnabled: true,
      devices: [{ device: "eth0", type: "ethernet", state: "connected", connection: "Wired connection 1" }, { device: "wlan0", type: "wifi", state: "disconnected", connection: null }],
      wifi: [{ ssid: "Home Network", signal: 82, secure: true, active: false, saved: false }, { ssid: "Guest", signal: 55, secure: false, active: false, saved: false }],
      saved: [{ name: "Wired connection 1", type: "ethernet" }] },
    bluetooth: { available: true, powered: true, scanning: false,
      devices: [{ mac: "AA:BB:CC:00:00:01", name: "Wireless Controller", paired: true, connected: true, icon: "input-gaming", battery: 80 }] },
    displays: { outputs: [{ connector: "HDMI-A-1", modes: ["3840x2160", "2560x1440", "1920x1080", "1280x720"] }], mode: "auto" },
    timedate: { available: true, timezone: "Europe/Bucharest", ntp: true, synced: true },
    timezones: ["America/New_York", "Asia/Tokyo", "Europe/Berlin", "Europe/Bucharest", "Europe/London", "Europe/Paris", "UTC"],
    storage: [{ mount: "/var", device: "/dev/nvme0n1p3", fs: "btrfs", total: 512 * 1024 ** 3, used: 180 * 1024 ** 3, free: 332 * 1024 ** 3, removable: false }],
    updates: { managed: true, state: "idle", checked: null, booted: { version: "0.1" }, staged: null, rollback: null, available: null },
    catalog: {items: [["steam","Steam"],["kart","SuperTuxKart"],["vlc","VLC"],["retroarch", "RetroArch", "engine"],["pcsx2", "PCSX2", "engine"],["rpcs3", "RPCS3", "engine"],["xemu", "xemu", "engine"],["ppsspp", "PPSSPP", "engine"],["dolphin", "Dolphin", "engine"],["cemu", "Cemu", "engine"],["melonds", "melonDS", "engine"],["mgba", "mGBA", "engine"],["flycast", "Flycast", "engine"],["mame", "MAME", "engine"],["dosbox", "DOSBox Staging", "engine"],["heroic", "Heroic Games Launcher", "tool"],["moonlight", "Moonlight", "tool"],["protonup", "ProtonUp-Qt", "tool"]].map(([id,name,kind=id]) => ({id,name,description:"store_" + kind,installed:false})), imports:[], job:{state:"idle"}},
    modules: { anyps5: { installed: true }, leonida: { installed: true, version: "067d3e8b9718", status: "experimental",
      wine: true, proton: true, checks: { state: "idle", passed: 0, failed: 0, total: 11, results: [], simulated: true, error: null, checked: null } } },
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
    if (path.startsWith("/api/games")) return d.games.filter(g => g.source !== "anyps5" || d.settings.compat.anyps5);
    const key = path.slice(5).split("?")[0];
    if (key in d) return JSON.parse(JSON.stringify(d[key]));
    return {};
  }
  if (path === "/api/modules/leonida/check") {
    const check = d.modules.leonida.checks;
    if (check.state === "running") throw Object.assign(new Error("A module check is already running"), { api: true });
    Object.assign(check, { state: "running", passed: 0, failed: 0, error: null, checked: null });
    setTimeout(() => Object.assign(check, { state: "done", passed: 11, checked: Math.floor(Date.now() / 1000) }), 400);
    return JSON.parse(JSON.stringify(d.modules));
  }
  if (path === "/api/catalog/action") {
    if (body.action === "scan" && body.id === "usb") { d.catalog.job = {state:"done", id:"usb", action:"scan"}; return {accepted:true}; }
    const item = d.catalog.items.find(i => i.id === body.id);
    if (!item || !["open","install","update"].includes(body.action)) throw new Error("unknown_catalog_action");
    item.installed = true;
    d.catalog.job = {state:"done", id:item.id, action:body.action};
    return {accepted:true};
  }
  if (path === "/api/users") {
    const u = { id: "u" + (d.users.length + 1), name: String(body.name || "").trim().slice(0, 16) || "Player", color: body.color || "blue" };
    d.users.push(u);
    return u;
  }
  const m = path.match(/^\/api\/games\/([^/]+)\/launch$/);
  if (m) {
    const g = d.games.find((x) => x.id === m[1] && (x.source !== "anyps5" || d.settings.compat.anyps5));
    if (!g) throw Object.assign(new Error("unknown game"), { api: true });
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
  const fail = (msg) => { throw Object.assign(new Error(msg), { api: true }); };
  const um = path.match(/^\/api\/users\/([^/]+)(\/delete)?$/);
  if (um) {
    const u = d.users.find((x) => x.id === um[1]);
    if (!u) fail("unknown user");
    if (um[2]) { d.users = d.users.filter((x) => x !== u); return { ok: true }; }
    if (body.name) u.name = String(body.name).slice(0, 16);
    if (body.color) u.color = body.color;
    return u;
  }
  const n = d.network;
  if (path === "/api/network/wifi") { n.wifiEnabled = body.on; return n; }
  if (path === "/api/network/connect") {
    const w = n.wifi.find((x) => x.ssid === body.ssid);
    if (w.secure && !w.saved && body.password !== "password123") fail("Wrong password (preview password: password123)");
    n.wifi.forEach((x) => (x.active = x === w));
    w.saved = true;
    if (!n.saved.find((x) => x.name === w.ssid)) n.saved.push({ name: w.ssid, type: "wifi" });
    return n;
  }
  if (path === "/api/network/disconnect") { n.wifi.forEach((x) => (x.active = false)); return n; }
  if (path === "/api/network/forget") {
    n.saved = n.saved.filter((x) => x.name !== body.name);
    n.wifi.forEach((x) => { if (x.ssid === body.name) { x.saved = false; x.active = false; } });
    return n;
  }
  const bt = d.bluetooth;
  if (path === "/api/bluetooth/power") { bt.powered = body.on; return bt; }
  if (path === "/api/bluetooth/scan") {
    bt.scanning = true;
    setTimeout(() => { bt.scanning = false; }, 4000);
    if (!bt.devices.find((x) => x.mac === "AA:BB:CC:00:00:02"))
      bt.devices.push({ mac: "AA:BB:CC:00:00:02", name: "Xbox Wireless Controller", paired: false, connected: false, icon: "input-gaming", battery: null });
    return bt;
  }
  const bm = path.match(/^\/api\/bluetooth\/(pair|connect|disconnect|remove)$/);
  if (bm) {
    const x = bt.devices.find((y) => y.mac === body.mac);
    if (bm[1] === "remove") bt.devices = bt.devices.filter((y) => y !== x);
    else { x.paired = true; x.connected = bm[1] !== "disconnect"; }
    return bt;
  }
  if (path === "/api/displays") { d.displays.mode = body.mode; return d.displays; }
  if (path === "/api/timedate") { if (body.timezone) d.timedate.timezone = body.timezone; if ("ntp" in body) d.timedate.ntp = body.ntp; return d.timedate; }
  if (path === "/api/hostname") { d.system.hostname = body.name; return { hostname: body.name }; }
  if (path === "/api/settings/reset") {
    d.settings = { language: "en", reduce_motion: false, high_contrast: false, boot_animation: true, startup_sound: true, ui_sounds: true, auto_updates: true, clock_24h: true, rest_after: 30, overscan: 100,
      compat: { steam: true, native: true, emulators: true, anyps5: true } };
    return d.settings;
  }
  const upm = path.match(/^\/api\/updates\/(check|apply|rollback)$/);
  if (upm) {
    const u = d.updates;
    u.checked = Math.floor(Date.now() / 1000);
    if (upm[1] === "check") u.available = u.staged ? null : { version: "0.2" };
    if (upm[1] === "apply") { u.staged = u.available; u.available = null; }
    if (upm[1] === "rollback") fail("No previous version on this system");
    return u;
  }
  return {};
}

export const api = {
  get: (p) => call("GET", p),
  post: (p, b) => call("POST", p, b),
  get offline() { return offline; },
  artUrl: (id) => `/api/games/${encodeURIComponent(id)}/art`,
};
