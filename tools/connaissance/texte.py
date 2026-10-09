"""Normalisation de texte et vérification d'extrait exact — la pierre angulaire anti-hallucination.

Un extrait « existe » dans un document si, une fois les deux textes normalisés (casse, accents conservés,
ponctuation et tableaux Markdown ignorés), l'extrait est une sous-chaîne du document. Cette vérification
est déterministe : aucun modèle n'intervient, donc aucun modèle ne peut la tromper.
"""
from __future__ import annotations

import re

_NON_MOT = re.compile(r"[^0-9a-zàâäçéèêëîïôöùûüÿœ]+")


def normaliser(texte: str) -> str:
    """Minuscules, tout ce qui n'est pas lettre/chiffre devient un espace, espaces réduits.

    >>> normaliser("| Karim  Benali | DSI/RSSI |")
    'karim benali dsi rssi'
    """
    return " ".join(_NON_MOT.sub(" ", texte.lower()).split())


def contient(extrait: str, texte_normalise: str) -> bool:
    """Vrai si `extrait` figure dans le document (déjà normalisé par `normaliser`). Un extrait vide est faux.

    >>> contient("Le DSI cumule", normaliser("Le DSI cumule les fonctions de DSI et de RSSI."))
    True
    >>> contient("le DSI ne cumule pas", normaliser("Le DSI cumule les fonctions."))
    False
    """
    cible = normaliser(extrait)
    return bool(cible) and cible in texte_normalise


def jetons(texte: str, minimum: int = 3) -> set[str]:
    """Mots normalisés d'au moins `minimum` caractères."""
    return {m for m in normaliser(texte).split() if len(m) >= minimum}


def nom_present(nom: str, texte_normalise: str, part: float = 0.7) -> bool:
    """Un nom (entité) figure-t-il dans le document ? Entier, ou au moins `part` de ses mots.

    Tolère les libellés composites (« Hugo Petit - Alternant ») sans accepter un nom étranger au document.
    """
    entier = normaliser(nom)
    if entier and entier in texte_normalise:
        return True
    mots = jetons(nom)
    if not mots:
        return False
    presents = set(texte_normalise.split())
    return sum(1 for m in mots if m in presents) / len(mots) >= part
