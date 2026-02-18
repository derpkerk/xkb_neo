#!/usr/bin/env python3
"""
Lokale (user) Installation für VOU/Neo-Patches in OpenMandriva / anderen Distros
Legt ~/.config/xkb/symbols/de an und fügt vou-Blöcke hinzu – KEIN Root nötig!
"""

import os
import shutil
import sys
from pathlib import Path

HOME = Path.home()
XKB_USER = HOME / ".config" / "xkb"
SYMBOLS = XKB_USER / "symbols"
RULES = XKB_USER / "rules"

# System-Pfade (nur zum Kopieren der Basis)
SYSTEM_XKB = Path("/usr/share/X11/xkb")
SYSTEM_SYMBOLS = SYSTEM_XKB / "symbols"
SYSTEM_RULES = SYSTEM_XKB / "rules"

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)

def copy_base_if_missing(src, dst):
    if not dst.exists():
        print(f"Kopiere Basisdatei: {src} → {dst}")
        shutil.copy2(src, dst)
    else:
        print(f"{dst} existiert bereits – überspringe Kopie")

def insert_patch(content_lines, marker, patch_lines, offset_before=1):
    """Sucht nach marker und fügt patch_lines davor oder danach ein"""
    for i, line in enumerate(content_lines):
        if marker in line:
            # offset_before = 1 bedeutet: 1 Zeile vor dem Marker einfügen
            insert_pos = i - offset_before if offset_before > 0 else i + 1
            content_lines[insert_pos:insert_pos] = patch_lines + ["\n"]
            print(f"→ Patch eingefügt bei Zeile {insert_pos+1} (Marker: {marker.strip()})")
            return True
    print(f"Warnung: Marker '{marker}' nicht gefunden – Patch nicht eingefügt!")
    return False

def main():
    print("Lokale VOU/Neo-Patch-Installation (user-only) – OpenMandriva freunly")
    print("================================================================")

    ensure_dir(SYMBOLS)
    ensure_dir(RULES)

    # 1. symbols/de Basis kopieren
    de_src = SYSTEM_SYMBOLS / "de"
    de_dst = SYMBOLS / "de"
    copy_base_if_missing(de_src, de_dst)

    # 2. Deine Patches einlesen (du musst diese Dateien aus dem Repo haben!)
    # Passe die Pfade an – idealerweise liegen sie im gleichen Ordner wie das Script
    script_dir = Path(__file__).parent

    try:
        with open(script_dir / "patches" / "de_neo_base", "r") as f:
            de_neo_patch = f.read().splitlines()
        with open(script_dir / "patches" / "de_koy", "r") as f:
            de_koy_patch = f.read().splitlines()
    except FileNotFoundError as e:
        print(f"Fehler: Patch-Datei nicht gefunden: {e}")
        print("→ Stelle sicher, dass 'patches/de_neo_base' und 'patches/de_koy' existieren!")
        sys.exit(1)

    # 3. In ~/.config/xkb/symbols/de lesen und Patches einfügen
    with open(de_dst, "r") as f:
        de_lines = f.read().splitlines()

    modified = False

    # NEO-Basis Patch (vorhandene neo_base erweitern oder neu einfügen)
    if insert_patch(de_lines, '"neo_base"', de_neo_patch, offset_before=1):
        modified = True

    # KOY Patch (nach koy-Block anhängen)
    if insert_patch(de_lines, '"koy"', de_koy_patch, offset_before=-1):  # nach dem Block
        modified = True

    # Falls "vou" noch nicht existiert → neuen Block ganz am Ende anhängen
    if all('"vou"' not in line for line in de_lines):
        print("→ Erstelle neuen 'vou'-Block am Dateiende")
        vou_block = [
            "",
            "// === VOU – basierend auf NEO + KOY-Patches ===",
            "partial alphanumeric_keys",
            'xkb_symbols "vou" {',
            '    include "de(neo_base)"',
            '    include "level3(ralt_switch)"',
            "    name[Group1]= \"Deutsch (VOU)\";",
            "",
            "    // Hier kommen die eigentlichen KOY/VOU-Änderungen (aus patches/de_koy)",
            # ← Füge hier den Inhalt von de_koy_patch ein oder lasse es als Include
        ]
        vou_block.extend(["    " + line for line in de_koy_patch])
        vou_block.append("};")
        de_lines.extend(vou_block)
        modified = True

    if modified:
        with open(de_dst, "w") as f:
            f.write("\n".join(de_lines) + "\n")
        print(f"Erfolgreich gepatcht: {de_dst}")
    else:
        print("Keine Änderungen nötig – 'vou' scheint bereits vorhanden")

    # Optional: Rules-Patch (für bessere GUI-Integration)
    print("\nOptionaler Step: Kopiere & patch evdev.extras.xml?")
    print("Das ist nur nötig, wenn 'vou' in KDE-Einstellungen fehlt")
    ans = input("Ja/Nein? [j/N]: ").strip().lower()
    if ans in ("j", "ja", "y", "yes"):
        extras_src = SYSTEM_RULES / "evdev.extras.xml"
        extras_dst = RULES / "evdev.extras.xml"
        copy_base_if_missing(extras_src, extras_dst)
        # Hier müsste man den <variant>-Block einfügen – das ist XML, etwas komplizierter
        print("→ Rules-Patch ist aktuell manuell. Füge in ~/.config/xkb/rules/evdev.extras.xml")
        print("   den <variant><name>vou</name>...</variant>-Block am Ende der <layout name=\"de\"> hinzu.")

    print("\nFertig! Teste jetzt:")
    print(f"  setxkbmap -verbose 10 de vou -I\"$HOME/.config/xkb\"")
    print("\nFür KDE: Nach Logout/Login sollte 'Deutsch (VOU)' in den Einstellungen erscheinen.")
    print("Bei Problemen: Schau in ~/.config/xkb/symbols/de und suche nach 'vou'.")

if __name__ == "__main__":
    main()
