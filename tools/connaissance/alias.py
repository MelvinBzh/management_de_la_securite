"""Fusion des alias : « K. Benali », « Karim Benali » et « Benali » désignent la même personne.

Principe de prudence : **une fusion manquée coûte un doublon, une fusion abusive corrompt les relations**
(deux entités différentes deviennent « la même »). On fusionne donc peu, avec des règles étroites, et le
résultat reste auditable (`fusionner` renvoie aussi les groupes).

Ce qui a été mesuré sur Nordval (304 entités) et corrigé par rapport à la première version :
- l'ancienne règle « les mots du plus court sont dans le plus long » reliait des noms composites à toutes
  les entités qu'ils citent (« Départ du responsable infrastructure (M. Dubreuil) » → LogiSoft, M365…) ;
- la fusion était TRANSITIVE (A~B et B~C ⇒ A~C), d'où des chaînes de dizaines de noms ;
- le type « autre » servait de pont entre n'importe quels types.
Désormais : comparaison à un REPRÉSENTANT de groupe (jamais de chaîne), préfixe de mots seulement, motif
« initiale + nom de famille » pour les personnes, types identiques, et vecteurs en dernier recours.
"""
from __future__ import annotations

import re
from collections import Counter

from . import ollama, texte

# Mesuré (nomic-embed-text, noms courts) : vraies variantes ≥ 0,84 ; noms distincts ≤ 0,73.
SEUIL_VECTEUR = 0.86


# Mots trop généraux pour désigner à eux seuls une entité précise : ils ne servent jamais de préfixe d'alias.
GENERIQUES = frozenset({
    "direction", "service", "services", "equipe", "equipes", "site", "sites", "compte", "comptes", "serveur", "serveurs",
    "systeme", "systemes", "donnees", "donnee", "responsable", "support", "reseau", "outil", "outils", "client", "clients",
    "prestataire", "prestataires", "fournisseur", "contrat", "contrats", "processus", "procedure", "poste", "postes",
    "materiel", "application", "applications", "document", "documents", "politique", "audit", "incident", "incidents",
})


def _mots(nom: str) -> list[str]:
    return texte.normaliser(nom).split()


def _chiffres(nom: str) -> set[str]:
    """Nombres du nom : « NAS 12 baies » et « NAS 4 baies » (ou « 10 ans » et « 5 ans ») ne sont pas la même chose."""
    return set(re.findall(r"\d+", nom))


def nom_compatible(a: str, b: str) -> bool:
    """Noms qui désignent vraisemblablement la même chose, sans modèle. Règles étroites, volontairement.

    1. mêmes mots (à l'ordre et à la casse près) ;
    2. PRÉFIXE : les mots du plus court sont exactement le début du plus long, le plus court contient un
       mot d'au moins 4 lettres, le plus long n'ajoute pas plus de 3 mots et n'est pas une combinaison
       « A / B » (« OPSITEL » ~ « OPSITEL Infogérance Réseau », mais pas « FleetTrack » ~ « FleetTrack/WMS ») ;
    3. PERSONNE : même dernier mot (≥ 4 lettres) et prénoms identiques ou l'un réduit à son initiale.

    >>> nom_compatible("K. Benali", "Karim Benali")
    True
    >>> nom_compatible("Saint-Priest (STP)", "Saint-Priest")
    True
    >>> nom_compatible("Julien Roussel", "Karim Benali")
    False
    >>> nom_compatible("LogiSoft", "Départ du responsable infrastructure (M. Dubreuil)")
    False
    """
    ta, tb = _mots(a), _mots(b)
    if not ta or not tb:
        return False
    ca, cb = _chiffres(a), _chiffres(b)
    if ca and cb and ca != cb:
        return False  # « NAS 12 baies » ≠ « NAS 4 baies », « 10 ans » ≠ « 5 ans »
    if set(ta) == set(tb):
        return True
    court, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    brut_long = a if long_ is ta else b
    brut_court = b if long_ is ta else a
    if (long_[:len(court)] == court and any(len(m) >= 4 for m in court)
            and not (len(court) == 1 and court[0] in GENERIQUES)   # « Direction » seule n'est pas un alias

            and len(long_) - len(court) <= 3                      # un alias, pas une phrase descriptive
            and not any(c in brut_long and c not in brut_court for c in "/,;")):  # ni une combinaison « A / B »
        return True
    if len(ta) >= 2 and len(tb) >= 2 and ta[-1] == tb[-1] and len(ta[-1]) >= 4:
        p, q = ta[0], tb[0]
        return p == q or (len(p) == 1 and q.startswith(p)) or (len(q) == 1 and p.startswith(q))
    return False


