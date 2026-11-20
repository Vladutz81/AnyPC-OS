// Fails if a string used in the UI is missing in any language.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "shell", "ui", "js");
globalThis.document = { documentElement: {} };
const i18n = await import(pathToFileURL(path.join(root, "i18n.js")).href);

const files = [];
const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).forEach((e) => {
  const p = path.join(d, e.name);
  if (e.isDirectory()) walk(p); else if (p.endsWith(".js")) files.push(p);
});
walk(root);

const used = new Set();
for (const f of files) {
  for (const m of fs.readFileSync(f, "utf8").matchAll(/\bt\("([a-z0-9_]+)"\s*[,)]/g)) used.add(m[1]);
}

let bad = 0;
for (const [code] of i18n.LANGS) {
  i18n.setLang(code);
  const missing = [...used].filter((k) => !i18n.has(k));
  if (missing.length) { bad++; console.error(`${code}: missing ${missing.join(", ")}`); }
}
if (bad) process.exit(1);
console.log(`${used.size} strings, ${i18n.LANGS.length} languages: OK`);
