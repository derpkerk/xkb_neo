#!/usr/bin/env python3
"""
Lokale VOU/Neo/KOY-Patch-Installation für OpenMandriva & andere Distros
- Arbeitet komplett im Home-Verzeichnis (~/.config/xkb/)
- Kein Root nötig
- Fügt level3-Patch (quote_switch) und Rules-Patch ein
"""

import os
import shutil
import sys
from pathlib import Path

HOME = Path.home()
XKB_USER = HOME / ".config" / "xkb"
SYMBOLS = XKB_USER / "symbols"
RULES = XKB_USER / "rules"

SYSTEM_XKB = Path("/usr/share/X11/xkb")
SYSTEM_SYMBOLS = SYSTEM_XKB / "symbols"
SYSTEM_RULES = SYSTEM_XKB / "rules"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def copy_base(src: Path, dst: Path):
    if not dst.exists():
        print(f"→ Kopiere Basis: {src} → {dst}")
        shutil.copy2(src, dst)
    else:
        print(f"→ {dst} existiert bereits – überspringe Kopie")

def read_patch(file_name: str) -> list[str]:
    script_dir = Path(__file__).parent
    path = script_dir / "patches" / file_name
    if not path.exists():
        print(f"Fehler: Patch-Datei fehlt: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()

def append_or_insert_block(lines: list[str], marker: str, patch_lines: list[str], after: bool = False):
    """Fügt Patch-Block nach oder vor Marker ein – oder am Ende, wenn Marker nicht gefunden"""
    found = False
    for i, line in enumerate(lines):
        if marker in line:
            found = True
            if after:
                # Nach dem gesamten Block einfügen → grobe Annäherung
                insert_pos = i + 1
                while insert_pos < len(lines) and lines[insert_pos].strip().startswith(" "):
                    insert_pos += 1
                lines[insert_pos:insert_pos] = [""] + patch_lines + [""]
            else:
                lines[i:i] = patch_lines + [""]
            print(f"→ Patch eingefügt bei Zeile {i+1} (Marker: {marker})")
            break
    if not found:
        print(f"→ Marker '{marker}' nicht gefunden → füge am Ende ein")
        lines.extend([""] + patch_lines + [""])

def patch_symbols_de():
    de_dst = SYMBOLS / "de"
    copy_base(SYSTEM_SYMBOLS / "de", de_dst)

    with open(de_dst, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    modified = False

    # NEO-Basis Patch
    neo_patch = read_patch("de_neo_base")
    if any('"neo_base"' in line for line in lines):
        append_or_insert_block(lines, '"neo_base"', neo_patch, after=True)
        modified = True

    # KOY Patch
    koy_patch = read_patch("de_koy")
    if any('"koy"' in line for line in lines):
        append_or_insert_block(lines, '"koy"', koy_patch, after=True)
        modified = True

    # Sicherstellen, dass ein vou-Block existiert
    if not any('"vou"' in line for line in lines):
        print("→ Erstelle neuen vou-Block am Ende")
        vou_block = [
            "",
            "// === VOU – basierend auf NEO + KOY (lokale Installation) ===",
            "partial alphanumeric_keys",
            'xkb_symbols "vou" {',
            '    include "de(neo_base)"',
            '    include "level3(ralt_switch)"',
            '    name[Group1]= "Deutsch (VOU)";',
            ""
        ]
        vou_block.extend(["    " + l for l in koy_patch])
        vou_block.append("};")
        lines.extend(vou_block)
        modified = True

    if modified:
        with open(de_dst, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"→ symbols/de erfolgreich aktualisiert: {de_dst}")
    else:
        print("→ Keine Änderungen in symbols/de nötig")

def patch_level3():
    level3_dst = SYMBOLS / "level3"
    copy_base(SYSTEM_SYMBOLS / "level3", level3_dst)

    level3_patch = read_patch("level3")

    with open(level3_dst, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    if not any("quote_switch" in line for line in lines):
        print("→ Füge level3 quote_switch Patch am Ende ein")
        lines.extend([""] + level3_patch + [""])
        with open(level3_dst, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"→ level3 erfolgreich gepatcht: {level3_dst}")
    else:
        print("→ quote_switch bereits in level3 vorhanden – überspringe")

def patch_rules():
    extras_dst = RULES / "evdev.extras.xml"
    copy_base(SYSTEM_RULES / "evdev.extras.xml", extras_dst)

    # Sehr einfache Variante: Nur den variant-Block anhängen (nicht perfekt, aber oft ausreichend)
    variant_snippet = [
        "",
        '    <variant>',
        '      <configItem>',
        '        <name>vou</name>',
        '        <shortDescription>vou</shortDescription>',
        '        <description>Deutsch (VOU)</description>',
        '        <languageList><iso639Id>ger</iso639Id></languageList>',
        '      </configItem>',
        '    </variant>',
        ""
    ]

    with open(extras_dst, "r", encoding="utf-8") as f:
        content = f.read()

    if "<name>vou</name>" not in content:
        print("→ Füge <variant> vou zu evdev.extras.xml hinzu")
        with open(extras_dst, "a", encoding="utf-8") as f:
            f.write("\n".join(variant_snippet) + "\n")
        print(f"→ Rules gepatcht: {extras_dst}")
    else:
        print("→ vou-Variante bereits in rules vorhanden – überspringe")

def print_instructions():
    print("\n" + "="*70)
    print("Lokale VOU-Installation abgeschlossen!")
    print("="*70)
    print("\nTeste das Layout:")
    print("  setxkbmap -verbose 10 de vou -I\"$HOME/.config/xkb\"")
    print("\nFür KDE/OpenMandriva:")
    print("  → Gehe in Systemeinstellungen → Eingabegeräte → Tastatur → Layouts")
    print("  → Nach Logout/Login oder plasmashell-Neustart sollte 'Deutsch (VOU)' erscheinen")
    print("  plasmashell-Neustart falls nötig: kquitapp6 plasmashell && kstart plasmashell")
    print("\nAutostart (X11): Füge in ~/.xprofile hinzu:")
    print("  setxkbmap de vou -I\"$HOME/.config/xkb\"")
    print("\nBei Problemen: Schau in ~/.config/xkb/symbols/de und suche nach 'vou'")
    print("  Oder führe aus: xkbcomp -I\"$HOME/.config/xkb\" -layout de -variant vou :0 2>&1")

def main():
    print("Lokale VOU/Neo/KOY Installation – user-only Modus für OpenMandriva")
    print("-----------------------------------------------------------------")

    patch_symbols_de()
    patch_level3()
    patch_rules()
    print_instructions()

if __name__ == "__main__":
    main()
