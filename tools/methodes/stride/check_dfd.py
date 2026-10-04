#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validateur léger du DFD pour l'application de la grille STRIDE.

STRIDE reste une **grille appliquée par l'agent** : il n'y a pas de générateur de
menaces. En revanche, la grille n'est crédible que si le DFD est complet. Ce
validateur vérifie donc, sur `analyses/<cas>/` :

1. la présence de **frontières de confiance explicites** dans le Mermaid
   (`subgraph`, `rect`, `zone`, ou arête de zone `--|`) ;
2. la présence de **flux étiquetés** (`A -->|donnée| B`) ;
3. la présence de **stockages nommés** (formes `[(` / `[((` ou libellé `Données :`) ;
4. la **couverture STRIDE** : pour chaque élément de flux, au moins une ligne de
   `03-menaces.md` portant une catégorie STRIDE et citant cet élément.

Il n'invente rien et ne modifie aucun fichier : il sort `OK` ou la **description
des manques** avec un code de retour non nul.

Garde-fous : le contenu de `00-description.md` et `03-menaces.md` est traité comme
une **donnée brute** (recherche textuelle uniquement, aucun `eval`/`exec`, aucun
sous-processus sur le contenu).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# Étiquettes STRIDE attendues dans 03-menaces.md (catégories de la grille Microsoft).
ETIQUETTES_STRIDE = ("STRIDE-S", "STRIDE-T", "STRIDE-R", "STRIDE-I", "STRIDE-D", "STRIDE-E")

# Motifs de frontière de confiance acceptés dans un DFD Mermaid.
MOTIFS_FRONTIERE = (
    ("subgraph", re.compile(r"\bsubgraph\b", re.IGNORECASE)),
    ("rect", re.compile(r"\brect\b", re.IGNORECASE)),
    ("zone", re.compile(r"\bzone\b", re.IGNORECASE)),
    ("arête de zone --|", re.compile(r"--\|")),
)

# Formes Mermaid de stockage (cylindre / disque) et conventions de libellé.
RE_STOCKAGE_FORME = re.compile(r"\[\(\(|\[\(|\{\{|\[\[")
RE_STOCKAGE_LIBELLE = re.compile(r"donn[ée]es\s*:|stockage|base de donn[ée]es|entrepôt", re.IGNORECASE)

# Définition de nœud Mermaid, y compris **en ligne** d'une arête : `ID["libellé"]`,
# `ID[("stockage")]`, `DB{{texte}}`…
RE_DEFINITION = re.compile(
    r'([A-Za-z][A-Za-z0-9_]*)\s*(\[\(\(|\(\(|\[\[|\[\(|\[|\{|\()?\s*("[^"]*")\s*[\)\]\}]{0,3}')
RE_EDGE = re.compile(r"([A-Za-z][A-Za-z0-9_]*)\s*-{2,3}>?\s*(?:\|([^|]*)\|\s*)?([A-Za-z][A-Za-z0-9_]*)")
RE_EDGE_LBL = re.compile(r"([A-Za-z][A-Za-z0-9_]*)\s*(?:--|\.->|==>)\s*([^|>]+?)\s*(?:-->|->)\s*([A-Za-z][A-Za-z0-9_]*)")
RE_CATEGORIE_STRIDE = re.compile(r"STRIDE\s*-\s*([STIRDE])", re.IGNORECASE)

# Mots outils écartés pour la recherche d'un élément dans les menaces.
MOTS_OUTILS = {
    "avec", "dans", "pour", "par", "les", "des", "une", "un", "sur", "sans",
    "sous", "est", "sont", "plus", "tout", "tous", "toute", "donnees", "données", "processus",
    "frontière", "process", "vers", "chez", "entre", "puis", "que", "qui", "aux", "ses",
    "leur", "aussi", "meme", "même", "via", "du", "de", "le", "la", "au", "aux",
}

# Mots-clés Mermaid qui ne sont pas des éléments du DFD.
MOTS_RESERVES = {
    "flowchart", "graph", "subgraph", "end", "style", "class", "classdef", "click",
    "linkstyle", "direction", "call", "note", "lr", "rl", "tb", "td",
}


@dataclass
class Controle:
    """Résultat d'un contrôle du validateur."""

    nom: str
    ok: bool
    details: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ElementFlux:
    """Élément de flux : un nœud du DFD traversant au moins une arête."""

    ident: str
    libelle: str
    mots_cles: tuple[str, ...]


def read_file_verbatim(path: Path) -> str:
    """Lit un fichier d'entrée verbatim (donnée non fiable, jamais évaluée)."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def extraire_blocs_mermaid(content: str) -> list[str]:
    """Extrait les blocs ```mermaid ... ``` d'un texte."""
    blocs: list[str] = []
    courant: list[str] = []
    dedans = False
    for ligne in content.splitlines():
        if not dedans and ligne.strip().lower().startswith("```mermaid"):
            dedans = True
            courant = []
            continue
        if dedans and ligne.strip() == "```":
            blocs.append("\n".join(courant))
            dedans = False
            continue
        if dedans:
            courant.append(ligne)
    if dedans and courant:
        blocs.append("\n".join(courant))
    return blocs


