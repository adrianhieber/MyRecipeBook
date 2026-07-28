#!/usr/bin/env python3
"""Normalize and audit index entries in the cookbook's ingredient tables.

The script only touches recipe files that are actively included by book.tex.
Run without arguments to audit and with --write to update the files.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book.tex"

CAT_VEG = r"Gemüse \& Pilze"
CAT_FRUIT = "Obst"
CAT_HERBS = r"Kräuter \& Gewürze"
CAT_LEGUMES = "Hülsenfrüchte"
CAT_GRAINS = r"Getreide, Pasta \& Brot"
CAT_ALTERNATIVES = r"Tofu \& Fleischalternativen"
CAT_DAIRY = r"Milchprodukte \& Alternativen"
CAT_EGGS = "Eier"
CAT_NUTS = r"Nüsse \& Samen"
CAT_PANTRY = r"Vorrat \& Konserven"
CAT_SAUCES = r"Öle, Saucen \& Würzmittel"
CAT_BAKING = r"Backzutaten \& Süßes"
CAT_DRINKS = "Getränke"

INDEX_RE = re.compile(r"\\index\{[^{}]*\}")
INPUT_RE = re.compile(r"^\s*\\input\{(rezepte/[^}]+)\}")


def included_recipes() -> list[Path]:
    paths: list[Path] = []
    for line in BOOK.read_text(encoding="utf-8").splitlines():
        match = INPUT_RE.match(line)
        if match:
            paths.append(ROOT / f"{match.group(1)}.tex")
    return paths


def has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def classify(display: str, amount: str) -> list[tuple[str, str]]:
    """Return all useful canonical index entries for one ingredient row."""

    text = display.lower()
    left = amount.lower()
    entries: list[tuple[str, str]] = []

    def add(category: str, term: str) -> None:
        entry = (category, term)
        if entry not in entries:
            entries.append(entry)

    def add_if(pattern: str, category: str, term: str) -> None:
        if has(text, pattern):
            add(category, term)

    # Gemüse und Pilze
    add_if(r"\bavocado", CAT_FRUIT, "Avocado")
    add_if(r"\bbanane", CAT_FRUIT, "Bananen")
    add_if(r"\bdattel", CAT_FRUIT, "Datteln")
    add_if(r"\berdbeer", CAT_FRUIT, "Erdbeeren")
    add_if(r"\bfeigen?", CAT_FRUIT, "Feigen")
    add_if(r"\bhimbeer", CAT_FRUIT, "Himbeeren")
    add_if(r"\blimette", CAT_FRUIT, "Limetten")
    add_if(r"\borange", CAT_FRUIT, "Orangen")
    add_if(r"\bpreiselbeer", CAT_FRUIT, "Preiselbeeren")
    add_if(r"\bjohannisbeer", CAT_FRUIT, "Johannisbeeren")
    add_if(r"\bapfelsaft", CAT_DRINKS, "Apfelsaft")

    if has(text, r"zitrone|zitronen") and not has(text, r"zitronensäure"):
        add(CAT_FRUIT, "Zitronen")

    add_if(r"\bblumenkohl", CAT_VEG, "Blumenkohl")
    add_if(r"\bbrokkoli", CAT_VEG, "Brokkoli")
    add_if(r"\bfrühlingszwiebel", CAT_VEG, "Frühlingszwiebeln")
    add_if(r"\bgurke\b", CAT_VEG, "Gurken")
    add_if(r"\bingwer", CAT_VEG, "Ingwer")
    add_if(r"\bkarotte|\bmöhre", CAT_VEG, "Karotten")
    add_if(r"\bkartoffeln?", CAT_VEG, "Kartoffeln")
    add_if(r"\bknoblauch(?!pulver)", CAT_VEG, "Knoblauch")
    add_if(r"\bknollensellerie|\bsellerie", CAT_VEG, "Sellerie")
    add_if(r"\bkürbispüree", CAT_PANTRY, "Kürbispüree")
    add_if(r"\blauch\b", CAT_VEG, "Lauch")
    add_if(r"\bpastinake", CAT_VEG, "Pastinaken")
    add_if(r"\bpiquillo", CAT_VEG, "Piquillo-Paprika")
    add_if(r"\bportobello", CAT_VEG, "Portobello")
    add_if(r"\brote beete", CAT_VEG, "Rote Beete")
    add_if(r"\bromana", CAT_VEG, "Romanasalat")
    add_if(r"\brucola", CAT_VEG, "Rucola")
    add_if(r"\bsalat\b", CAT_VEG, "Salat")
    add_if(r"\bschalotte", CAT_VEG, "Schalotten")
    add_if(r"\bshiitake", CAT_VEG, "Shiitake")
    add_if(r"\bshimeji", CAT_VEG, "Shimeji")
    add_if(r"\bspitzpaprika", CAT_VEG, "Spitzpaprika")
    add_if(r"\bsüßkartoffel", CAT_VEG, "Süßkartoffeln")
    add_if(r"\bzwiebel(?!pulver|granulat)", CAT_VEG, "Zwiebeln")
    if has(text, r"\bpilze?\b") and not has(text, r"pilz-würz"):
        add(CAT_VEG, "Pilze")
    if has(text, r"\bpaprika\b") and not has(
        text, r"spitzpaprika|piquillo|paprikapulver|paprikamark"
    ):
        add(CAT_VEG, "Paprika")

    # Tomaten nach ihrer im Vorrat relevanten Form unterscheiden.
    if has(text, r"tomatenmark"):
        add(CAT_PANTRY, "Tomatenmark")
    elif has(text, r"getrocknete tomaten"):
        add(CAT_PANTRY, "Tomaten, getrocknet")
    elif has(text, r"passierte tomaten|gestückelte tomaten|geschälte tomaten|passata|tomatensauce"):
        add(CAT_PANTRY, "Tomaten (Konserve)")
    elif has(text, r"\btomate|\btomaten|\bcherrytomaten"):
        add(CAT_VEG, "Tomaten")

    # Kräuter und Gewürze
    spice_rules = (
        (r"\bbasilikum", "Basilikum"),
        (r"\bbärlauch", "Bärlauch"),
        (r"\bcayenne", "Cayennepfeffer"),
        (r"\bchili(?!öl| in öl)", "Chili"),
        (r"\bcurry", "Curry"),
        (r"\bdill", "Dill"),
        (r"\bgaram masala", "Garam Masala"),
        (r"\bital\. kräuter", "Italienische Kräuter"),
        (r"\bknoblauchpulver", "Knoblauchpulver"),
        (r"\bkoriander", "Koriander"),
        (r"\bkreuzkümmel", "Kreuzkümmel"),
        (r"\bkurkuma", "Kurkuma"),
        (r"\blorbeer", "Lorbeer"),
        (r"\bmajoran", "Majoran"),
        (r"\bmuskat", "Muskat"),
        (r"\bnelken", "Nelken"),
        (r"\bor(e|a)gano", "Oregano"),
        (r"\bpaprikapulver", "Paprikapulver"),
        (r"\bpetersilie", "Petersilie"),
        (r"\bpfeffer", "Pfeffer"),
        (r"\branch gewürz", "Ranch-Gewürzmischung"),
        (r"\brosmarin", "Rosmarin"),
        (r"\bsalbei", "Salbei"),
        (r"\bsalz|\bmeersalz", "Salz"),
        (r"\bschnittlauch", "Schnittlauch"),
        (r"\bsenfkörner", "Senfkörner"),
        (r"\bsumak", "Sumak"),
        (r"\bthymian", "Thymian"),
        (r"\btofugewürz", "Tofu-Gewürz"),
        (r"\bwacholder", "Wacholderbeeren"),
        (r"\bzimt", "Zimt"),
        (r"\bzwiebelgranulat", "Zwiebelgranulat"),
        (r"\bzwiebelpulver", "Zwiebelpulver"),
    )
    for pattern, term in spice_rules:
        add_if(pattern, CAT_HERBS, term)

    # Hülsenfrüchte
    add_if(r"\bbeluga-linsen", CAT_LEGUMES, "Beluga-Linsen")
    add_if(r"\bkichererbsenmehl", CAT_LEGUMES, "Kichererbsenmehl")
    add_if(r"\bkichererbsen\b", CAT_LEGUMES, "Kichererbsen")
    add_if(r"\bkidneybohnen", CAT_LEGUMES, "Kidneybohnen")
    if has(text, r"\blinsen\b") and not has(text, r"beluga"):
        add(CAT_LEGUMES, "Linsen")

    # Getreide, Pasta und Brot
    grain_rules = (
        (r"\bblätterteig", "Blätterteig"),
        (r"\bburger buns", "Burger Buns"),
        (r"\bcouscous", "Couscous"),
        (r"\bfettuccine", "Fettuccine"),
        (r"\bfladenbrot", "Fladenbrot"),
        (r"\bhaferflocken", "Haferflocken"),
        (r"\bhartweizengrieß", "Hartweizengrieß"),
        (r"\bklebreismehl", "Klebreismehl"),
        (r"\blasagneplatten", "Lasagneplatten"),
        (r"\bpanko|semmelbrösel", "Semmelbrösel"),
        (r"\bpenne", "Penne"),
        (r"\bprotein wraps", "Wraps"),
        (r"\bramen", "Ramen"),
        (r"\breispapier", "Reispapier"),
        (r"\brisottoreis", "Risottoreis"),
        (r"\bspaghetti", "Spaghetti"),
        (r"\btagliatelle", "Tagliatelle"),
        (r"\budon", "Udon-Nudeln"),
    )
    for pattern, term in grain_rules:
        add_if(pattern, CAT_GRAINS, term)
    if has(text, r"\bmehl\b|\bweizenmehl") and not has(text, r"kichererbsen|klebreis"):
        add(CAT_GRAINS, "Weizenmehl")
    if has(text, r"\bnudeln?\b") and not has(text, r"ramen|udon"):
        add(CAT_GRAINS, "Pasta")
    if has(text, r"\bpasta\b") and not has(text, r"pastawasser"):
        add(CAT_GRAINS, "Pasta")
    if has(text, r"\breis\b|\bbasmatireis") and not has(text, r"risottoreis|reispapier|reisessig|reiswein"):
        add(CAT_GRAINS, "Reis")
    if has(text, r"zum bestäuben") and has(left, r"mehl"):
        add(CAT_GRAINS, "Weizenmehl")

    # Proteinquellen und Alternativen
    alternative_rules = (
        (r"\bburger-trockenmischung", "Burger-Patty"),
        (r"\bmock duck", "Mock Duck"),
        (r"\bräuchertofu", "Räuchertofu"),
        (r"\bseidentofu", "Seidentofu"),
        (r"\bseitan", "Seitan"),
        (r"\bsojageschnetzeltes", "Sojageschnetzeltes"),
        (r"\bsojamedaillons", "Sojamedaillons"),
        (r"\btofuhack", "Tofuhack"),
        (r"\byuba|tofuhaut", "Yuba"),
    )
    for pattern, term in alternative_rules:
        add_if(pattern, CAT_ALTERNATIVES, term)
    if has(text, r"\btofu\b") and not has(text, r"räuchertofu|seidentofu|tofuhack|tofuhaut"):
        add(CAT_ALTERNATIVES, "Tofu")

    # Milchprodukte und pflanzliche Alternativen
    dairy_rules = (
        (r"\bbuttermilch", "Buttermilch"),
        (r"\bcrème fraîche|creme fraîche", "Crème fraîche"),
        (r"\bfeta", "Feta"),
        (r"\bfrischkäse", "Frischkäse"),
        (r"\bghee", "Ghee"),
        (r"\bjoghurt|\bnaturjoghurt", "Joghurt"),
        (r"\bkäse\b", "Käse"),
        (r"\bkefir", "Kefir"),
        (r"\bkokoscreme", "Kokoscreme"),
        (r"\bkokosmilch", "Kokosmilch"),
        (r"\bmascarpone", "Mascarpone"),
        (r"\bmargarine", "Margarine"),
        (r"\bmozzarella", "Mozzarella"),
        (r"\bparmesan", "Parmesan"),
        (r"\bsojajoghurt", "Sojajoghurt"),
        (r"\bsojamilch", "Sojamilch"),
        (r"\bsojasahne", "Sojasahne"),
        (r"\bvanilleeis", "Vanilleeis"),
    )
    for pattern, term in dairy_rules:
        add_if(pattern, CAT_DAIRY, term)
    if has(text, r"\bvegane butter"):
        add(CAT_DAIRY, "Vegane Butter")
    elif has(text, r"\bbutter\b") and not has(text, r"erdnussbutter"):
        add(CAT_DAIRY, "Butter")
    if has(text, r"\bpflanzliche sahne|\bvegane sahne"):
        add(CAT_DAIRY, "Pflanzliche Sahne")
    elif has(text, r"\bsahne\b") and not has(text, r"sojasahne|saure sahne"):
        add(CAT_DAIRY, "Sahne")
    add_if(r"\bsaure sahne", CAT_DAIRY, "Saure Sahne")
    if has(text, r"\bmilch\b|\bvollmilch") and not has(text, r"kokosmilch|sojamilch|buttermilch"):
        add(CAT_DAIRY, "Milch")

    # Eier
    add_if(r"\beigelb", CAT_EGGS, "Eigelb")
    add_if(r"\beierersatz", CAT_EGGS, "Eierersatz")
    add_if(r"\bleinsamen-eier", CAT_EGGS, "Leinsamen-Eier")
    if has(text, r"\bei\b|\beier\b") and not has(text, r"eigelb|eierersatz|leinsamen"):
        add(CAT_EGGS, "Eier")

    # Nüsse und Samen
    nut_rules = (
        (r"\bcashew", "Cashews"),
        (r"\berdnuss", "Erdnüsse"),
        (r"\bkokosraspeln", "Kokos"),
        (r"\bkürbiskern", "Kürbiskerne"),
        (r"\bleinsamen", "Leinsamen"),
        (r"\bmandel", "Mandeln"),
        (r"\bnussmischung", "Nussmischung"),
        (r"\bpistaz", "Pistazien"),
        (r"\bsesam(?!öl)", "Sesam"),
        (r"\bwaln", "Walnüsse"),
    )
    for pattern, term in nut_rules:
        add_if(pattern, CAT_NUTS, term)

    # Vorrat und Konserven
    pantry_rules = (
        (r"\bapfelmus", "Apfelmus"),
        (r"\bgemüsebrühe", "Gemüsebrühe"),
        (r"\bhefeflocken", "Hefeflocken"),
        (r"\bkapern", "Kapern"),
        (r"\bmais\b", "Mais"),
        (r"\bpaprikamark", "Paprikamark"),
        (r"\boliven\b", "Oliven"),
        (r"\bessiggurken", "Essiggurken"),
    )
    for pattern, term in pantry_rules:
        add_if(pattern, CAT_PANTRY, term)

    # Öle, Saucen und Würzmittel
    sauce_rules = (
        (r"\bagavendicksaft", "Agavendicksaft"),
        (r"\bahornsirup", "Ahornsirup"),
        (r"\bapfelessig", "Apfelessig"),
        (r"\bbalsamico", "Balsamico"),
        (r"\bburgersauce", "Burgersauce"),
        (r"\bchili in öl", "Chiliöl"),
        (r"\bchiliöl", "Chiliöl"),
        (r"\bessig\b", "Essig"),
        (r"\bgranatapfelsirup", "Granatapfelsirup"),
        (r"\bhonig", "Honig"),
        (r"\bketchup", "Ketchup"),
        (r"\bmelasse", "Melasse"),
        (r"\bmiso", "Miso"),
        (r"\bmsg", "MSG"),
        (r"\bpilz-würzsoße|austernsoße", "Pilz-Würzsauce"),
        (r"\breisessig|reisweinessig", "Reisessig"),
        (r"\brotweinessig", "Rotweinessig"),
        (r"\bsenf\b", "Senf"),
        (r"\bsesamöl", "Sesamöl"),
        (r"\bsojasauce|\bsojasoße", "Sojasauce"),
        (r"\bsriracha", "Sriracha"),
        (r"\btahin", "Tahin"),
        (r"\bteriyaki", "Teriyakisauce"),
    )
    for pattern, term in sauce_rules:
        add_if(pattern, CAT_SAUCES, term)
    if has(text, r"\bolivenöl"):
        add(CAT_SAUCES, "Olivenöl")
    if has(text, r"\bkokosöl"):
        add(CAT_SAUCES, "Kokosöl")
    if has(text, r"\böl\b|\bpflanzenöl") and not has(text, r"olivenöl|kokosöl|sesamöl|chiliöl| in öl"):
        add(CAT_SAUCES, "Pflanzenöl")

    # Backzutaten und Süßes
    baking_rules = (
        (r"\bbackpulver", "Backpulver"),
        (r"\bkakao", "Kakaopulver"),
        (r"\bkartoffelstärke", "Kartoffelstärke"),
        (r"\bmaisstärke|\bspeisestärke", "Speisestärke"),
        (r"\bmarzipan", "Marzipan"),
        (r"\bnatron", "Natron"),
        (r"schokolade|schokodrops", "Schokolade"),
        (r"\btrockenhefe", "Trockenhefe"),
        (r"\bzitronensäure", "Zitronensäure"),
    )
    for pattern, term in baking_rules:
        add_if(pattern, CAT_BAKING, term)
    if has(text, r"\bpuderzucker"):
        add(CAT_BAKING, "Puderzucker")
    elif has(text, r"\bvanillezucker"):
        add(CAT_BAKING, "Vanillezucker")
    elif has(text, r"\bzucker"):
        add(CAT_BAKING, "Zucker")
    if has(text, r"\bvanille") and not has(text, r"vanillezucker|vanilleeis"):
        add(CAT_BAKING, "Vanille")

    # Getränke und Flüssigkeiten
    drink_rules = (
        (r"\bespresso", "Espresso"),
        (r"\bkaffee", "Kaffee"),
        (r"\bmateblätter", "Mate"),
        (r"\bportwein", "Portwein"),
        (r"\brotwein\b", "Rotwein"),
        (r"\bweißwein", "Weißwein"),
        (r"\bwasser|\bpastawasser", "Wasser"),
    )
    for pattern, term in drink_rules:
        add_if(pattern, CAT_DRINKS, term)

    return sorted(entries, key=lambda item: (item[0].casefold(), item[1].casefold()))


def normalize_file(path: Path, write: bool) -> tuple[int, list[tuple[int, str]]]:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    output: list[str] = []
    inside = False
    indexed_rows = 0
    unmatched: list[tuple[int, str]] = []

    for lineno, original in enumerate(lines, start=1):
        line = original
        if re.search(r"\\ingredientsB?\{", line):
            inside = True

        if (
            inside
            and "&" in line
            and not line.lstrip().startswith("%")
            and r"\textbf{" not in line
        ):
            clean = INDEX_RE.sub("", line)
            left, right = clean.split("&", maxsplit=1)
            display = re.split(r"\\\\", right, maxsplit=1)[0].strip()
            entries = classify(display, left.strip())
            if not entries:
                unmatched.append((lineno, display or clean.strip()))
            else:
                tags = "".join(
                    rf"\index{{{category}!{term}}}" for category, term in entries
                )
                if r"\\" in clean:
                    clean = clean.replace(r"\\", tags + r"\\", 1)
                else:
                    ending = "\n" if clean.endswith("\n") else ""
                    clean = clean.removesuffix("\n") + tags + ending
                line = clean
                indexed_rows += 1

        output.append(line)
        if inside and line.lstrip().startswith("}"):
            inside = False

    if write and output != lines:
        path.write_text("".join(output), encoding="utf-8")
    return indexed_rows, unmatched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write", action="store_true", help="rewrite ingredient index entries"
    )
    args = parser.parse_args()

    total_rows = 0
    all_unmatched: list[tuple[Path, int, str]] = []
    for path in included_recipes():
        rows, unmatched = normalize_file(path, args.write)
        total_rows += rows
        all_unmatched.extend((path, line, text) for line, text in unmatched)

    mode = "updated" if args.write else "audited"
    print(f"{mode}: {len(included_recipes())} recipes, {total_rows} indexed rows")
    for path, line, text in all_unmatched:
        print(f"UNMATCHED {path.relative_to(ROOT)}:{line}: {text}")
    if all_unmatched:
        print(f"{len(all_unmatched)} ingredient rows need a classification")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
