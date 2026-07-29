# Mini-Kochbuch

Ein eigenständiger, druckbarer Rezept-Spickzettel. Das Hauptkochbuch und dessen
LaTeX-Dateien werden dafür nicht verändert.

## Aktueller Prototyp

- Format: A5 quer
- Rezepte: Savory Oatmeal und Mushroom Wellington
- Quellen:
  - `rezepte/fruehstueck/savory-oatmeal.tex`
  - `rezepte/signature_dish/veggi-beef-wellington.tex`
- Ausgabe: eine schlichte Zutaten-/Ablaufmatrix wie im gezeigten
  Limoncello-Tiramisu-Schema. Zutaten stehen links; verbundene Zellen rechts
  zeigen Verarbeitung und Zusammenführung.
- Rezepttexte und Mengen werden unverändert aus dem Hauptkochbuch übernommen.

## Struktur

Jedes Rezept liegt in einer eigenen Datei:

```text
rezepte/
├── 01-garlic-soy-tofu-bites.html
├── ...
└── 61-zwiebelsuppe.html
```

Die Nummer am Anfang bestimmt die Reihenfolge im PDF. Für weitere Rezepte wird
eine neue Datei im Ordner `rezepte/` angelegt. Dadurch bleiben auch 61 oder mehr
Rezepte einzeln bearbeitbar.

Das gemeinsame Tabellenlayout steht in `style.css`.

`generate.py` liest die in `book.tex` eingebundenen LaTeX-Rezepte und
aktualisiert die einzelnen Spickzettel. Die zwei abgestimmten Referenzseiten
für Mushroom Wellington und Savory Oatmeal sind handgesetzt und werden dabei
nicht überschrieben. `rezepte/manifest.txt` hält die aktuelle Reihenfolge fest,
damit keine alte oder nicht mehr eingebundene Datei im PDF landet.

## PDF erstellen

`build.sh` aktualisiert zunächst die generierten Rezeptdateien, sammelt danach
alle Dateien aus `rezepte/` und erstellt daraus das gemeinsame PDF.

```bash
./build.sh
```

Das Skript erzeugt `mini-kochbuch.pdf` im selben Ordner. Voraussetzung ist
Google Chrome oder ein kompatibler Chrome-Befehl unter `google-chrome`.