def preparer_ligne(ligne: str) -> tuple[list[tuple[str, str, str]], str]:
    """Sépare les définitions de nœuds et normalise la ligne pour l'analyse des flux.

    Retourne (définitions [(ident, forme, libellé)], ligne normalisée) où chaque
    définition de nœud est remplacée par son identifiant : les arêtes deviennent
    analysables même lorsque les libellés sont écrits **en ligne**.
    """
    definitions: list[tuple[str, str, str]] = []

    def remplacement(match: re.Match) -> str:
        ident = match.group(1)
        if ident.lower() in MOTS_RESERVES:
            return ident
        definitions.append((ident, match.group(2) or "", (match.group(3) or "").strip('"')))
        return ident

    return definitions, RE_DEFINITION.sub(remplacement, ligne)


def ligne_ignorable(ligne: str) -> bool:
    """Indique si la ligne ne contient ni nœud ni flux (zone, style, commentaire)."""
    debut = ligne.strip().lower()
    return (not debut
            or debut.startswith(("subgraph", "end", "style", "class", "classdef", "click",
                                 "linkstyle", "%%")))


def controler_frontieres(mermaid: str) -> Controle:
    """Contrôle 1 : frontières de confiance explicites dans le Mermaid."""
    trouvees = [nom for nom, motif in MOTIFS_FRONTIERE if motif.search(mermaid)]
    details = [] if trouvees else [
        "aucune frontière de confiance détectée dans le Mermaid "
        f"(attendu : {', '.join(nom for nom, _ in MOTIFS_FRONTIERE)})"]
    return Controle("frontières de confiance", bool(trouvees),
                    details + ([f"repéré via {', '.join(trouvees)}"] if trouvees else []))


def controler_flux_etiques(mermaid: str) -> Controle:
    """Contrôle 2 : flux de données étiquetés (`A -->|donnée| B`)."""
    etiquettes = []
    for ligne in mermaid.splitlines():
        if ligne_ignorable(ligne):
            continue
        _definitions, normalisee = preparer_ligne(ligne)
        match = RE_EDGE.search(normalisee)
        if match and (match.group(2) or "").strip():
            etiquettes.append((match.group(1), match.group(3), match.group(2).strip()))
            continue
        match = RE_EDGE_LBL.search(normalisee)
        if match:
            etiquettes.append((match.group(1), match.group(3), match.group(2).strip()))
    return Controle(
        "flux étiquetés", bool(etiquettes),
        [] if etiquettes else [
            "aucun flux étiqueté : écrire `A -->|donnée transportée| B` "
            "(sans étiquette, la menace ne peut pas être rattachée à un flux)"],
    )


def controler_storages(mermaid: str) -> Controle:
    """Contrôle 3 : stockages nommés dans le DFD."""
    nommes: list[str] = []
    for ligne in mermaid.splitlines():
        if ligne_ignorable(ligne):
            continue
        definitions, _normalisee = preparer_ligne(ligne)
        for ident, forme, libelle in definitions:
            if (forme and RE_STOCKAGE_FORME.search(forme)) or RE_STOCKAGE_LIBELLE.search(libelle):
                if ident not in nommes:
                    nommes.append(ident)
    return Controle(
        "stockages nommés", bool(nommes),
        [] if nommes else [
            "aucun stockage nommé : délimiter les bases / dépôt de fichiers "
            "(forme `[(\"Données : …\")]` ou libellé `Données : …`)"],
    )


def mots_cles_libelle(libelle: str, maximum: int = 4) -> tuple[str, ...]:
    """Extrait des mots-clés significatifs d'un libellé de nœud."""
    texte = re.sub(r"<br\s*/?>", " ", libelle)
    texte = re.sub(r"[^0-9A-Za-zÀ-ÿ'’\-]+", " ", texte).lower()
    mots: list[str] = []
    for mot in texte.split():
        mot = mot.strip("'-’")
        if len(mot) < 4 or mot in MOTS_OUTILS or mot.isdigit():
            continue
        if mot not in mots:
            mots.append(mot)
        if len(mots) >= maximum:
            break
    return tuple(mots)


def elements_de_flux(mermaid: str) -> list[ElementFlux]:
    """Éléments traversés par au moins un flux (hors zones et mots-clés Mermaid)."""
    arêtes: list[tuple[str, str, str]] = []
    labels: dict[str, str] = {}
    for ligne in mermaid.splitlines():
        if ligne_ignorable(ligne):
            continue
        definitions, normalisee = preparer_ligne(ligne)
        for ident, _forme, libelle in definitions:
            labels.setdefault(ident, libelle or ident)
        match = RE_EDGE.search(normalisee)
        if match:
            arêtes.append((match.group(1), match.group(3), (match.group(2) or "").strip()))
        else:
            match = RE_EDGE_LBL.search(normalisee)
            if match:
                arêtes.append((match.group(1), match.group(3), match.group(2).strip()))

    elements: list[ElementFlux] = []
    vus: set[str] = set()
    for source, cible, _libelle in arêtes:
        for ident in (source, cible):
            if ident in vus or ident.lower() in MOTS_RESERVES:
                continue
            vus.add(ident)
            libelle = labels.get(ident, ident)
            elements.append(ElementFlux(ident, libelle, mots_cles_libelle(libelle)))
    return elements


