"""Rapports de contrôle numérotés, et points à faire valider par un humain.

Le pilote (`web/chaine.py`) enregistre ici chaque contrôle d'étape. Pour chaque contrôle :

- un **numéro** (Contrôle n°1, n°2…), une **version** de l'étape (la 1re écriture, puis chaque reprise) ;
- **ce qui n'allait pas** (les corrections demandées) ;
- **ce qui a changé** depuis la version précédente (lignes ajoutées / retirées) ;
- un verdict : `conforme`, `non_conforme` (l'agent reprend) ou, en dernier recours,
  **« nécessite une validation humaine »** avec le POURQUOI et QUOI vérifier.

Jamais de verdict muet : si le contrôle n'a rien rendu de lisible, ou s'il reste non conforme après
les reprises, la décision revient à l'analyste, qui sait pourquoi et ce qu'il doit relire.

Source de vérité : `controles.json` ; `RAPPORT-CONTROLE.md` en est la version lisible (réécrite à chaque fois).
"""
from __future__ import annotations

import difflib
import json
import time
from pathlib import Path

NOM_JSON = "controles.json"
NOM_RAPPORT = "RAPPORT-CONTROLE.md"
VERDICTS = {"conforme": "CONFORME", "non_conforme": "NON CONFORME", "humaine": "NÉCESSITE UNE VALIDATION HUMAINE"}
LIMITE_EXTRAITS = 5
LARGEUR_EXTRAIT = 160


