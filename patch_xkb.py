"""
Angepasstes Script: Fügt VOU nur in /usr/share/X11/xkb/symbols/custom ein
- Keine Kopie der gesamten de-Datei mehr
- Nur der vou-Block + Patches
- Rules-Patch für evdev.extras.xml
"""

import os
import sys
from pathlib import Path

curr_dir = os.path.dirname(__file__)
xkb_base = os.path.realpath("/usr/share/X11/xkb")
symbols_custom = Path(f"{xkb_base}/symbols/custom")
rules_extras = Path(f"{xkb_base}/rules/evdev.extras.xml")

def read_patch(file_name: str) -> list[str]:
    path = Path(curr_dir) / "patches" / file_name
    if not path.exists():
        print(f"Fehler: Patch-Datei nicht gefunden: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()

def ensure_custom_exists():
    if not symbols_custom.exists():
        print(f"→ Erstelle leere custom-Datei: {symbols_custom}")
        symbols_custom.parent.mkdir(parents=True, exist_ok=True)
        symbols_custom.touch()
        with open(symbols_custom, "w", encoding="utf-8") as f:
            f.write("// Custom layouts – managed by user script\n\n")
    else:
        print(f"→ custom existiert bereits: {symbols_custom}")

def append_vou_block():
    de_neo_patch = read_patch("de_neo_base")
    de_koy_patch = read_patch("de_koy")

    vou_block = [
        "",
        "// === Deutsch (VOU) – Ergänzung in custom ===",
        "partial alphanumeric_keys",
        'xkb_symbols "vou" {',
        '    include "de(neo_base)"',
        '    include "level3(ralt_switch)"',  # oder quote_switch, ralt_switch_multi_key, ...
        '    name[Group1]= "Deutsch (VOU)";',
        "",
        "    // === Patches aus de_neo_base ==="
    ]
    vou_block.extend(["    " + line for line in de_neo_patch if line.strip() and not line.startswith("//")])
    vou_block.append("")
    vou_block.append("    // === Patches aus de_koy ===")
    vou_block.extend(["    " + line for line in de_koy_patch if line.strip() and not line.startswith("//")])
    vou_block.append("};")

    with open(symbols_custom, "r", encoding="utf-8") as f:
        content = f.read()

    if '"vou"' in content:
        print("→ 'vou' bereits in custom vorhanden – überspringe Hinzufügen")
        return

    print("→ Füge vou-Block ans Ende von custom hinzu")
    with open(symbols_custom, "a", encoding="utf-8") as f:
        f.write("\n".join(vou_block) + "\n")

def patch_rules_extras():
    if not rules_extras.exists():
        print(f"Warnung: {rules_extras} existiert nicht – Rules-Patch übersprungen")
        return

    with open(rules_extras, "r", encoding="utf-8") as f:
        content = f.read()

    if "<name>vou</name>" in content:
        print("→ vou-Variante bereits in evdev.extras.xml – überspringe")
        return

    variant_block = [
        "",
        "    <variant>",
        "      <configItem>",
        "        <name>vou</name>",
        "        <shortDescription>vou</shortDescription>",
        "        <description>Deutsch (VOU)</description>",
        "        <languageList><iso639Id>ger</iso639Id></languageList>",
        "      </configItem>",
        "    </variant>",
        ""
    ]

    print("→ Füge <variant> vou ans Ende von evdev.extras.xml")
    with open(rules_extras, "a", encoding="utf-8") as f:
        f.write("\n".join(variant_block) + "\n")

def main():
    print("Lokale VOU-Installation in symbols/custom (update-sicher)")
    print("-------------------------------------------------------")

    ensure_custom_exists()
    append_vou_block()
    patch_rules_extras()

    print("\nFertig! Teste jetzt:")
    print("  setxkbmap vou")
    print("  oder")
    print("  setxkbmap de vou")
    print("\nFalls nicht gefunden → explizit Pfad angeben:")
    print("  setxkbmap de vou -I/usr/share/X11/xkb")
    print("\nDebug bei Fehlern:")
    print("  xkbcomp -layout de -variant vou :0 2>&1")
    print("\nIn KDE/OpenMandriva: Nach Logout/Login sollte 'Deutsch (VOU)' in den Layout-Einstellungen erscheinen.")

if __name__ == "__main__":
    main()
