#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes : les identifiants de preuve `[E…]` sont STABLES quand un document est retraité ou retiré.

    python3 tools/connaissance/tests/test_stabilite.py

Un livrable cite `[E1233]` : si ce numéro était réattribué à un autre fait (SQLite réutilise les numéros libérés en fin de
table), la citation mentirait sans qu'on le voie. On vérifie aussi qu'un premier lancement donne les mêmes numéros qu'avant.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import couverture, fiches, ingestion  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402

RESULTATS: list[tuple[str, bool]] = []


def verifier(nom: str, condition: bool) -> None:
    RESULTATS.append((nom, bool(condition)))


def document(sujet: str, *lignes: str) -> str:
    return f"# {sujet}\n\n" + "\n".join(lignes) + "\n" + ("Texte de remplissage sans importance pour le test. " * 8) + "\n"


def faux_moteurs():
    def faits(nom, contenu):
        return [fiches.Fait(nom, "Le document dit : " + l, l, True) for l in contenu.splitlines() if l.startswith("Fait")]
    return ingestion.Moteurs(faits, lambda n, c: ([], []), lambda t, **_: [[float(len(x) % 7), 1.0, 0.5] for x in t],
                             lambda index, **_: [], lambda index, besoin, vec=None, **_: couverture.Reponse(
                                 besoin, couverture.INCONNU, "", (), "", "sans_objet", True, ""))


def ids_faits(index: Index, doc: str) -> dict[str, int]:
    return {extrait: i for i, extrait in index.base.execute("SELECT id, extrait FROM elements WHERE doc = ? AND genre = 'fait'", (doc,))}


M = faux_moteurs()

# --- 1. un premier lancement : les numéros sont ceux d'avant (1, 2, 3… dans l'ordre d'insertion) ------------------------------------
idx = Index(":memory:")
ingestion.traiter_document(idx, "a.md", document("A", "Fait A1 : le serveur est à Lesquin", "Fait A2 : la sauvegarde est quotidienne"), M)
ingestion.traiter_document(idx, "b.md", document("B", "Fait B1 : le pare-feu est un FortiGate", "Fait B2 : 126 portables"), M)
tous = [i for (i,) in idx.base.execute("SELECT id FROM elements ORDER BY id")]
verifier("premier lancement : numéros consécutifs depuis 1 (comportement inchangé)", tous == list(range(1, len(tous) + 1)))
avant_b = ids_faits(idx, "b.md")
max_avant = max(tous)

# --- 2. un document modifié : les faits identiques gardent leur numéro, le fait changé en reçoit un NOUVEAU -----------------------
ingestion.traiter_document(idx, "b.md", document("B", "Fait B1 : le pare-feu est un FortiGate", "Fait B2 : 132 portables", "Fait B3 : nouveau"), M)
apres_b = ids_faits(idx, "b.md")
verifier("fait inchangé : même numéro", apres_b["Fait B1 : le pare-feu est un FortiGate"] == avant_b["Fait B1 : le pare-feu est un FortiGate"])
verifier("fait modifié : nouveau numéro, supérieur à tout numéro déjà attribué", apres_b["Fait B2 : 132 portables"] > max_avant)
verifier("fait ajouté : nouveau numéro supérieur", apres_b["Fait B3 : nouveau"] > max_avant)
retires = idx.retires()
ancien_b2 = avant_b["Fait B2 : 126 portables"]
verifier("l'ancien fait modifié est gardé à part, avec son texte", ancien_b2 in retires and retires[ancien_b2]["extrait"] == "Fait B2 : 126 portables")
verifier("un numéro repris n'est pas « retiré »", avant_b["Fait B1 : le pare-feu est un FortiGate"] not in retires)
verifier("le numéro retiré n'est pas réattribué", ancien_b2 not in {i for (i,) in idx.base.execute("SELECT id FROM elements")})

# --- 3. un document retiré en FIN de table : ses numéros ne sont pas réutilisés par le document suivant --------------------------
derniers = [i for (i,) in idx.base.execute("SELECT id FROM elements WHERE doc = 'b.md'")]
idx.supprimer_document("b.md")
ingestion.traiter_document(idx, "c.md", document("C", "Fait C1 : tout neuf"), M)
nouveaux = [i for (i,) in idx.base.execute("SELECT id FROM elements WHERE doc = 'c.md'")]
verifier("numéros du dernier document retiré non réattribués", not set(nouveaux) & set(derniers) and min(nouveaux) > max(derniers))
verifier("les éléments du document retiré sont consultables (texte et vecteur)",
         all(i in idx.retires() and idx.retires()[i]["vecteur"] for i in derniers))

# --- 4. un document identique retraité en entier (« tout refaire ») : aucun numéro ne bouge ---------------------------------------
avant_a = ids_faits(idx, "a.md")
ingestion.traiter_document(idx, "a.md", document("A", "Fait A1 : le serveur est à Lesquin", "Fait A2 : la sauvegarde est quotidienne"), M)
verifier("retraitement identique : tous les numéros sont conservés", ids_faits(idx, "a.md") == avant_a)
verifier("retraitement identique : rien n'est déclaré retiré pour ce document", not [r for r in idx.retires().values() if r["doc"] == "a.md"])

# --- 5. la mémoire du plus grand numéro survit à la réouverture du fichier ---------------------------------------------------------
idx.fermer()
idx2 = Index(":memory:")
verifier("index neuf : plus grand numéro attribué = 0", idx2.lire_meta("element_id_max", "0") == "0")

echecs = [n for n, ok in RESULTATS if not ok]
for n, ok in RESULTATS:
    print(("PASS " if ok else "FAIL ") + n)
print(f"STABILITE: {len(RESULTATS) - len(echecs)} PASS, {len(echecs)} FAIL")
sys.exit(1 if echecs else 0)
