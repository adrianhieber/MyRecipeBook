#!/usr/bin/env python3
"""Verkleinert die Bilder im Ordner ``pic`` proportional.

Ohne ``--anwenden`` zeigt das Skript nur an, welche Bilder geändert würden.
Für die Bildbearbeitung wird Pillow benötigt:

    python3 -m pip install Pillow
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
except ImportError:
    print(
        "Fehler: Pillow ist nicht installiert.\n"
        "Installation: python3 -m pip install Pillow",
        file=sys.stderr,
    )
    raise SystemExit(1)


STANDARD_BILDORDNER = Path(__file__).resolve().parent / "pic"
UNTERSTUETZTE_ENDUNGEN = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class Statistik:
    gefunden: int = 0
    verkleinert: int = 0
    uebersprungen: int = 0
    fehler: int = 0
    bytes_vorher: int = 0
    bytes_nachher: int = 0


def dateigroesse_anzeigen(anzahl_bytes: int) -> str:
    """Gibt eine Dateigröße kompakt und gut lesbar aus."""
    wert = float(anzahl_bytes)
    for einheit in ("B", "KiB", "MiB", "GiB"):
        if wert < 1024 or einheit == "GiB":
            return f"{wert:.1f} {einheit}"
        wert /= 1024
    raise AssertionError("unerreichbar")


def zielgroesse(
    breite: int, hoehe: int, maximale_kante: int
) -> tuple[int, int]:
    """Berechnet die neue Größe ohne Hochskalieren."""
    groesste_kante = max(breite, hoehe)
    if groesste_kante <= maximale_kante:
        return breite, hoehe

    faktor = maximale_kante / groesste_kante
    return max(1, round(breite * faktor)), max(1, round(hoehe * faktor))


def speicheroptionen(
    bild: Image.Image, formatname: str, qualitaet: int
) -> dict[str, object]:
    """Liefert sinnvolle Speicheroptionen für das jeweilige Bildformat."""
    optionen: dict[str, object] = {}

    exif = bild.info.get("exif")
    icc_profil = bild.info.get("icc_profile")
    if exif:
        optionen["exif"] = exif
    if icc_profil:
        optionen["icc_profile"] = icc_profil

    if formatname == "JPEG":
        optionen.update(quality=qualitaet, optimize=True, progressive=True)
    elif formatname == "PNG":
        optionen.update(optimize=True, compress_level=9)
    elif formatname == "WEBP":
        optionen.update(quality=qualitaet, method=6)

    return optionen


def bild_speichern(
    bild: Image.Image,
    quellpfad: Path,
    formatname: str,
    qualitaet: int,
) -> None:
    """Speichert atomar, damit ein Abbruch die Originaldatei nicht zerstört."""
    temp_pfad: Path | None = None
    modus = quellpfad.stat().st_mode

    try:
        with tempfile.NamedTemporaryFile(
            dir=quellpfad.parent,
            prefix=f".{quellpfad.stem}-",
            suffix=quellpfad.suffix,
            delete=False,
        ) as temp_datei:
            temp_pfad = Path(temp_datei.name)

        zu_speichern = bild
        if formatname == "JPEG" and bild.mode not in ("RGB", "L", "CMYK"):
            # JPEG unterstützt keine Transparenz.
            zu_speichern = bild.convert("RGB")

        zu_speichern.save(
            temp_pfad,
            format=formatname,
            **speicheroptionen(bild, formatname, qualitaet),
        )
        os.chmod(temp_pfad, modus)
        os.replace(temp_pfad, quellpfad)
    finally:
        if temp_pfad is not None:
            temp_pfad.unlink(missing_ok=True)


def backup_anlegen(bildpfad: Path, bildordner: Path, backupordner: Path) -> None:
    """Kopiert das Original einmalig in die passende Backup-Unterstruktur."""
    ziel = backupordner / bildpfad.relative_to(bildordner)
    if ziel.exists():
        return
    ziel.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bildpfad, ziel)


def bild_verarbeiten(
    bildpfad: Path,
    bildordner: Path,
    maximale_kante: int,
    qualitaet: int,
    anwenden: bool,
    backupordner: Path | None,
) -> tuple[bool, int, int]:
    """Prüft und verkleinert ein Bild. Gibt Änderung und Dateigrößen zurück."""
    groesse_vorher = bildpfad.stat().st_size

    with Image.open(bildpfad) as original:
        formatname = original.format
        if formatname not in {"JPEG", "PNG", "WEBP", "MPO"}:
            raise ValueError(f"nicht unterstütztes Bildformat: {formatname}")

        # Handybilder enthalten häufig nur einen EXIF-Rotationshinweis.
        bild = ImageOps.exif_transpose(original)
        alte_abmessungen = bild.size
        neue_abmessungen = zielgroesse(*alte_abmessungen, maximale_kante)

        if neue_abmessungen == alte_abmessungen:
            return False, groesse_vorher, groesse_vorher

        print(
            f"  {bildpfad.relative_to(bildordner)}: "
            f"{alte_abmessungen[0]}×{alte_abmessungen[1]} → "
            f"{neue_abmessungen[0]}×{neue_abmessungen[1]} "
            f"({dateigroesse_anzeigen(groesse_vorher)})"
        )

        if not anwenden:
            return True, groesse_vorher, groesse_vorher

        if backupordner is not None:
            backup_anlegen(bildpfad, bildordner, backupordner)

        bild.thumbnail(neue_abmessungen, Image.Resampling.LANCZOS)
        # MPO-Handybilder werden als normales, kompatibles JPEG gespeichert.
        ausgabeformat = "JPEG" if formatname == "MPO" else formatname
        bild_speichern(bild, bildpfad, ausgabeformat, qualitaet)

    return True, groesse_vorher, bildpfad.stat().st_size


def argumente_einlesen() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verkleinert Bilder in pic rekursiv und behält ihr Seitenverhältnis bei. "
            "Ohne --anwenden wird nur eine Vorschau ausgegeben."
        )
    )
    parser.add_argument(
        "--ordner",
        type=Path,
        default=STANDARD_BILDORDNER,
        help="Bildordner (Standard: pic neben diesem Skript)",
    )
    parser.add_argument(
        "--max-kante",
        type=int,
        default=2400,
        help="Maximale Länge der größten Bildkante in Pixeln (Standard: 2400)",
    )
    parser.add_argument(
        "--qualitaet",
        type=int,
        default=85,
        help="JPEG-/WebP-Qualität von 1 bis 95 (Standard: 85)",
    )
    parser.add_argument(
        "--anwenden",
        action="store_true",
        help="Dateien tatsächlich überschreiben; ohne diese Option nur Vorschau",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Originale vor dem Überschreiben zusätzlich in pic_backup sichern",
    )
    return parser.parse_args()


def main() -> int:
    argumente = argumente_einlesen()
    bildordner = argumente.ordner.resolve()

    if argumente.max_kante < 1:
        print("Fehler: --max-kante muss mindestens 1 sein.", file=sys.stderr)
        return 2
    if not 1 <= argumente.qualitaet <= 95:
        print("Fehler: --qualitaet muss zwischen 1 und 95 liegen.", file=sys.stderr)
        return 2
    if not bildordner.is_dir():
        print(f"Fehler: Bildordner nicht gefunden: {bildordner}", file=sys.stderr)
        return 2

    backupordner = (
        bildordner.parent / f"{bildordner.name}_backup"
        if argumente.backup and argumente.anwenden
        else None
    )
    statistik = Statistik()
    bildpfade = sorted(
        pfad
        for pfad in bildordner.rglob("*")
        if pfad.is_file() and pfad.suffix.lower() in UNTERSTUETZTE_ENDUNGEN
    )

    modus = "ANWENDEN" if argumente.anwenden else "VORSCHAU"
    print(
        f"{modus}: {len(bildpfade)} Bilder, "
        f"maximal {argumente.max_kante} px an der längsten Kante"
    )
    if backupordner is not None:
        print(f"Backup: {backupordner}")

    for bildpfad in bildpfade:
        statistik.gefunden += 1
        try:
            geaendert, groesse_vorher, groesse_nachher = bild_verarbeiten(
                bildpfad=bildpfad,
                bildordner=bildordner,
                maximale_kante=argumente.max_kante,
                qualitaet=argumente.qualitaet,
                anwenden=argumente.anwenden,
                backupordner=backupordner,
            )
            statistik.bytes_vorher += groesse_vorher
            statistik.bytes_nachher += groesse_nachher
            if geaendert:
                statistik.verkleinert += 1
            else:
                statistik.uebersprungen += 1
        except (OSError, ValueError, UnidentifiedImageError) as fehler:
            statistik.fehler += 1
            print(f"FEHLER bei {bildpfad}: {fehler}", file=sys.stderr)

    if argumente.anwenden:
        ersparnis = statistik.bytes_vorher - statistik.bytes_nachher
        print(
            f"\nFertig: {statistik.verkleinert} verkleinert, "
            f"{statistik.uebersprungen} bereits passend, "
            f"{statistik.fehler} Fehler."
        )
        print(
            f"Größe: {dateigroesse_anzeigen(statistik.bytes_vorher)} → "
            f"{dateigroesse_anzeigen(statistik.bytes_nachher)} "
            f"(gespart: {dateigroesse_anzeigen(max(0, ersparnis))})"
        )
    else:
        print(
            f"\nVorschau: {statistik.verkleinert} würden verkleinert, "
            f"{statistik.uebersprungen} sind bereits passend, "
            f"{statistik.fehler} Fehler."
        )
        print("Zum Ausführen: python3 bilder_verkleinern.py --anwenden --backup")

    return 1 if statistik.fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
