
# Schönes Rezeptbuch - editierbare Version

Diese Version ist bewusst **kein reines PDF**, sondern ein weiterbearbeitbares LaTeX-Projekt.

## Wichtige Dateien

- `book_schoen.tex` - neue Hauptdatei mit schönem Layout
- `praemble_schoen.tex` - Pakete und Grundkonfiguration
- `style/kochbuch-style.tex` - Farben, Hintergründe, Rezeptkarten, Kapiteltrenner
- `rezepte/.../*.tex` - deine eigentlichen Rezepte, unverändert weiterbearbeitbar
- `pic/...` - Rezeptbilder und Kapitelbilder
- `book_schoen.pdf` - kompilierte Vorschau
- `book.tex` - deine ursprüngliche Hauptdatei bleibt erhalten

## Kompilieren

```bash
latexmk -pdf book_schoen.tex
makeindex book_schoen.idx
latexmk -pdf book_schoen.tex
```

Oder kurz:

```bash
latexmk -pdf -interaction=nonstopmode book_schoen.tex
```

## Layout ändern

Farben, Hintergrund, Kopfzeilen, Rezeptboxen und Kapiteltrenner stehen in:

```tex
style/kochbuch-style.tex
```

Zum Beispiel kannst du dort Farben wie `Tomato`, `Basil`, `WarmPaper` ändern oder die Bilder der Kapiteltrenner in `book_schoen.tex` austauschen.

## Neues Rezept hinzufügen

1. Eine neue Datei in einem passenden Unterordner unter `rezepte/` anlegen.
2. Das Rezept wie bisher mit `\begin{recipe} ... \end{recipe}` schreiben.
3. In `book_schoen.tex` an der passenden Stelle per `\input{rezepte/.../dein-rezept}` einbinden.

