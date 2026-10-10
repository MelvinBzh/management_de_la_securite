"""Le dossier de connaissance vu depuis le site : état, lancement en arrière-plan, lecture seule.

Le travail lui-même est dans `tools/connaissance/` (voir son README) ; ce module ne fait que :
- dire si la connaissance PEUT être construite (profil Ollama actif, serveur renseigné) ;
- lancer la mise à jour en arrière-plan quand des documents sont déposés ;
- lire l'index (sans jamais le modifier) pour la page « Connaissances ».
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.connaissance import citations, externe, travail
from tools.connaissance.index import Index
from web import lib, reglages


def endpoint_ollama() -> str:
    """Adresse du serveur Ollama du profil actif, ou « » si le profil actif n'est pas Ollama."""
    try:
        etat = reglages.appliquer_profil(dict(reglages.charger() or {}))
    except Exception:  # noqa: BLE001 — des réglages illisibles ne doivent pas casser le site
        return ""
    if (etat.get("profil_actif") or "") != reglages.PROFIL_OLLAMA:
        return ""
    return str(etat.get("endpoint") or "").strip()


def dossier_du_projet(projet: str) -> Path:
    return lib.DOSSIER_ANALYSES / projet


def etat(projet: str) -> dict:
    """État du travail + `pourcent` (0 à 100) et `resume` lisible."""
    e = travail.lire_etat(dossier_du_projet(projet))
    fait, total = int(e.get("fait") or 0), int(e.get("total") or 0)
    e["pourcent"] = int(100 * fait / total) if total else 0
    statut = e.get("statut")
    if statut == "en_cours":
        e["resume"] = f"{e.get('libelle') or e.get('phase', '')} — {fait}/{total}" if total else str(e.get("libelle") or "démarrage")
    elif statut == "termine":
        bilan = e.get("bilan") or {}
        e["resume"] = ("À jour" if bilan.get("inchange") else f"À jour ({len(bilan.get('traites', []))} document(s) traité(s))")
    elif statut == "erreur":
        e["resume"] = "Erreur : " + str(e.get("erreur", ""))[:160]
    elif statut == "interrompu":
        e["resume"] = "Interrompu — relancez, les documents déjà traités sont conservés."
    else:
        e["resume"] = "Pas encore construit"
    return e


def recherche_externe_disponible() -> bool:
    """Un moteur de recherche web est-il configuré (E21_RECHERCHE_URL) ?"""
    return bool(externe.serveur_recherche())


def demarrer(projet: str, *, complet: bool = False, avec_externe: bool = False) -> tuple[bool, str]:
    """Lance la mise à jour en arrière-plan. `(lancé, message)` : jamais d'exception pour l'interface."""
    if avec_externe and not recherche_externe_disponible():
        return False, "La recherche hors des documents n'est pas configurée sur ce serveur (variable E21_RECHERCHE_URL)."
    ollama = endpoint_ollama()
    if not ollama:
        return False, ("La connaissance du projet se construit avec les modèles Ollama : choisissez le profil "
                       "« ollama » dans « Réglages modèles ».")
    dossier = dossier_du_projet(projet)
    if not (dossier / travail.DOSSIER_INTRANTS).is_dir():
        return False, "Ce projet n'a pas encore de documents."
    if not complet and not avec_externe and not travail.a_mettre_a_jour(dossier):
        return False, "Le dossier de connaissance est déjà à jour."
    try:
        travail.lancer(dossier, complet=complet, endpoint=ollama, externe=avec_externe)
    except RuntimeError as exc:
        return False, str(exc)
    return True, "Mise à jour de la connaissance lancée en arrière-plan."


def lire(projet: str) -> dict | None:
    """Contenu de l'index d'un projet pour affichage (lecture seule) ; None si rien n'est encore construit."""
    _, base, _ = travail.chemins(dossier_du_projet(projet))
    if not base.is_file():
        return None
    index = Index(base)
    try:
        documents = index.documents()
        faits = [dict(zip(("doc", "texte", "extrait", "genre"), l)) for l in index.base.execute(
            "SELECT doc, libelle, extrait, genre FROM elements WHERE genre IN ('fait','relation') AND verifie = 1 ORDER BY doc, id")]
        entites = [dict(zip(("nom", "canonique", "type", "docs"), (l[0], l[1], l[2], json.loads(l[3] or "[]"))))
                   for l in index.base.execute("SELECT nom, canonique, type, docs FROM entites ORDER BY canonique, nom")]
        return {"documents": documents, "faits": faits, "entites": entites, "contradictions": index.contradictions(),
                "couvertures": index.couvertures(), "compte": index.compter(), "externes": externe.externes(index),
                "maj": index.lire_meta("derniere_mise_a_jour")}
    finally:
        index.fermer()


def pour_lecture(dossier: Path, texte: str) -> tuple[str, bool]:
    """Texte d'un livrable prêt à afficher : les citations `[E12]` deviennent des notes discrètes (infobulle =
    extrait). Renvoie `(texte, contient_du_html)` ; sans citation ni index, le texte est rendu tel quel."""
    if not citations.RE_CITATION.search(texte):
        return texte, False
    _, base, _ = travail.chemins(dossier)
    if not base.is_file():
        return texte, False
    index = Index(base)
    try:
        details = citations.extraits(index, citations.ids_cites(texte))
    finally:
        index.fermer()
    return citations.pour_affichage(texte, details), True
