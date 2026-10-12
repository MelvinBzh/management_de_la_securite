# -*- coding: utf-8 -*-
"""Ce qui a CHANGÉ dans la connaissance depuis le dernier état appliqué aux livrables.

Après l'ajout, la modification ou le retrait de documents, on ne refait pas l'analyse : on calcule d'abord ce qui a
changé, à partir de l'index des preuves (aucun modèle) :

  - documents ajoutés, modifiés (même nom, contenu différent), retirés ;
  - faits NOUVEAUX (rien de semblable avant), CONFIRMÉS (même chose qu'un fait d'un autre document), MODIFIÉS (l'ancien
    fait d'un document devient un fait proche mais différent : « 126 portables » → « 132 portables »), PERDUS (retirés sans
    équivalent) ;
  - contradictions qui touchent les documents changés.

L'« état appliqué » est un instantané (`connaissance/baseline.json`) écrit quand les livrables ont été faits ou mis à
jour : documents (nom → empreinte) et éléments (identifiant → document). Les identifiants de preuve sont stables
(voir `Index.ajouter_element`) : « ajouté » et « retiré » ont donc un sens exact.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import ollama

try:  # accélère la comparaison des vecteurs ; sans lui, le calcul est correct mais plus lent
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

NOM_BASELINE = "baseline.json"
GENRES_SEMANTIQUES = ("fait", "relation")
SEUIL_MODIFIE = 0.80          # ancien fait → nouveau fait du MÊME document
SEUIL_REMPLACE = 0.85         # idem quand le document a été remplacé par un autre nom
SEUIL_CONFIRME = 0.90         # nouveau fait ≈ fait d'un AUTRE document déjà connu


@dataclass
class Delta:
    documents_ajoutes: list[str] = field(default_factory=list)
    documents_modifies: list[str] = field(default_factory=list)
    documents_retires: list[str] = field(default_factory=list)
    nouveaux: list[dict] = field(default_factory=list)       # éléments sans équivalent
    confirmes: list[dict] = field(default_factory=list)      # {"nouveau", "existant", "cos"}
    modifies: list[dict] = field(default_factory=list)       # {"avant", "apres", "cos"}
    perdus: list[dict] = field(default_factory=list)         # éléments retirés sans équivalent
    contradictions: list[dict] = field(default_factory=list)
    ajoutes_ids: set[int] = field(default_factory=set)
    retires_ids: set[int] = field(default_factory=set)

    @property
    def documents_changes(self) -> set[str]:
        return set(self.documents_ajoutes) | set(self.documents_modifies)

    def vide(self) -> bool:
        return not (self.documents_ajoutes or self.documents_modifies or self.documents_retires or self.ajoutes_ids or self.retires_ids)

    def resume(self) -> dict:
        return {"documents_ajoutes": len(self.documents_ajoutes), "documents_modifies": len(self.documents_modifies),
                "documents_retires": len(self.documents_retires), "faits_nouveaux": len(self.nouveaux),
                "faits_confirmes": len(self.confirmes), "faits_modifies": len(self.modifies), "faits_perdus": len(self.perdus),
                "contradictions": len(self.contradictions)}


# ---------------------------------------------------------------------------------------------------------- instantané
def chemin_baseline(dossier: str | Path) -> Path:
    return Path(dossier) / "connaissance" / NOM_BASELINE


def instantane(index) -> dict:
    """État actuel de l'index : documents lus sans erreur (nom → empreinte) et éléments (identifiant → document)."""
    return {
        "documents": {nom: d["empreinte"] for nom, d in index.documents().items() if d["statut"] == "ok"},
        "elements": {str(i): doc for i, doc in index.base.execute("SELECT id, doc FROM elements WHERE origine = 'document'")},
    }


def ecrire_baseline(dossier: str | Path, index, signature: str = "") -> Path:
    """Enregistre l'état actuel comme « appliqué aux livrables »."""
    chemin = chemin_baseline(dossier)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    donnees = instantane(index)
    donnees.update({"date": time.strftime("%Y-%m-%d %H:%M:%S"), "signature": signature})
    temporaire = chemin.with_suffix(".tmp")
    temporaire.write_text(json.dumps(donnees, ensure_ascii=False), encoding="utf-8")
    temporaire.replace(chemin)
    return chemin


