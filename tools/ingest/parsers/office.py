# -*- coding: utf-8 -*-
"""Parseurs bureautiques et texte : XLSX, CSV, DOCX, PPTX, TXT/MD.

Choix documenté pour les formules (XLSX) : le parseur lit le classeur avec
`data_only=False`, donc une cellule de formule est restituée **telle quelle**
(`=2+2`). Aucune évaluation n'est faite par l'outil — une formule est une
DONNÉE, jamais du code à exécuter. (`data_only=True` renverrait `None` ici :
openpyxl n'évalue rien et aucun tableur n'a jamais calculé la valeur.)
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

from . import commun

# Garde-fou CSV : limite la taille du bloc « source brute » réécrite en mémoire.
TAILLE_MAX_BLOC_BRUT = 200_000


# --------------------------------------------------------------------------- XLSX

def parse_xlsx(chemin, meta: dict) -> str:
    """Chaque feuille devient une section, chaque plage une section tableau."""
    import openpyxl

    classeur = openpyxl.load_workbook(chemin, data_only=False, read_only=True)
    try:
        sections = []
        for feuille in classeur.worksheets:
            lignes = []
            for ligne in feuille.iter_rows(values_only=True):
                lignes.append(["" if c is None else c for c in ligne])
            if not any(any(str(c).strip() for c in l) for l in lignes):
                sections.append(f"## Feuille « {feuille.title} »\n\n*(feuille vide)*")
                continue
            _signaler_formules(lignes, meta, feuille.title)
            bloc = commun.bloc_tableau(f"## Feuille « {feuille.title} »", lignes, meta)
            if bloc:
                sections.append(bloc)
        return "\n\n".join(sections)
    finally:
        classeur.close()


def _signaler_formules(lignes, meta: dict, titre: str) -> None:
    """Journalise les cellules ressemblant à une formule (conservées telles quelles)."""
    compteurs = [
        (i + 1, j + 1, str(c))
        for i, ligne in enumerate(lignes)
        for j, c in enumerate(ligne)
        if commun.cellules_formule(str(c))
    ]
    if not compteurs:
        return
    exemples = ", ".join(f"{c} (ligne {i}, colonne {j})" for i, j, c in compteurs[:3])
    commun.avertir(
        meta,
        f"Feuille « {titre} » : {len(compteurs)} cellule(s) de type formule conservée(s) "
        f"comme donnée, sans évaluation : {exemples}",
    )


# --------------------------------------------------------------------------- CSV

def parse_csv(chemin, meta: dict) -> str:
    """CSV/TSV : détection du délimiteur puis tableau markdown + source brute."""
    with open(chemin, "rb") as fichier:
        return parse_bytes(Path(chemin).name, fichier.read(), meta)


def parse_csv_bytes(nom: str, donnees: bytes, meta: dict) -> str:
    return parse_bytes(nom, donnees, meta)


def parse_bytes(nom: str, donnees: bytes, meta: dict) -> str:
    """Entrée générique depuis des octets (membre d'archive, zéro écriture disque).

    Les OOXML sont réellement **parsés depuis la mémoire** : sans ce dispatch, un
    membre `.docx`/`.pptx`/`.xlsx` d'un ZIP retombait sur `_texte()`, qui déversait
    le binaire décodé latin-1 dans l'intrant (régression T-ING-11).
    """
    bas = nom.lower()
    if bas.endswith((".csv", ".tsv")):
        return _csv(nom, donnees, meta)
    if bas.endswith(".docx"):
        return parse_docx(io.BytesIO(donnees), meta)
    if bas.endswith(".pptx"):
        return parse_pptx(io.BytesIO(donnees), meta)
    if bas.endswith((".xlsx", ".xlsm")):
        return parse_xlsx(io.BytesIO(donnees), meta)
    return _texte(nom, donnees, meta)


def _decoder(donnees: bytes) -> str:
    """UTF-8 (avec BOM) puis repli latin-1 : aucun document ne fait échouer l'extraction."""
    for encodage in ("utf-8-sig", "latin-1"):
        try:
            return donnees.decode(encodage)
        except UnicodeDecodeError:
            continue
    return donnees.decode("utf-8", errors="replace")


def _csv(nom: str, donnees: bytes, meta: dict) -> str:
    texte = _decoder(donnees)
    delimiteur = _detecter_delimiteur(texte)
    lignes = list(csv.reader(io.StringIO(texte, newline=""), delimiter=delimiteur))
    lignes = [l for l in lignes if any(c.strip() for c in l)]
    if not lignes:
        return ""
    nom_delimiteur = {"\t": "tabulation", "|": "barre verticale"}.get(delimiteur, delimiteur)
    parties = [f"## CSV — {nom}", f"Délimiteur détecté : `{nom_delimiteur}`"]
    bloc = commun.bloc_tableau("", lignes, meta)
    if bloc:
        parties.append(bloc)
    # Copie brute delimited : garantit la fidélité (cellules vides, guillemets, sauts).
    if len(texte) <= TAILLE_MAX_BLOC_BRUT:
        parties.append(
            "<!-- Texte brut de la source (donnée verbatim, non interprétée) -->\n\n"
            "```text\n" + texte.replace("\r\n", "\n").replace("\r", "\n").strip("\n") + "\n```"
        )
    else:
        commun.avertir(meta, "Source CSV volumineuse : bloc brut omis (tableau conservé)")
    return "\n\n".join(parties)


def _detecter_delimiteur(texte: str) -> str:
    """Choisit `;`, `,` ou tabulation d'après l'en-tête, puis d'après tout le texte."""
    echantillon = "\n".join(texte.split("\n")[:20])
    try:
        return csv.Sniffer().sniff(echantillon, delimiters=";,\t|").delimiter
    except csv.Error:
        pass
    compteurs = {d: echantillon.count(d) for d in (";", ",", "\t", "|")}
    meilleur = max(compteurs, key=lambda d: (compteurs[d], d == "\t"))
    return meilleur if compteurs[meilleur] else ","


# --------------------------------------------------------------------------- DOCX

def parse_docx(chemin, meta: dict) -> str:
    """Paragraphes (titres mis en forme) puis tableaux du document Word."""
    import docx

    document = docx.Document(chemin)
    parties = []
    index_tableau = 0
    for bloc in _blocs_docx(document):
        genre, valeur = bloc
        if genre == "paragraphe":
            style = (valeur.style.name or "") if valeur.style is not None else ""
            texte = commun.normaliser(valeur.text)
            if not texte:
                continue
            niveau = _niveau_titre(style)
            if niveau:
                parties.append("#" * min(niveau + 2, 6) + " " + texte)
            elif style.lower() == "title":
                parties.append("## " + texte)
            else:
                parties.append(texte)
        else:
            index_tableau += 1
            lignes = [[cell.text for cell in ligne.cells] for ligne in valeur.rows]
            bloc_md = commun.bloc_tableau(f"### Tableau {index_tableau}", lignes, meta)
            if bloc_md:
                parties.append(bloc_md)
    return "\n\n".join(parties)


def _niveau_titre(style: str) -> int | None:
    """ Traduit « Heading 2 » / « Titre 2 » en niveau de titre markdown (0 = aucun)."""
    lowered = style.lower()
    for marqueur in ("heading", "titre"):
        if lowered.startswith(marqueur):
            chiffres = "".join(c for c in lowered if c.isdigit())
            return int(chiffres) if chiffres else 1
    return None


def _blocs_docx(document):
    """Itère paragraphes et tableaux dans l'ordre du document (python-docx n'a pas d'API d'ordre)."""
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    corps = document.element.body
    for enfant in corps.iterchildren():
        if enfant.tag.endswith("}p"):
            yield "paragraphe", Paragraph(enfant, document)
        elif enfant.tag.endswith("}tbl"):
            yield "tableau", Table(enfant, document)


# --------------------------------------------------------------------------- PPTX

def parse_pptx(chemin, meta: dict) -> str:
    """Textes, tableaux et notes de chaque diapositive."""
    from pptx import Presentation

    presentation = Presentation(chemin)
    sections = []
    for numero, diapo in enumerate(presentation.slides, 1):
        parties = [f"## Diapositive {numero}"]
        index_tableau = 0
        for forme in diapo.shapes:
            if getattr(forme, "has_text_frame", False):
                for paragraphe in forme.text_frame.paragraphs:
                    texte = commun.normaliser("".join(r.text for r in paragraphe.runs) or paragraphe.text)
                    if texte:
                        retrait = "  " * min(paragraphe.level, 3)
                        parties.append(f"{retrait}- {texte}" if paragraphe.level else texte)
            elif getattr(forme, "has_table", False):
                index_tableau += 1
                lignes = [[cell.text for cell in ligne.cells] for ligne in forme.table.rows]
                bloc = commun.bloc_tableau(f"### Tableau {index_tableau}", lignes, meta)
                if bloc:
                    parties.append(bloc)
        notes = ""
        try:
            if diapo.has_notes_slide:
                notes = commun.normaliser(diapo.notes_slide.notes_text_frame.text)
        except Exception:
            notes = ""
        if notes:
            parties.append("### Notes\n\n" + notes)
        sections.append("\n\n".join(parties))
    return "\n\n".join(sections)


# --------------------------------------------------------------------------- TXT

def parse_txt(chemin, meta: dict) -> str:
    """TXT/MD : passe-plat intégral (aucun contenu tronqué)."""
    with open(chemin, "rb") as fichier:
        return parse_txt_bytes(Path(chemin).name, fichier.read(), meta)


def parse_txt_bytes(nom: str, donnees: bytes, meta: dict) -> str:
    return _texte(nom, donnees, meta)


def _texte(nom: str, donnees: bytes, meta: dict) -> str:
    if _est_binaire(donnees):
        # Garde-fou : jamais d'octets binaires déversés dans un intrant Markdown
        # (un fichier renommé `.txt` ne doit pas polluer le brouillon de l'étape 1).
        commun.avertir(meta, f"Fichier binaire non analysable (contenu ignoré) : {nom}")
        return f"## Contenu — {nom}\n\n*(contenu binaire non exploitable)*"
    texte = commun.normaliser(_decoder(donnees))
    return f"## Contenu — {nom}\n\n{texte}" if texte else f"## Contenu — {nom}\n\n*(fichier vide)*"


def _est_binaire(donnees: bytes) -> bool:
    """Vrai si le bloc ressemble à du binaire : octet nul ou trop de contrôles."""
    if not donnees:
        return False
    if b"\x00" in donnees:
        return True
    # Octets de contrôle hors tabulation / retour ligne / form feed.
    controles = sum(1 for octet in donnees if octet < 9 or 13 < octet < 32)
    return controles / len(donnees) > 0.02