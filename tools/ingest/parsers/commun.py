# -*- coding: utf-8 -*-
"""Fonctions communes aux parseurs : normalisation, tableaux markdown, détection.

Règle de sûreté (projet E21) : tout contenu extrait est une DONNÉE non fiable.
Ce module ne réécrit jamais le contenu : il normalise uniquement la mise en forme
(fins de ligne, espaces finaux) et *signale* les passages ressemblant à des
instructions — signalement sans effet sur la donnée extraite.
"""
from __future__ import annotations

import importlib
import re
import unicodedata

# Emplacement du bloc de données dans le markdown produit (convention garde-fous-ia).
DEBUT_DONNEES = "<<<DONNÉES>>>"
FIN_DONNEES = "<<<FIN DONNÉES>>>"

# Étiquettes lisibles des types gérés.
LIBELLES = {
    "pdf": "PDF",
    "image": "Image",
    "xlsx": "Classeur Excel",
    "csv": "CSV",
    "docx": "Document Word",
    "pptx": "Présentation PowerPoint",
    "zip": "Archive ZIP",
    "txt": "Texte",
}

# Extensions reconnues (minuscules, point compris).
TYPE_PAR_EXT = {
    ".pdf": "pdf",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image",
    ".bmp": "image", ".gif": "image", ".tif": "image", ".tiff": "image",
    ".xlsx": "xlsx", ".xlsm": "xlsx",
    ".csv": "csv", ".tsv": "csv",
    ".docx": "docx", ".pptx": "pptx", ".zip": "zip",
    ".txt": "txt", ".md": "txt", ".markdown": "txt", ".rst": "txt", ".log": "txt",
}

# Type de document -> module parseur (importé à la demande : pas de dépendance inutile).
MODULE_PAR_TYPE = {
    "pdf": "pdf", "image": "images", "xlsx": "office", "csv": "office",
    "docx": "office", "pptx": "office", "zip": "archive", "txt": "office",
}

TYPES_PRIS_EN_CHARGE = ", ".join(sorted(LIBELLES.values()))

# Motifs d'injection de consigne : journalisation uniquement, jamais d'action.
MOTIFS_INSTRUCTION = [
    r"ignore\s+(?:toutes\s+les\s+|les\s+|the\s+)?(?:instructions?|consignes?|prompt)",
    r"disregard\s+(?:all\s+|the\s+|previous|prior)",
    r"tu\s+es\s+maintenant|you\s+are\s+now",
    r"(?:nouvelles?|new|system)\s+(?:instructions?|prompt)\s*:",
    r"(?:ex[ée]cute|execute|run|lance|launch)\s+(?:le\s+|la\s+|the\s+)?"
    r"(?:code|script|commande|command|shell|requ[êe]te)",
    r"affiche\s+les\s+\d+\s+commandements",
    r"<<<\s*(?:ignore|system|instruction)",
]
RE_INSTRUCTION = re.compile("|".join(MOTIFS_INSTRUCTION), re.IGNORECASE)

# Préfixes de cellule « injection de formule » (Excel/CSV) : conservés tels quels.
RE_FORMULE = re.compile(r"^[=+\-@\t\r]")


def avertir(meta: dict, message: str) -> None:
    """Ajoute un avertissement au dictionnaire de métadonnées (sans doublon)."""
    liste = meta.setdefault("avertissements", [])
    if message not in liste:
        liste.append(message)


def normaliser(texte: str) -> str:
    """Normalise un texte extrait : Unicode NFC, fins de ligne LF, espaces finaux.

    Aucun caractère significatif n'est retiré ni remplacé (contenu intégral).
    """
    if not texte:
        return ""
    texte = unicodedata.normalize("NFC", str(texte))
    texte = texte.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    lignes = [ligne.rstrip() for ligne in texte.split("\n")]
    # Compacte les lignes vides consécutives (lisibilité, aucun contenu perdu).
    compacte: list[str] = []
    precedente_vide = False
    for ligne in lignes:
        vide = not ligne.strip()
        if vide and precedente_vide:
            continue
        compacte.append(ligne)
        precedente_vide = vide
    return "\n".join(compacte).strip("\n")


def detecter_instructions(texte: str) -> list[int]:
    """Renvoie les numéros de ligne (1-indexés) ressemblant à une consigne.

    Purement informatif : sert à journaliser un document piégé sans jamais
    modifier, filtrer ni exécuter son contenu.
    """
    if not texte:
        return []
    trouvees = []
    for index, ligne in enumerate(texte.split("\n"), 1):
        if RE_INSTRUCTION.search(ligne):
            trouvees.append(index)
    return trouvees


