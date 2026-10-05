# -*- coding: utf-8 -*-
r"""Lecture et validation des en-têtes YAML des fichiers opencode (agents, skills).

Ces en-têtes sont la **frontière la plus silencieuse du projet** : opencode n'affiche
aucune erreur applicative quand un agent est refusé. Il écrit simplement

    ! agent "orchestrator" not found. Falling back to default agent

puis démarre la chaîne **sans les consignes de cet agent**. Le modèle, privé de son
brief, reformule la demande et propose un plan ; le processus sort en code 0 et aucun
livrable n'apparaît. Un `mode: agent` écrit à la place de `mode: primary` suffit à
éteindre toute la chaîne sans laisser de trace.

Ce module donne donc un seul endroit pour dire ce qu'opencode accepte, utilisé par
le déploiement du Studio (qui refuse d'écrire un en-tête invalide plutôt que de
casser la chaîne) et par les tests (WEB-26).

Valeurs et clés documentées par l'usage réel de opencode 1.18.x, vérifié en
exécutant l'agent : `mode` n'accepte que `primary`, `subagent`, `all` ou rien.
"""
from __future__ import annotations

import re

# Valeurs acceptées par la clé `mode` d'un agent. `primary` = l'agent avec lequel
# l'utilisateur dialogue (donc lançable par `opencode run --agent`) ; `subagent` =
# reservé aux agents specialized appelés par la chaîne ; `all` = les deux.
MODES_AGENT = ("primary", "subagent", "all")

# Clés d'en-tête reconnues. Une clé hors de cette liste n'est pas forcément rejetée
# par opencode, mais elle ne veut rien dire pour nous : la signaler évite qu'une
# faute de frappe passe inaperçue.
CLES_AGENT = frozenset({
    "description", "mode", "model", "small_model", "variant", "temperature",
    "top_p", "prompt", "tools", "permission", "disable", "color",
})
CLES_SKILL = frozenset({"name", "description", "agent", "model"})

# `opencode.jsonc` et les en-têtes partagent la même écriture d'identifiant :
# `nom:tag` (Ollama), éventuellement préfixé par un fournisseur.
RE_MODELE = re.compile(r"^[a-zA-Z0-9._:-]{1,64}(/[a-zA-Z0-9._:-]{1,96})?$")


class EnteteInvalide(ValueError):
    """En-tête qu'opencode refuserait — donc chaîne cassée (fail closed)."""


def lire(contenu: str) -> dict[str, str]:
    """Renvoie les clés de premier niveau de l'en-tête, à plat.

    Les sous-clés (`permission:`, `tools:`…) sont ignorées : elles appartiennent à
    opencode, pas à cette vérification. Renvoie un dictionnaire vide si le fichier
    n'a pas d'en-tête — un agent sans en-tête reste utilisable, il n'est simplement
    pas personnalisable.
    """
    if not isinstance(contenu, str) or not contenu.startswith("---\n"):
        return {}
    fin = contenu.find("\n---", 3)
    if fin == -1:
        return {}
    tete: dict[str, str] = {}
    for ligne in contenu[4:fin].splitlines():
        if not ligne.strip() or ligne[:1] in (" ", "\t") or ligne.lstrip().startswith("#"):
            continue
        cle, separateur, valeur = ligne.partition(":")
        if not separateur:
            continue
        tete[cle.strip()] = valeur.strip()
    return tete


def verifier_mode(contenu: str) -> str:
    """Renvoie le `mode` d'un agent, ou `""` s'il est absent.

    Lève `EnteteInvalide` si la valeur n'est pas acceptée par opencode : c'est le
    seul contrôle rendu obligatoire au déploiement, parce que c'est le seul qui
    désactive silencieusement un agent.
    """
    mode = lire(contenu).get("mode", "")
    if mode and mode not in MODES_AGENT:
        raise EnteteInvalide(
            f"mode « {mode} » : opencode n'accepte que "
            f"{', '.join(MODES_AGENT)} (ou pas de mode du tout). "
            "Un agent refusé n'est pas enregistré : opencode bascule alors sur "
            "l'agent par défaut et la chaîne démarre sans ses consignes."
        )
    return mode


# En YAML, une clé qui commence par `*` est un **alias**. Écrit tel quel,
#     permission:
#       bash:
#         *: deny
# opencode 1.18.34 n'enregistre pas l'agent — sans message, sans code d'erreur :
# `opencode run --agent orchestrator` bascule sur l'agent par défaut et la chaîne
# démarre sans ses consignes. Constaté puis reproduit en isolement (dossier neuf,
# agent de contrôle) : la même permission écrite `'*': deny` est acceptée, et
# l'agent répond. D'où la règle : toute clé de permission contient son `*` entre
# guillemets.
RE_CLE_YAML_ETOILE = re.compile(r"^(\s+)\*:(?:\s|$)", re.M)


def verifier_permission(contenu: str) -> list[str]:
    """Renvoie la liste des clés de permission que opencode refuserait.

    todayne **tout** l'agent parce qu'une seule clé est mal écrite — le pire des
    modes de panne, puisque rien ne signale que le fichier a été écarté.
    """
    problemes = []
    for numero, ligne in enumerate(contenu.splitlines(), 1):
        if RE_CLE_YAML_ETOILE.match(ligne):
            problemes.append(
                f"ligne {numero} : clé « * » nue — écrivez-la entre guillemets ('*')"
            )
    return problemes


def modele(contenu: str) -> str:
    """Renvoie le modèle déclaré par l'en-tête, ou `""`."""
    return lire(contenu).get("model", "")


def controles(contenu: str, type_: str = "agent") -> list[str]:
    """Liste des anomalies d'un fichier, sans rien jeter (pour un rapport lisible).

    `type_` vaut `agent` ou `skill`. N'élève jamais : c'est un diagnostic, alors que
    `verifier_mode` est le garde-fou bloquant du déploiement.
    """
    tete = lire(contenu)
    if not tete:
        return [] if type_ == "skill" else ["en-tête absent ou illisible"]
    connus = CLES_AGENT if type_ == "agent" else CLES_SKILL
    problemes = [f"clé inconnue : {cle}" for cle in sorted(set(tete) - connus)]
    if not tete.get("description"):
        problemes.append("description absente ou vide")
    if type_ == "agent":
        mode = tete.get("mode", "")
        if mode and mode not in MODES_AGENT:
            problemes.append(
                f"mode « {mode} » refusé (valeurs acceptées : "
                f"{', '.join(MODES_AGENT)})"
            )
    valeur = tete.get("model", "")
    if valeur and not RE_MODELE.match(valeur):
        problemes.append(f"model « {valeur} » illisible")
    problemes.extend(verifier_permission(contenu))
    if type_ == "skill" and not tete.get("name"):
        problemes.append("name absent ou vide")
    return problemes


__all__ = [
    "CLES_AGENT",
    "CLES_SKILL",
    "EnteteInvalide",
    "MODES_AGENT",
    "controles",
    "lire",
    "modele",
    "verifier_mode",
    "verifier_permission",
]