def lire_baseline(dossier: str | Path) -> dict | None:
    try:
        donnees = json.loads(chemin_baseline(dossier).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return donnees if isinstance(donnees, dict) and "elements" in donnees else None


# ---------------------------------------------------------------------------------------------------------- comparaison
def _vecteur(brut) -> list[float] | None:
    if not brut:
        return None
    return brut if isinstance(brut, list) else json.loads(brut)


def _plus_proches(requetes: list[list[float] | None], base: list[list[float] | None]) -> list[tuple[int, float]]:
    """Pour chaque vecteur de `requetes`, `(indice dans base, similarité cosinus)` du plus proche ; (-1, 0.0) sinon."""
    sortie = [(-1, 0.0)] * len(requetes)
    valides = [i for i, v in enumerate(base) if v]
    if not valides:
        return sortie
    if np is not None:
        try:
            matrice = np.array([base[i] for i in valides], dtype=float)
            normes = np.linalg.norm(matrice, axis=1)
            normes[normes == 0] = 1.0
            matrice = matrice / normes[:, None]
            for k, v in enumerate(requetes):
                if not v:
                    continue
                q = np.array(v, dtype=float)
                n = np.linalg.norm(q)
                if n == 0 or q.shape[0] != matrice.shape[1]:
                    continue
                scores = matrice @ (q / n)
                meilleur = int(scores.argmax())
                sortie[k] = (valides[meilleur], float(scores[meilleur]))
            return sortie
        except (ValueError, TypeError):
            pass  # vecteurs de tailles différentes : repli sur le calcul pas à pas
    for k, v in enumerate(requetes):
        if not v:
            continue
        meilleur = max(((i, ollama.cosinus(v, base[i])) for i in valides), key=lambda x: x[1])
        sortie[k] = meilleur
    return sortie


def calculer(index, baseline: dict | None, *, contradictions_detail: bool = True) -> Delta:
    """Compare l'index actuel à `baseline` (état appliqué). Sans baseline, tout est « inconnu » : delta vide."""
    delta = Delta()
    if not baseline:
        return delta
    docs_av = baseline.get("documents", {})
    docs_ap = {nom: d["empreinte"] for nom, d in index.documents().items() if d["statut"] == "ok"}
    delta.documents_ajoutes = sorted(n for n in docs_ap if n not in docs_av)
    delta.documents_modifies = sorted(n for n in docs_ap if n in docs_av and docs_ap[n] != docs_av[n])
    delta.documents_retires = sorted(n for n in docs_av if n not in docs_ap)

    courants = {}
    for i, genre, doc, libelle, extrait, vec in index.base.execute(
            "SELECT id, genre, doc, libelle, extrait, vecteur FROM elements WHERE origine = 'document'"):
        courants[int(i)] = {"id": int(i), "genre": genre, "doc": doc, "libelle": libelle, "extrait": extrait, "vecteur": _vecteur(vec)}
    avant_ids = {int(i) for i in baseline.get("elements", {})}
    delta.ajoutes_ids = set(courants) - avant_ids
    delta.retires_ids = avant_ids - set(courants)

    ajoutes = [courants[i] for i in sorted(delta.ajoutes_ids) if courants[i]["genre"] in GENRES_SEMANTIQUES]
    retires_txt = index.retires()
    perdus = [retires_txt[i] for i in sorted(delta.retires_ids) if i in retires_txt and retires_txt[i]["genre"] in GENRES_SEMANTIQUES]

    # 1. ancien fait → nouveau fait proche : le fait a CHANGÉ (même document, ou document remplacé par un autre nom)
    if ajoutes and perdus:
        proches = _plus_proches([a["vecteur"] for a in ajoutes], [p["vecteur"] for p in perdus])
        paires = []
        for k, (j, cos) in enumerate(proches):
            if j < 0:
                continue
            seuil = SEUIL_MODIFIE if ajoutes[k]["doc"] == perdus[j]["doc"] else SEUIL_REMPLACE
            if cos >= seuil:
                paires.append((cos, k, j))
        pris_a, pris_p = set(), set()
        for cos, k, j in sorted(paires, reverse=True):
            if k in pris_a or j in pris_p:
                continue
            pris_a.add(k)
            pris_p.add(j)
            delta.modifies.append({"avant": perdus[j], "apres": ajoutes[k], "cos": round(cos, 3)})
        ajoutes = [a for k, a in enumerate(ajoutes) if k not in pris_a]
        perdus = [p for j, p in enumerate(perdus) if j not in pris_p]
    delta.perdus = perdus

    # 2. nouveau fait ≈ fait déjà connu d'un AUTRE document : il le CONFIRME (rien à changer) ; sinon il est NOUVEAU
    if ajoutes:
        deja = [c for i, c in courants.items() if i not in delta.ajoutes_ids and c["genre"] in GENRES_SEMANTIQUES]
        proches = _plus_proches([a["vecteur"] for a in ajoutes], [d["vecteur"] for d in deja])
        for a, (j, cos) in zip(ajoutes, proches):
            if j >= 0 and cos >= SEUIL_CONFIRME and deja[j]["doc"] != a["doc"]:
                delta.confirmes.append({"nouveau": a, "existant": deja[j], "cos": round(cos, 3)})
            else:
                delta.nouveaux.append(a)

    if contradictions_detail:
        changes = delta.documents_changes
        for c in index.contradictions():
            if c["doc_a"] in changes or c["doc_b"] in changes:
                delta.contradictions.append(c)
    return delta