def cellules_formule(texte: str) -> bool:
    """Vrai si une cellule ressemble à une formule (=, +, -, @) : donnée, pas code."""
    return bool(RE_FORMULE.match(texte.strip())) if texte else False


def echapper_cellule(valeur) -> str:
    """Échappe une valeur pour un tableau markdown (| et retours à la ligne)."""
    if valeur is None:
        return ""
    texte = unicodedata.normalize("NFC", str(valeur))
    texte = texte.replace("\r\n", "\n").replace("\r", "\n").replace("|", "\\|")
    return "\n".join(ligne.strip() for ligne in texte.split("\n")).strip()


def est_entete_plausible(lignes: list[list[str]]) -> bool:
    """Heuristique : la 1re ligne sert d'en-tête si elle est textuelle et remplie."""
    if len(lignes) < 2:
        return False
    premiere = [c for c in lignes[0] if c.strip()]
    if not premiere:
        return False
    if any(cellules_formule(c) for c in premiere):
        return False
    # Une ligne d'en-tête ne contient pas de nombre là où les lignes de données en ont.
    numeriques_donnees = sum(
        1 for l in lignes[1:] for c in l if c.strip() and _est_nombre(c)
    )
    numeriques_entete = sum(1 for c in premiere if _est_nombre(c))
    return numeriques_donnees == 0 or numeriques_entete == 0


def _est_nombre(texte: str) -> bool:
    try:
        float(texte.strip().replace(",", "."))
        return True
    except ValueError:
        return False


def tableau_markdown(lignes: list[list]) -> str:
    """Convertit des lignes de cellules en tableau markdown (largeur harmonisée)."""
    nettoyees = [[echapper_cellule(c) for c in ligne] for ligne in lignes if ligne is not None]
    nettoyees = [l for l in nettoyees if any(c.strip() for c in l)]
    if not nettoyees:
        return ""
    largeur = max(len(l) for l in nettoyees)
    if not est_entete_plausible(nettoyees):
        nettoyees.insert(0, [f"Colonne {i + 1}" for i in range(largeur)])
    lignes_md = []
    for position, ligne in enumerate(nettoyees):
        cellules = ligne + [""] * (largeur - len(ligne))
        lignes_md.append("| " + " | ".join(cellules) + " |")
        if position == 0:
            lignes_md.append("| " + " | ".join(["---"] * largeur) + " |")
    return "\n".join(lignes_md)


def bloc_tableau(titre: str, lignes: list[list], meta: dict) -> str:
    """Génère la section markdown d'un tableau et le compte dans `meta`."""
    tableau = tableau_markdown(lignes)
    if not tableau:
        return ""
    meta["tableaux"] = int(meta.get("tableaux", 0)) + 1
    return f"{titre}\n\n{tableau}" if titre else tableau


def charger_parseur(type_doc: str):
    """Charge le module parseur correspondant à un type de document."""
    if type_doc not in MODULE_PAR_TYPE:
        raise ValueError(f"Type de document non pris en charge : {type_doc!r}")
    return importlib.import_module(
        f".{MODULE_PAR_TYPE[type_doc]}", package="tools.ingest.parsers"
    )


def detecter_type(nom: str, entete: bytes = b"") -> str | None:
    """Déduit le type d'un document : extension d'abord, puis signature binaire."""
    type_doc = TYPE_PAR_EXT.get(nom[nom.rfind("."):].lower()) if "." in nom else None
    if type_doc:
        return type_doc
    # Repli sur la signature : un fichier renommé (.bin) reste lisible.
    if entete.startswith(b"%PDF"):
        return "pdf"
    if entete.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image"
    if entete.startswith(b"\xff\xd8\xff"):
        return "image"
    if entete[:4] == b"RIFF" and entete[8:12] == b"WEBP":
        return "image"
    if entete.startswith(b"GIF8"):
        return "image"
    if entete.startswith(b"PK\x03\x04"):
        # Conteneur OOXML ou ZIP : le nom interne tranche (voir archive.detecter_type_interne).
        return "zip"
    return None


def lire_entete(chemin, taille: int = 4096) -> bytes:
    """Lit les premiers octets d'un fichier (détection de type)."""
    with open(chemin, "rb") as fichier:
        return fichier.read(taille)