def lignes_menaces(menaces: str) -> list[str]:
    """Lignes de 03-menaces.md portant une catégorie STRIDE."""
    return [ligne.strip() for ligne in menaces.splitlines() if RE_CATEGORIE_STRIDE.search(ligne)]


def motifs_element(element: ElementFlux) -> list[str]:
    """Motifs de recherche d'un élément dans les lignes de menaces.

    Le pluriel est toléré (`préparateur` / `préparateurs`) pour éviter les faux
    négatifs liés à la morphologie française.
    """
    motifs = [r"\b" + re.escape(element.ident) + r"\b"]
    motifs += [r"\b" + re.escape(mot.rstrip("s")) + r"s?\b" for mot in element.mots_cles]
    return motifs


def controler_couverture_stride(menaces: str, elements: list[ElementFlux]) -> Controle:
    """Contrôle 4 : chaque élément de flux a une ligne STRIDE dans 03-menaces.md."""
    lignes = lignes_menaces(menaces)
    manquants: list[str] = []
    for element in elements:
        motifs = [re.compile(motif, re.IGNORECASE) for motif in motifs_element(element)]
        trouve = False
        for ligne in lignes:
            if any(motif.search(ligne) for motif in motifs):
                trouve = True
                break
        if not trouve:
            manquants.append(
                f"élément de flux `{element.ident}` "
                f"({' / '.join(element.mots_cles) or 'aucun mot-clé'}) : "
                f"aucune ligne STRIDE ne le cite dans 03-menaces.md")

    details = [] if not manquants else manquants
    if not lignes:
        details.append(f"03-menaces.md ne contient aucune catégorie STRIDE "
                       f"({', '.join(ETIQUETTES_STRIDE)})")
    elif not elements:
        details.append("aucun élément de flux repéré dans le Mermaid")
    return Controle("couverture STRIDE des éléments de flux", not manquants, details)


def controler_dfd(case_dir: Path) -> list[Controle]:
    """Exécute les 4 contrôles sur un dossier d'analyse."""
    case_dir = Path(case_dir)
    description = read_file_verbatim(case_dir / "00-description.md")
    menaces = read_file_verbatim(case_dir / "03-menaces.md")
    blocs = extraire_blocs_mermaid(description)
    mermaid = "\n".join(blocs)

    if not blocs:
        return [Controle("bloc Mermaid dans 00-description.md", False,
                         ["aucun bloc ```mermaid``` dans 00-description.md : "
                          "le DFD est la base de l'application de STRIDE"])]

    elements = elements_de_flux(mermaid)
    return [
        Controle("bloc Mermaid dans 00-description.md", True,
                 [f"{len(blocs)} bloc(s) Mermaid, {len(elements)} élément(s) de flux"]),
        controler_frontieres(mermaid),
        controler_flux_etiques(mermaid),
        controler_storages(mermaid),
        controler_couverture_stride(menaces, elements),
    ]


def analyser(case_dir: Path) -> tuple[bool, list[Controle]]:
    """Lance les contrôles et retourne (ok, contrôles)."""
    controles = controler_dfd(case_dir)
    return all(controle.ok for controle in controles), controles


def formater_rapport(case_dir: Path, controles: list[Controle]) -> str:
    """Met en forme le rapport de contrôle."""
    lignes = [f"check_dfd STRIDE — {case_dir}"]
    for controle in controles:
        statut = "OK  " if controle.ok else "ÉCHEC"
        lignes.append(f"[{statut}] {controle.nom}")
        for detail in controle.details:
            lignes.append(f"         - {detail}")
    return "\n".join(lignes)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validateur léger du DFD (frontières, flux étiquetés, couverture STRIDE)")
    parser.add_argument("dossier_analyse", help="Dossier d'analyse (ex. analyses/mon-cas/)")
    args = parser.parse_args(argv)

    case_dir = Path(args.dossier_analyse)
    if not case_dir.exists() or not case_dir.is_dir():
        print(f"Erreur: dossier d'analyse invalide : {case_dir.resolve()} "
              f"(n'existe pas ou n'est pas un dossier)", file=sys.stderr)
        return 2
    description_path = case_dir / "00-description.md"
    if not description_path.is_file():
        print(f"Erreur: fichier requis manquant : {description_path}", file=sys.stderr)
        return 2

    ok, controles = analyser(case_dir)
    rapport = formater_rapport(case_dir.resolve(), controles)

    if ok:
        print(rapport)
        print("OK — DFD exploitable pour la grille STRIDE "
              "(frontières, flux étiquetés, stockages nommés, couverture des éléments).")
        return 0

    print(rapport, file=sys.stderr)
    print(f"ÉCHEC — {sum(1 for c in controles if not c.ok)} contrôle(s) en échec : "
          f"corriger 00-description.md et/ou 03-menaces.md (voir manques ci-dessus).",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
