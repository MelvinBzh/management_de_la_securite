#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes : contexte des faits de tableau, garde-fou « non documenté », fraîcheur — aucun modèle."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import couverture, fiches, ingestion, relations, travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402
from web import controles  # noqa: E402

RESULTATS: list[tuple[str, bool]] = []


def verifier(nom: str, condition: bool) -> None:
    RESULTATS.append((nom, bool(condition)))


NL = chr(10)

# --- un fait de tableau garde son en-tête de colonnes (mesuré : « 95 » en k€ lu comme 95 postes) --------------------
contenu = NL.join(["# Extrait", "<<<DONNÉES>>>", "## Feuille « Budget_SI_2026 »", "",
                   "| Poste | Budget (k€) | Réalisé (k€) |", "|---|---|---|",
                   "| Postes de travail / terminaux radio | 95 | 40 |", "| Cybersécurité | 120 | 60 |",
                   "Texte de remplissage. " * 20, "<<<FIN DONNÉES>>>"])
D = Path(tempfile.mkdtemp(prefix="e21-gf-"))
(D / "intrants").mkdir()
(D / "intrants" / "budget.md").write_text(contenu, encoding="utf-8")


def faits(nom, texte):
    return [fiches.Fait(nom, "Il existe 95 postes de travail", "| Postes de travail / terminaux radio | 95 | 40 |", True),
            fiches.Fait(nom, "Le budget est suivi", "Texte de remplissage. Texte de remplissage.", True)]


moteurs = ingestion.Moteurs(faits, lambda n, c: ([], []), lambda t, **_: [[1.0, 0.0, 1.0] for _ in t],
                            lambda index, **_: [], lambda index, besoin, vec=None, **_: couverture.Reponse(
                                besoin, couverture.INCONNU, "", (), "", "sans_objet", True, ""))
index = Index(":memory:")
ingestion.traiter_document(index, "budget.md", contenu, moteurs)
libelles = [l for (l,) in index.base.execute("SELECT libelle FROM elements WHERE genre = 'fait' ORDER BY id")]
verifier("fait de tableau : le libellé porte la section et l'en-tête de colonnes",
         "Budget (k€)" in libelles[0] and "Budget_SI_2026" in libelles[0] and libelles[0].endswith("Il existe 95 postes de travail"))
verifier("fait de texte courant : libellé inchangé", libelles[1] == "Le budget est suivi")

# --- garde-fou : « non documenté » seulement si aucun passage ne parle du sujet -----------------------------------------
idx = Index(":memory:")
idx.ajouter_element("passage", "pra.md", "Plan de reprise", "La restauration des sauvegardes n'a pas été testée depuis 2024, "
                    "la dernière restauration réussie date de mars 2023.", True)
besoin = couverture.Besoin("cont-restau", "Continuité", "Quand a eu lieu la dernière restauration de sauvegarde réussie ?")
passages_proches = couverture.passages_aux_mots_de_la_question(idx, besoin.question)
verifier("les passages aux mots de la question sont retrouvés (mots-clés seuls)", len(passages_proches) == 1 and passages_proches[0]["doc"] == "pra.md")
r = couverture.evaluer(idx, besoin, None, juge=lambda b, c, m: {"statut": "inconnu", "passages": [], "reponse": "", "manque": "journal"})
verifier("« inconnu » du juge MAIS des passages parlent du sujet : relecture demandée, pas de certitude",
         r.statut == couverture.INCONNU and r.a_valider and "relire avant de conclure" in r.pourquoi and "pra.md" in r.pourquoi)
vide = Index(":memory:")
vide.ajouter_element("passage", "autre.md", "Restauration", "Tarifs de la cantine et horaires d'ouverture.", True)
r2 = couverture.evaluer(vide, besoin, None, juge=lambda b, c, m: {"statut": "inconnu", "passages": [], "reponse": "", "manque": "journal"})
verifier("vraiment rien : « non documenté, à demander » comme avant", r2.statut == couverture.INCONNU and "relire avant de conclure" not in r2.pourquoi)
verifier("un besoin à un seul mot significatif ne déclenche pas le garde-fou",
         couverture.passages_aux_mots_de_la_question(idx, "Qui est le DPO ?") == [])

# --- fraîcheur : les livrables savent sur quels documents ils ont été faits ------------------------------------------------
P = Path(tempfile.mkdtemp(prefix="e21-fr-"))
(P / "intrants").mkdir()
(P / "connaissance").mkdir()
i2 = Index(travail.chemins(P)[1])
i2.enregistrer_document("a.md", "h-a1")
i2.enregistrer_document("b.md", "h-b1")
i2.fermer()
s1 = travail.signature_documents(P)
verifier("signature stable et non vide", s1 and s1 == travail.signature_documents(P))
i3 = Index(travail.chemins(P)[1])
i3.enregistrer_document("b.md", "h-b2")  # b.md modifié
i3.fermer()
s2 = travail.signature_documents(P)
verifier("un document modifié change la signature", s2 != s1)
controles.enregistrer(P, 1, "Étape 1", "g", "conforme", "", None, "x", signature=s1)
controles.enregistrer(P, 2, "Étape 2", "g", "conforme", "", None, "x", signature=s1)
controles.enregistrer(P, 3, "Étape 3", "g", "conforme", "", None, "x", signature=s1)
verifier("documents inchangés : aucune étape périmée", controles.etapes_perimees(P, s1) == [])
verifier("documents changés : toutes les étapes concernées (et leurs suivantes) sont périmées", controles.etapes_perimees(P, s2) == ["1", "2", "3"])
controles.enregistrer(P, 1, "Étape 1", "g", "conforme", "", None, "x", signature=s2)
verifier("une étape refaite sur les nouveaux documents n'est plus périmée, ses suivantes le restent", controles.etapes_perimees(P, s2) == ["2", "3"])
verifier("sans signature courante : rien n'est déclaré périmé", controles.etapes_perimees(P, "") == [])

echecs = [n for n, ok in RESULTATS if not ok]
for n, ok in RESULTATS:
    print(("PASS " if ok else "FAIL ") + n)
print(f"GARDE-FOUS: {len(RESULTATS) - len(echecs)} PASS, {len(echecs)} FAIL")
sys.exit(1 if echecs else 0)
