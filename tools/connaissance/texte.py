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


DEBUT_DONNEES = "<<<DONNÉES>>>"
FIN_DONNEES = "<<<FIN DONNÉES>>>"


def corps(contenu: str) -> str:
    r"""Partie utile d'un document ingéré : ce qui est entre `<<<DONNÉES>>>` et `<<<FIN DONNÉES>>>`.

    L'ingestion ajoute un en-tête technique (nom du fichier, type, taille, avertissement). Ce n'est pas de
    l'information : mesuré, il produisait de faux signalements de contradiction (« # Extrait — A » contre
    « # Extrait — B »). Le résultat est une TRANCHE CONTIGUË du texte d'origine — rien n'est reformulé.
    Un texte sans marqueurs est rendu tel quel.

    >>> corps("# Extrait — x\n\n<<<DONNÉES>>>\n\nContenu utile\n\n<<<FIN DONNÉES>>>")
    'Contenu utile'
    >>> corps("Texte brut")
    'Texte brut'
    """
    debut = contenu.find(DEBUT_DONNEES)
    if debut < 0:
        return contenu
    debut += len(DEBUT_DONNEES)
    fin = contenu.find(FIN_DONNEES, debut)
    return contenu[debut:fin if fin >= 0 else len(contenu)].strip()


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