def lire(dossier: Path) -> list[dict]:
    """Contrôles déjà enregistrés (liste vide si aucun ou fichier illisible)."""
    try:
        donnees = json.loads((Path(dossier) / NOM_JSON).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [d for d in donnees if isinstance(d, dict)] if isinstance(donnees, list) else []


def texte_des_livrables(dossier: Path, fichiers: list[str]) -> str:
    """Texte concaténé des livrables d'une étape (vide s'ils n'existent pas encore)."""
    morceaux = []
    for nom in fichiers:
        try:
            morceaux.append((Path(dossier) / nom).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(morceaux)


def resume_changements(avant: str | None, apres: str) -> str:
    """« Ce qui a changé » entre deux versions : comptes + quelques lignes concernées."""
    if not avant or not avant.strip():
        return "Première version de l'étape."
    ancien = [l.strip() for l in avant.splitlines() if l.strip()]
    nouveau = [l.strip() for l in apres.splitlines() if l.strip()]
    ajoutees, retirees = [], []
    for ligne in difflib.unified_diff(ancien, nouveau, lineterm="", n=0):
        if ligne.startswith("+") and not ligne.startswith("+++"):
            ajoutees.append(ligne[1:])
        elif ligne.startswith("-") and not ligne.startswith("---"):
            retirees.append(ligne[1:])
    if not ajoutees and not retirees:
        return "Aucun changement : l'agent a rendu le même texte."
    morceaux = [f"{len(ajoutees)} ligne(s) ajoutée(s), {len(retirees)} retirée(s)."]
    for titre, lignes in (("Retiré", retirees), ("Ajouté", ajoutees)):
        for ligne in lignes[:LIMITE_EXTRAITS]:
            court = ligne if len(ligne) <= LARGEUR_EXTRAIT else ligne[: LARGEUR_EXTRAIT - 1] + "…"
            morceaux.append(f"{titre} : {court}")
    return "\n".join(morceaux)


def pourquoi_et_quoi(cause: str, corrections: str, fichiers: list[str]) -> tuple[str, str]:
    """Texte « pourquoi » et « quoi vérifier » d'une validation humaine.

    `cause` : « illisible » (le contrôle n'a pas rendu de verdict exploitable) ou « reste_non_conforme ».
    """
    liste = ", ".join(f"`{n}`" for n in fichiers)
    if cause == "illisible":
        pourquoi = ("Le contrôle automatique n'a pas rendu de verdict exploitable après plusieurs tentatives "
                    "(deux modèles de familles différentes). L'étape n'a donc pas pu être vérifiée par la machine.")
        quoi = (f"Relire {liste} face aux documents d'origine : repérer tout composant, logiciel, rôle, chiffre "
                "ou source qui ne figure dans aucun document fourni, et le retirer ou le marquer « à confirmer ».")
    else:
        pourquoi = ("Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : "
                    f"{corrections or 'détail dans le rapport de contrôle'}")
        quoi = (f"Pour chaque point signalé, chercher l'affirmation dans {liste} puis dans les documents d'origine ; "
                "si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.")
    return pourquoi, quoi


def enregistrer(dossier: Path, etape: int | str, libelle: str, controleur: str, verdict: str,
                corrections: str = "", avant: str | None = None, apres: str = "",
                humaine: tuple[str, str] | None = None) -> dict:
    """Ajoute un contrôle (numéroté, versionné) et réécrit le rapport lisible. Renvoie l'entrée."""
    if verdict not in ("conforme", "non_conforme"):
        raise ValueError(f"verdict inconnu : {verdict}")
    dossier = Path(dossier)
    entrees = lire(dossier)
    version = 1 + sum(1 for e in entrees if str(e.get("etape")) == str(etape))
    entree = {
        "numero": len(entrees) + 1, "etape": etape, "libelle": libelle, "version": version,
        "controleur": controleur, "verdict": verdict, "corrections": corrections,
        "changements": resume_changements(avant, apres), "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "humaine": None,
    }
    if humaine:
        entree["humaine"] = {"pourquoi": humaine[0], "quoi": humaine[1]}
    entrees.append(entree)
    _ecrire(dossier, entrees)
    return entree


def marquer_humaine(dossier: Path, etape: int | str, pourquoi: str, quoi: str) -> None:
    """Le dernier contrôle de l'étape nécessite une validation humaine."""
    dossier = Path(dossier)
    entrees = lire(dossier)
    for entree in reversed(entrees):
        if str(entree.get("etape")) == str(etape):
            entree["humaine"] = {"pourquoi": pourquoi, "quoi": quoi}
            break
    else:
        return
    _ecrire(dossier, entrees)


def _ecrire(dossier: Path, entrees: list[dict]) -> None:
    (dossier / NOM_JSON).write_text(json.dumps(entrees, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dossier / NOM_RAPPORT).write_text(rapport_markdown(entrees), encoding="utf-8")


def a_valider(dossier: Path) -> list[dict]:
    """Étapes dont le DERNIER contrôle nécessite une validation humaine (une reprise conforme l'efface)."""
    derniers: dict[str, dict] = {}
    for entree in lire(dossier):
        derniers[str(entree.get("etape"))] = entree
    return [e for e in derniers.values() if e.get("humaine")]


def rapport_markdown(entrees: list[dict]) -> str:
    """Rapport lisible : une section par contrôle, dans l'ordre, avec un sommaire d'abord."""
    lignes = ["# Rapport de contrôle", "",
              "Un contrôle indépendant relit chaque étape avant la suivante. Pour chacun : ce qui n'allait pas, "
              "ce qui a changé depuis la version précédente, et le verdict.", ""]
    humaines = {}
    for e in entrees:
        humaines[str(e.get("etape"))] = e if e.get("humaine") else None
    attente = [e for e in humaines.values() if e]
    if attente:
        lignes += ["## À faire valider par un humain", ""]
        for e in attente:
            lignes += [f"- **{e['libelle']}** — {e['humaine']['pourquoi']}", f"  - À vérifier : {e['humaine']['quoi']}"]
        lignes.append("")
    if not entrees:
        lignes.append("_Aucun contrôle enregistré._")
    for e in entrees:
        etat = VERDICTS["humaine"] if e.get("humaine") else VERDICTS.get(e["verdict"], e["verdict"])
        lignes += [f"## Contrôle n°{e['numero']} — {e['libelle']}, version {e['version']} : {etat}", "",
                   f"- Contrôleur : {e['controleur']}  ·  {e.get('date', '')}",
                   "- Ce qui n'allait pas : " + (e.get("corrections") or "rien à signaler"),
                   "- Ce qui a changé depuis la version précédente :"]
        lignes += ["  " + l for l in str(e.get("changements", "")).splitlines()]
        if e.get("humaine"):
            lignes += ["- Pourquoi une validation humaine : " + e["humaine"]["pourquoi"],
                       "- Quoi vérifier : " + e["humaine"]["quoi"]]
        lignes.append("")
    return "\n".join(lignes)