def _vecteur_autorise(a: str, b: str) -> bool:
    """Les vecteurs ne servent qu'aux noms assez longs et qui ne sont pas des listes (« STP / LSQ »)."""
    return min(len(texte.normaliser(a)), len(texte.normaliser(b))) >= 7 and "/" not in a and "/" not in b


def _compatibles(a: tuple[str, str, int], b: tuple[str, str, int], vecteurs: list[list[float]] | None,
                 seuil: float, par_vecteur: bool) -> bool:
    """`a`, `b` = (nom normalisé, nom d'origine, indice du vecteur). `par_vecteur` : types identiques."""
    ca, cb = _chiffres(a[1]), _chiffres(b[1])
    if ca and cb and ca != cb:
        return False
    if nom_compatible(a[1], b[1]):
        return True
    return (par_vecteur and bool(vecteurs) and _vecteur_autorise(a[1], b[1])
            and ollama.cosinus(vecteurs[a[2]], vecteurs[b[2]]) >= seuil)


def fusionner(entites: list[tuple[str, str]], vecteurs_noms: list[list[float]] | None = None,
              seuil: float = SEUIL_VECTEUR) -> tuple[dict[str, str], list[list[str]]]:
    """Regroupe des entités `(nom, type)` en entités canoniques.

    `vecteurs_noms[i]` est le vecteur du i-ème nom de `sorted({(normalisé, nom, type)})`, c'est-à-dire de
    `noms_distincts(entites)` (le même ordre). Renvoie `(canonique, groupes)` : `canonique` associe le NOM
    NORMALISÉ de chaque variante à son nom canonique (le plus fréquent, à égalité le plus long) ; `groupes` liste
    les groupes de plus d'un nom, à relire par un humain.
    """
    uniques = noms_distincts(entites)
    frequences = Counter(texte.normaliser(n) for n, _ in entites)
    ordre = sorted(range(len(uniques)), key=lambda k: (-frequences[uniques[k][0]], -len(uniques[k][1])))
    groupes: list[list[int]] = []  # le premier membre est le représentant
    for k in ordre:
        placé = False
        for groupe in groupes:
            rep = groupe[0]
            type_rep, type_k = uniques[rep][2], uniques[k][2]
            if type_rep != type_k and "autre" not in (type_rep, type_k):
                continue  # deux types précis différents : jamais fusionnés
            # le type « autre » ne fusionne qu'au vu du NOM (règles étroites), jamais sur la seule proximité vectorielle
            if _compatibles((uniques[rep][0], uniques[rep][1], rep), (uniques[k][0], uniques[k][1], k), vecteurs_noms, seuil,
                            par_vecteur=type_rep == type_k):
                groupe.append(k)
                placé = True
                break
        if not placé:
            groupes.append([k])
    canonique: dict[str, str] = {}
    listes: list[list[str]] = []
    for groupe in groupes:
        for k in groupe:
            canonique[uniques[k][0]] = uniques[groupe[0]][1]
        if len(groupe) > 1:
            listes.append(sorted(uniques[k][1] for k in groupe))
    return canonique, listes


def noms_distincts(entites: list[tuple[str, str]]) -> list[tuple[str, str, str]]:
    """Variantes distinctes `(normalisé, nom, type)`, triées : l'ordre attendu par `vecteurs_noms`."""
    return sorted({(texte.normaliser(n), n, t) for n, t in entites if texte.normaliser(n)})
