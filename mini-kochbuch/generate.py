#!/usr/bin/env python3
"""Erzeugt aus den in book.tex eingebundenen Rezepten einzelne Spickzettel.

Die beiden handgesetzten Referenzseiten (Wellington und Savory Oatmeal) werden
nicht überschrieben. Alle anderen Dateien werden aus den LaTeX-Quellen erzeugt.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book.tex"
OUTPUT = Path(__file__).resolve().parent / "rezepte"
MANIFEST = OUTPUT / "manifest.txt"
MANUAL_SLUGS = {"veggi-beef-wellington", "savory-oatmeal"}
MAX_ACTION_COLUMNS = 7


@dataclass
class Ingredient:
    amount: str
    name: str
    group: str = ""


@dataclass
class Recipe:
    number: int
    source: Path
    slug: str
    title: str
    header: str
    ingredients: list[Ingredient]
    steps: list[str]
    notes: list[tuple[str, str]]


def strip_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def balanced(text: str, start: int, opener: str = "{", closer: str = "}") -> tuple[str, int]:
    if start >= len(text) or text[start] != opener:
        raise ValueError(f"Erwartete {opener!r} an Position {start}")
    depth = 0
    for pos in range(start, len(text)):
        char = text[pos]
        if char == opener and (pos == 0 or text[pos - 1] != "\\"):
            depth += 1
        elif char == closer and (pos == 0 or text[pos - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return text[start + 1 : pos], pos + 1
    raise ValueError(f"Nicht geschlossene Klammer ab Position {start}")


def remove_braced_command(text: str, command: str) -> str:
    needle = f"\\{command}"
    while True:
        match = re.search(re.escape(needle) + r"\s*\{", text)
        if not match:
            return text
        brace = text.find("{", match.start())
        _, end = balanced(text, brace)
        text = text[: match.start()] + text[end:]


def replace_two_arg_command(text: str, command: str, keep: int = 2) -> str:
    needle = f"\\{command}"
    while True:
        match = re.search(re.escape(needle) + r"\s*\{", text)
        if not match:
            return text
        first_start = text.find("{", match.start())
        first, first_end = balanced(text, first_start)
        cursor = first_end
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] != "{":
            return text
        second, second_end = balanced(text, cursor)
        replacement = first if keep == 1 else second
        text = text[: match.start()] + replacement + text[second_end:]


def clean_latex(value: str) -> str:
    value = strip_comments(value)
    value = remove_braced_command(value, "index")
    value = replace_two_arg_command(value, "href", keep=2)
    value = replace_two_arg_command(value, "recipesource", keep=2)

    fractions = {
        ("1", "2"): "½",
        ("1", "3"): "⅓",
        ("2", "3"): "⅔",
        ("1", "4"): "¼",
        ("3", "4"): "¾",
    }

    def fraction(match: re.Match[str]) -> str:
        top, bottom = match.group(1).strip(), match.group(2).strip()
        return fractions.get((top, bottom), f"{top}/{bottom}")

    value = re.sub(r"\\nicefrac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", fraction, value)
    value = re.sub(
        r"\\unit\s*\[([^\]]+)\]\s*\{([^{}]+)\}",
        lambda match: f"{match.group(1).strip()} {match.group(2).strip()}",
        value,
    )
    value = re.sub(r"\\portion\s*\{([^{}]+)\}", r"\1", value)
    value = value.replace(r"\textcelcius", "°C")
    value = value.replace(r"\degree", "°")
    value = value.replace(r"\&", "&")
    value = value.replace(r"\%", "%")
    value = value.replace(r"\,", " ")
    value = value.replace(r"\;", " ")
    value = value.replace(r"\quad", " ")
    value = value.replace(r"\protect", "")
    value = value.replace(r"\newline", " ")
    value = value.replace(r"\\", " ")
    value = value.replace("--", "–")
    value = value.replace("~", " ")

    # Formatierungsbefehle behalten ihren Inhalt.
    previous = None
    while previous != value:
        previous = value
        value = re.sub(
            r"\\(?:textbf|textit|emph|small|footnotesize|textsuperscript)"
            r"\s*\{([^{}]*)\}",
            r"\1",
            value,
        )

    value = re.sub(r"\\(?:small|footnotesize|normalsize)\b", "", value)
    value = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", "", value)
    value = value.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", value).strip()


def command_blocks(text: str, command: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    pattern = re.compile(rf"\\{re.escape(command)}(?![A-Za-z])")
    cursor = 0
    while True:
        match = pattern.search(text, cursor)
        if not match:
            return results
        pos = match.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
        option = ""
        if pos < len(text) and text[pos] == "[":
            option, pos = balanced(text, pos, "[", "]")
            while pos < len(text) and text[pos].isspace():
                pos += 1
        if pos < len(text) and text[pos] == "{":
            body, pos = balanced(text, pos)
            results.append((option, body))
        cursor = max(pos, match.end() + 1)


def recipe_title_and_preamble(text: str) -> tuple[str, str]:
    match = re.search(r"\\begin\{recipe\}", text)
    if not match:
        raise ValueError("Kein recipe-Block gefunden")
    pos = match.end()
    while pos < len(text) and text[pos].isspace():
        pos += 1
    preamble_start = pos
    if pos < len(text) and text[pos] == "[":
        _, pos = balanced(text, pos, "[", "]")
        while pos < len(text) and text[pos].isspace():
            pos += 1
    if pos >= len(text) or text[pos] != "{":
        raise ValueError("Rezepttitel nicht gefunden")
    title, end = balanced(text, pos)
    return clean_latex(title), text[preamble_start:end]


def metadata_value(preamble: str, key: str) -> str:
    match = re.search(rf"\b{re.escape(key)}\s*=\s*\{{", preamble)
    if not match:
        return ""
    start = preamble.find("{", match.start())
    body, _ = balanced(preamble, start)
    return clean_latex(body)


def make_header(title: str, preamble: str) -> str:
    parts: list[str] = []
    portion = metadata_value(preamble, "portion")
    preparation = metadata_value(preamble, "preparationtime")
    baking = metadata_value(preamble, "bakingtime")
    if portion:
        suffix = "" if re.search(r"[A-Za-zÄÖÜäöüß]", portion) else " Portionen"
        parts.append(f"{portion}{suffix}")
    if preparation:
        parts.append(preparation)
    if baking:
        parts.append(baking)
    return f"{title} – {' · '.join(parts)}" if parts else title


def parse_ingredients(text: str) -> list[Ingredient]:
    blocks = command_blocks(text, "ingredients") + command_blocks(text, "ingredientsB")
    ingredients: list[Ingredient] = []
    current_group = ""
    for _, block in blocks:
        block = remove_braced_command(strip_comments(block), "index")
        for raw_row in re.split(r"\\\\(?:\[[^\]]*\])?", block):
            row = raw_row.strip()
            if not row or "Fortsetzung auf" in row or r"\multicolumn" in row:
                continue
            parts = re.split(r"(?<!\\)&", row, maxsplit=1)
            amount = clean_latex(parts[0])
            name = clean_latex(parts[1]) if len(parts) > 1 else ""
            if not name and amount:
                current_group = amount
                continue
            if amount or name:
                ingredients.append(Ingredient(amount=amount, name=name, group=current_group))
    return ingredients


def parse_steps(text: str) -> list[str]:
    blocks = command_blocks(text, "preparation")
    if not blocks:
        return []
    chunks = re.split(r"\\step(?![A-Za-z])", blocks[0][1])
    return [clean_latex(chunk) for chunk in chunks[1:] if clean_latex(chunk)]


def parse_notes(text: str) -> list[tuple[str, str]]:
    notes: list[tuple[str, str]] = []
    for option, body in command_blocks(text, "suggestion"):
        notes.append((clean_latex(option) or "Vorschlag", clean_latex(body)))
    for option, body in command_blocks(text, "hint"):
        notes.append((clean_latex(option) or "Hinweis", clean_latex(body)))
    return [(label, body) for label, body in notes if body]


def normalize(value: str) -> str:
    value = value.lower()
    value = value.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


STOPWORDS = {
    "alternativ",
    "optional",
    "frisch",
    "frische",
    "frischer",
    "gehackt",
    "gemahlen",
    "getrocknet",
    "gross",
    "klein",
    "mittel",
    "nach",
    "packung",
    "prise",
    "scheiben",
    "stangen",
    "stueck",
    "etwas",
    "gesamt",
    "weitere",
    "zum",
    "zur",
}


def stem(word: str) -> str:
    if word in {"ei", "eier"}:
        return "ei"
    if word in {"oel", "oele"}:
        return "oel"
    for suffix in ("ern", "en", "er", "es", "em", "e", "n", "s"):
        if len(word) >= 6 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def keywords(value: str) -> set[str]:
    words = normalize(value).split()
    return {
        stem(word)
        for word in words
        if word not in STOPWORDS and (len(word) >= 3 or word in {"ei", "oel"})
    }


JOIN_WORDS = keywords(
    "zugeben dazugeben hinzufügen einrühren unterrühren untermischen vermengen "
    "mischen mixen pürieren heben verteilen darauf darüber zusammen schichten "
    "belegen füllen bestreichen alles restliche restlichen"
)
FINAL_WORDS = keywords(
    "servieren anrichten toppen backen köcheln köcheln lassen kochen lassen "
    "abkühlen ziehen lassen ruhen lassen einkochen reduzieren garen"
)


def step_ranges(ingredients: list[Ingredient], steps: list[str]) -> list[tuple[int, int]]:
    if not ingredients:
        return [(0, 0) for _ in steps]

    ingredient_words = [keywords(item.name) for item in ingredients]
    group_members: dict[str, set[int]] = {}
    for index, item in enumerate(ingredients):
        if item.group:
            for word in keywords(item.group):
                group_members.setdefault(word, set()).add(index)

    all_rows = set(range(len(ingredients)))
    previous: set[int] = set()
    ranges: list[tuple[int, int]] = []

    for step_text in steps:
        words = keywords(step_text)
        direct: set[int] = set()
        for index, item_words in enumerate(ingredient_words):
            if words & item_words:
                direct.add(index)
        for group_word, members in group_members.items():
            if group_word in words:
                direct.update(members)

        if {"alles", "zutaten"} & words:
            direct.update(all_rows)

        active = set(direct)
        if words & JOIN_WORDS:
            active.update(previous)
        if not active and previous:
            active.update(previous)
        if words & FINAL_WORDS and not direct:
            active.update(previous or all_rows)
        if not active:
            active.update(all_rows)

        previous = active
        ranges.append((min(active), max(active)))

    return ranges


def order_ingredients(ingredients: list[Ingredient], steps: list[str]) -> list[Ingredient]:
    """Sortiert Zutaten nach ihrem ersten Vorkommen im Ablauf.

    Mengen und Bezeichnungen bleiben unverändert; nur die für eine Ablaufmatrix
    notwendige Reihenfolge wird angepasst.
    """

    step_words = [keywords(step) for step in steps]
    ranked: list[tuple[int, int, Ingredient]] = []
    for original_index, ingredient in enumerate(ingredients):
        words = keywords(ingredient.name)
        group_words = keywords(ingredient.group)
        first_use = len(steps)
        for step_index, words_in_step in enumerate(step_words):
            if words_in_step & words or words_in_step & group_words:
                first_use = step_index
                break
        ranked.append((first_use, original_index, ingredient))
    return [item for _, _, item in sorted(ranked, key=lambda entry: (entry[0], entry[1]))]


def grouped_actions(ingredients: list[Ingredient], steps: list[str]) -> list[tuple[int, int, str]]:
    if not steps:
        return [(0, max(0, len(ingredients) - 1), "Keine Zubereitungsschritte eingetragen.")]

    ranges = step_ranges(ingredients, steps)
    count = min(MAX_ACTION_COLUMNS, len(steps))
    actions: list[tuple[int, int, str]] = []
    for column in range(count):
        start = column * len(steps) // count
        end = (column + 1) * len(steps) // count
        selected_steps = steps[start:end]
        selected_ranges = ranges[start:end]
        first_row = min(item[0] for item in selected_ranges)
        last_row = max(item[1] for item in selected_ranges)
        actions.append((first_row, last_row, "<br><br>".join(html.escape(step) for step in selected_steps)))
    return actions


def render(recipe: Recipe) -> str:
    actions = grouped_actions(recipe.ingredients, recipe.steps)
    columns = len(actions)
    ingredient_width = 25
    action_width = (100 - ingredient_width) / max(columns, 1)
    row_count = len(recipe.ingredients)
    density = "dense" if row_count >= 21 or len(recipe.notes) >= 3 else ""

    starts: dict[tuple[int, int], tuple[int, str]] = {}
    occupied: set[tuple[int, int]] = set()
    for column, (first, last, text) in enumerate(actions):
        starts[(first, column)] = (last - first + 1, text)
        for row in range(first + 1, last + 1):
            occupied.add((row, column))

    lines = [
        f'<section class="sheet generated cols-{columns} {density}">',
        '  <table class="recipe-table generated-table">',
        "    <colgroup>",
        f'      <col style="width:{ingredient_width}%">',
    ]
    lines.extend(f'      <col style="width:{action_width:.4f}%">' for _ in actions)
    lines.extend(
        [
            "    </colgroup>",
            "    <thead>",
            f'      <tr><th colspan="{columns + 1}">{html.escape(recipe.header)}</th></tr>',
            "    </thead>",
            "    <tbody>",
        ]
    )

    previous_group = ""
    for row, ingredient in enumerate(recipe.ingredients):
        group_label = ""
        if ingredient.group and ingredient.group != previous_group:
            group_label = f'<span class="ingredient-group-label">{html.escape(ingredient.group)}</span>'
        previous_group = ingredient.group
        amount = f"<b>{html.escape(ingredient.amount)}</b> " if ingredient.amount else ""
        lines.append("      <tr>")
        lines.append(
            f'        <td class="ingredient-cell">{group_label}{amount}{html.escape(ingredient.name)}</td>'
        )
        for column in range(columns):
            key = (row, column)
            if key in starts:
                rowspan, text = starts[key]
                rowspan_attr = f' rowspan="{rowspan}"' if rowspan > 1 else ""
                lines.append(f"        <td{rowspan_attr}>{text}</td>")
            elif key not in occupied:
                lines.append("        <td></td>")
        lines.append("      </tr>")

    for label, body in recipe.notes:
        lines.append(
            f'      <tr class="note-row"><td>{html.escape(label)}</td>'
            f'<td colspan="{columns}">{html.escape(body)}</td></tr>'
        )

    lines.extend(["    </tbody>", "  </table>", "</section>", ""])
    return "\n".join(lines)


def validate_rendered(recipe: Recipe, rendered: str) -> None:
    expected = [recipe.header, *recipe.steps]
    for ingredient in recipe.ingredients:
        expected.extend(part for part in (ingredient.amount, ingredient.name) if part)
    for label, body in recipe.notes:
        expected.extend((label, body))

    missing = [value for value in expected if html.escape(value) not in rendered]
    if missing:
        sample = ", ".join(repr(value) for value in missing[:3])
        raise ValueError(f"Unvollständige Ausgabe für {recipe.title}: {sample}")


def load_recipes() -> list[Recipe]:
    book_text = BOOK.read_text(encoding="utf-8")
    source_names = re.findall(r"^\\input\{(rezepte/[^}]+)\}", book_text, flags=re.MULTILINE)
    recipes: list[Recipe] = []
    for number, source_name in enumerate(source_names, start=1):
        source = ROOT / f"{source_name}.tex"
        text = source.read_text(encoding="utf-8")
        title, preamble = recipe_title_and_preamble(text)
        slug = source.stem
        steps = parse_steps(text)
        ingredients = order_ingredients(parse_ingredients(text), steps)
        recipes.append(
            Recipe(
                number=number,
                source=source,
                slug=slug,
                title=title,
                header=make_header(title, preamble),
                ingredients=ingredients,
                steps=steps,
                notes=parse_notes(text),
            )
        )
    return recipes


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    recipes = load_recipes()
    if not recipes:
        raise SystemExit("Keine eingebundenen Rezepte in book.tex gefunden")

    manifest_entries: list[str] = []
    generated_count = 0
    manual_count = 0
    for recipe in recipes:
        target = OUTPUT / f"{recipe.number:02d}-{recipe.slug}.html"
        manifest_entries.append(target.name)
        if recipe.slug in MANUAL_SLUGS:
            if not target.exists():
                raise SystemExit(f"Handgesetzte Datei fehlt: {target}")
            manual_count += 1
            continue
        rendered = render(recipe)
        validate_rendered(recipe, rendered)
        target.write_text(rendered, encoding="utf-8")
        generated_count += 1

    MANIFEST.write_text("\n".join(manifest_entries) + "\n", encoding="utf-8")
    print(f"Erstellt/aktualisiert: {generated_count} generierte Rezeptdateien")
    print(f"Handgesetzt beibehalten: {manual_count} Rezeptdateien")
    print(f"Gesamt: {len(recipes)} Rezeptdateien")


if __name__ == "__main__":
    main()
