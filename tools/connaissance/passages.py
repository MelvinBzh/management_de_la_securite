"""Passages : le texte d'origine des documents, découpé, comme FILET DE SÉCURITÉ de l'index.

Pourquoi : l'extraction de faits par un modèle peut RATER une information (mesuré : aucun fait ne mentionnait
« hors support constructeur » alors que le document le dit) ou la réduire à un fragment inutilisable (« S. Morel »).
Les passages sont le texte du document lui-même : rien n'est perdu, rien n'est reformulé, donc rien n'est à
vérifier — ils sont « vérifiés par construction ». La recherche les trouve même quand l'extraction a échoué.

Chaque passage est un bloc CONTIGU du document (donc une sous-chaîne exacte). Le contexte utile à la lecture (titre
de section, en-tête de tableau) est conservé À PART, dans `Passage.contexte`, pour ne jamais altérer le texte.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import texte

TAILLE_PASSAGE = 1200
MIN_UTILE = 40  # caractères normalisés : en dessous, un bloc n'est que du bruit (titre isolé, séparateur)

_SEPARATEUR_TABLEAU = re.compile(r"^\s*\|[\s:|\-]+\|\s*$")


@dataclass(frozen=True)
class Passage:
    doc: str
    contexte: str  # titre de section et en-tête de tableau les plus proches (aide à la lecture, hors texte)
    texte: str     # bloc contigu du document, tel quel


def decouper(doc: str, contenu: str, taille: int = TAILLE_PASSAGE, minimum: int = MIN_UTILE) -> list[Passage]:
    """Découpe un document en passages d'au plus `taille` caractères, aux limites de lignes.

    Une ligne n'est jamais coupée (une ligne de tableau reste entière). Le dernier titre `#` et l'en-tête du
    tableau en cours sont mémorisés comme contexte de chaque passage.

    >>> p = decouper("d.md", "# Contrats\\n| Prestataire | Fin |\\n|---|---|\\n| OPSITEL | 2026 |\\n| Sage | 2027 |", taille=60, minimum=0)
    >>> p[-1].contexte
    'Contrats · | Prestataire | Fin |'
    >>> all(texte_.texte in "# Contrats\\n| Prestataire | Fin |\\n|---|---|\\n| OPSITEL | 2026 |\\n| Sage | 2027 |" for texte_ in p)
    True
    """
    passages: list[Passage] = []
    courant: list[str] = []
    longueur = 0
    titre = entete = ""
    contexte_debut = ""

    def clore() -> None:
        nonlocal courant, longueur
        bloc = "\n".join(courant).strip("\n")
        if len(texte.normaliser(bloc)) >= minimum:
            passages.append(Passage(doc, contexte_debut, bloc))
        courant, longueur = [], 0

    lignes = texte.corps(contenu).splitlines()  # sans l'en-tête technique de l'ingestion
    for position, ligne in enumerate(lignes):
        if ligne.startswith("#"):
            titre = ligne.lstrip("# ").strip()
            entete = ""
        elif _SEPARATEUR_TABLEAU.match(ligne) and position > 0 and lignes[position - 1].lstrip().startswith("|"):
            entete = lignes[position - 1].strip()
        elif not ligne.lstrip().startswith("|"):
            entete = ""
        if longueur + len(ligne) + 1 > taille and courant:
            clore()
        if not courant:
            contexte_debut = " · ".join(x for x in (titre, entete) if x)
        courant.append(ligne)
        longueur += len(ligne) + 1
    if courant:
        clore()
    return passages
