#!/usr/bin/env python3
"""Static checks for the boot splash theme (session/plymouth/anypc).

Plymouth cannot run in CI, so this checks what can break silently: the theme
file points at the right script, every image the script loads exists and is a
PNG, and braces and parentheses in the script are balanced.
"""
import configparser
import pathlib
import re
import sys

THEME = pathlib.Path(__file__).resolve().parent.parent / "session" / "plymouth" / "anypc"
INSTALL_DIR = "/usr/share/plymouth/themes/anypc"
errors = []

cfg = configparser.ConfigParser()
cfg.read(THEME / "anypc.plymouth")
if cfg.get("Plymouth Theme", "ModuleName", fallback="") != "script":
    errors.append("anypc.plymouth: ModuleName must be script")
if cfg.get("script", "ImageDir", fallback="") != INSTALL_DIR:
    errors.append(f"anypc.plymouth: ImageDir must be {INSTALL_DIR}")
script_path = cfg.get("script", "ScriptFile", fallback="")
if script_path != f"{INSTALL_DIR}/anypc.script":
    errors.append("anypc.plymouth: ScriptFile must be the anypc.script in the theme folder")

script = (THEME / "anypc.script").read_text(encoding="utf-8")
code = "\n".join(line.split("#", 1)[0] for line in script.splitlines())

images = sorted(set(re.findall(r'"([\w.-]+\.png)"', code)))
for name in images:
    f = THEME / name
    if not f.is_file():
        errors.append(f"anypc.script loads {name}, which is missing")
    elif f.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        errors.append(f"{name} is not a PNG file")

for a, b in ("()", "{}", "[]"):
    if code.count(a) != code.count(b):
        errors.append(f"anypc.script: unbalanced {a}{b}")

for e in errors:
    print("error:", e)
if errors:
    sys.exit(1)
print(f"boot splash theme OK ({len(images)} images)")
