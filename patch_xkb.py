#!/usr/bin/env python3
"""
Angepasstes Script: Fügt VOU nur in /usr/share/X11/xkb/symbols/custom ein
- Keine Kopie der gesamten de-Datei mehr
- Nur der vou-Block + Patches
- level3-Patch wird in ~/.config/xkb/symbols/level3 geschrieben
- Rules-Patch für evdev.extras.xml (systemweit)
"""

import os
import sys
from pathlib import Path

curr_dir = os.path.dirname(__file__)
xkb_base = os.path.realpath("/usr/share/X11/xkb")
symbols_custom = Path(f"{xkb_base}/symbols/custom")
rules_extras = Path(f"{xkb_base}/rules/evdev.extras.xml")

# User-spezifischer Pfad für level3
user_symbols = Path.home() / ".config" / "xkb" / "symbols"
user_level3 = user_symbols / "level3"

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

def ensure_user_level3_exists():
    user_symbols.mkdir(parents=True, exist_ok=True)
    if not user_level3.exists():
        print(f"→ Erstelle user-level3: {user_level3}")
        user_level3.touch()
        with open(user_level3, "w", encoding="utf-8") as f:
            f.write("// User-level3 modifications – managed by script\n\n")
            # Optional: Basis-Inhalt von system level3 kopieren
            system_level3 = Path(f"{xkb_base}/symbols/level3")
            if system_level3.exists():
                with open(system_level3, "r", encoding="utf-8") as src:
                    f.write(src.read())
                print("   → Basis-Inhalt von system-level3 übernommen")
    else:
        print(f"→ user-level3 existiert bereits: {user_level3}")

def append_vou_block():
    de_neo_patch = read_patch("de_neo_base")
    de_koy_patch = read_patch("de_koy")

    vou_block = [
        "",
        "// === Deutsch (VOU) – Ergänzung in custom ===",
        "partial alphanumeric_keys",
        'xkb_symbols "vou" {',
        '    include "de(neo_base)"',
        '    include "level3(quote_switch)"',  # ← zeigt auf deine user-level3
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

def patch_user_level3():
    level3_patch = read_patch("level3")

    with open(user_level3, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    if any("quote_switch" in line for line in lines):
        print("→ quote_switch bereits in user-level3 vorhanden – überspringe")
        return

    print("→ Füge level3-Patch ans Ende von user-level3")
    lines.extend([""] + level3_patch + [""])
    with open(user_level3, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"→ user-level3 erfolgreich gepatcht: {user_level3}")

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
    print("Lokale VOU-Installation in symbols/custom + user-level3 (update-sicher)")
    print("---------------------------------------------------------------------")

    ensure_custom_exists()
    ensure_user_level3_exists()
    append_vou_block()
    patch_user_level3()
    patch_rules_extras()

    print("\nFertig! Teste jetzt:")
    print("  setxkbmap vou")
    print("  oder")
    print("  setxkbmap de vou")
    print("\nFalls nicht gefunden → explizit Pfad angeben:")
    print("  setxkbmap de vou -I/usr/share/X11/xkb -I\"$HOME/.config/xkb\"")
    print("\nDebug bei Fehlern:")
    print("  xkbcomp -layout de -variant vou -I\"$HOME/.config/xkb\" :0 2>&1")
    print("\nIn KDE/OpenMandriva: Nach Logout/Login oder plasmashell-Neustart sollte 'Deutsch (VOU)' erscheinen.")
    print("  plasmashell-Neustart falls nötig: kquitapp6 plasmashell && kstart plasmashell")

if __name__ == "__main__":
    main()
