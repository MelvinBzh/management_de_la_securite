"""Fusion des alias : « K. Benali », « Karim Benali » et « Benali » désignent la même personne.

Deux entités sont fusionnées si leurs types sont compatibles ET (leurs noms sont compatibles OU leurs
vecteurs sont très proches). On ne fusionne jamais deux types différents (hors « autre ») : « Sage »
l'éditeur et « Sage X3 » le logiciel restent distincts tant que leurs noms ne l'imposent pas.
Le résultat est auditable : `fusionner` renvoie aussi les groupes, à relire par un humain.
"""
from __future__ import annotations

from collections import Counter

from . import ollama, texte

SEUIL_VECTEUR = 0.90


def nom_compatible(a: str, b: str) -> bool:
    """Noms qui désignent vraisemblablement la même chose (sans modèle).

    Règles : mêmes mots ; ou les mots du plus court sont tous dans le plus long (≥ 1 mot de 4 lettres) ;
    ou même dernier mot et initiale du prénom compatible (« k benali » ~ « karim benali »).

    >>> nom_compatible("K. Benali", "Karim Benali")
    True
    >>> nom_compatible("Saint-Priest (STP)", "Saint-Priest")
    True
    >>> nom_compatible("Julien Roussel", "Karim Benali")
    False
    """
    ta, tb = texte.normaliser(a).split(), texte.normaliser(b).split()
    if not ta or not tb:
        return False
    if set(ta) == set(tb):
        return True
    court, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if set(court) <= set(long_) and any(len(m) >= 4 for m in court):
        return True
    if len(ta) >= 2 and len(tb) >= 2 and ta[-1] == tb[-1] and len(ta[-1]) >= 4:
        return ta[0][0] == tb[0][0] and (len(ta[0]) == 1 or len(tb[0]) == 1)
    return False


def _types_compatibles(a: str, b: str) -> bool:
    return a == b or "autre" in (a, b)


def fusionner(entites: list[tuple[str, str]], vecteurs_noms: list[list[float]] | None = None,
              seuil: float = SEUIL_VECTEUR) -> tuple[dict[str, str], list[list[str]]]:
    """Regroupe des entités `(nom, type)` en entités canoniques.

    Renvoie `(canonique, groupes)` : `canonique` associe le NOM NORMALISÉ de chaque variante à son nom
    canonique (le plus fréquent, à égalité le plus long) ; `groupes` liste les groupes de plus d'un nom.
    """
    uniques = sorted({(texte.normaliser(n), n, t) for n, t in entites if texte.normaliser(n)})
    parent = list(range(len(uniques)))

    def racine(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(uniques)):
        for j in range(i + 1, len(uniques)):
            if not _types_compatibles(uniques[i][2], uniques[j][2]):
                continue
            proches = bool(vecteurs_noms) and ollama.cosinus(vecteurs_noms[i], vecteurs_noms[j]) >= seuil
            if proches or nom_compatible(uniques[i][1], uniques[j][1]):
                parent[racine(i)] = racine(j)
    frequences = Counter(texte.normaliser(n) for n, _ in entites)
    groupes: dict[int, list[int]] = {}
    for i in range(len(uniques)):
        groupes.setdefault(racine(i), []).append(i)
    canonique: dict[str, str] = {}
    listes: list[list[str]] = []
    for membres in groupes.values():
        meilleur = max(membres, key=lambda k: (frequences[uniques[k][0]], len(uniques[k][1])))
        for k in membres:
            canonique[uniques[k][0]] = uniques[meilleur][1]
        if len(membres) > 1:
            listes.append(sorted(uniques[k][1] for k in membres))
    return canonique, listes
