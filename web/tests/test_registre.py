#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes : registre, validation et synthèse établis par le code (`web/registre.py`) — aucun modèle."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from web import lib, registre  # noqa: E402

ECHECS: list[str] = []


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


NL = chr(10)
D = Path(tempfile.mkdtemp(prefix="e21-reg-"))
(D / "intrants").mkdir()
w = lambda nom, lignes: (D / nom).write_text(NL.join(lignes) + NL, encoding="utf-8")  # noqa: E731

w("01-actifs.md", ["# Actifs", "", "| ID | Actif | Type |", "|---|---|---|", "| A01 | NordTMS | logiciel |", "| A02 | Site Lesquin | site |"])
w("03-menaces.md", ["# Menaces", "", "| ID | Actif concerné | Catégorie (grille) | Description | CVE si connue | Source |", "|---|---|---|---|---|---|",
                    "| M001 | A01 — NordTMS | STRIDE-S | Vol de données clients [E12] | — | STRIDE-S, ANSSI-PSSI |",
                    "| M002 | A01 — NordTMS | STRIDE-T | Altération des tournées | — | STRIDE-T |",
                    "| M003 | A02 — Site Lesquin | STRIDE-D | Coupure électrique prolongée | — | STRIDE-D |",
                    "| M004 | A02 — Site Lesquin | STRIDE-E | Accès physique non contrôlé | — | STRIDE-E |"])
w("04-evaluation.md", ["# Évaluation", "", "| ID | Menace | Probabilité | Impact | Niveau | Justification |", "|---|---|---|---|---|---|",
                       "| M001 | A01 vol | Élevé | Critique | Critique | MFA absente [E12] |",
                       "| M002 | A01 altération | Moyen | Élevé | Élevé | Pas de journal |",
                       "| M003 | A02 coupure | Faible | Moyen | Faible | Onduleur testé |",
                       "| M004 | A02 accès | Moyen | Moyen | Moyen | Badge partagé |"])
w("05-traitement.md", ["# Traitement", "", "| ID | Actif et menace | Traitement | Contre-mesures | Sources | Risque résiduel estimé |", "|---|---|---|---|---|---|",
                       "| M001 | A01 vol | Réduire | MFA + cloisonnement base [ISO27002-5.15] | ISO27002-5.15 STRIDE-S | Moyen |",
                       "| M002 | A01 altération | Réduire | Journalisation centralisée | ANSSI-HYGIENE-4 | Faible |",
                       "| M003 | A02 coupure | Accepter | Aucune | STRIDE-D | Faible |",
                       "| M004 | A02 accès | Éviter | Contrôle d'accès | ISO27002-5.15 | Faible |"])

# --- lecture et correspondance --------------------------------------------------------------------------------------------
risques, pb = registre.lire_risques(D)
verifier("4 risques lus, aucun problème de correspondance", len(risques) == 4 and pb == [])
verifier("les sources des étapes 3 et 5 sont réunies sans doublon", risques[0]["sources"] == ["STRIDE-S", "ANSSI-PSSI", "ISO27002-5.15"])
verifier("la menace garde catégorie et description", risques[0]["menace"].startswith("STRIDE-S — Vol de données"))

# --- registre + validation ----------------------------------------------------------------------------------------------------
n, pb = registre.ecrire_registre_et_validation(D)
verifier("registre, validation et JSON écrits", n == 4 and pb == [] and all((D / f).is_file() for f in ("registre-risques.md", "06-validation.md", lib.NOM_JSON_REGISTRE)))
colonnes, lignes = lib.lire_registre(D)
verifier("le registre se lit avec le lecteur du site (ID de M001 à M004)", [r["ID"] for r in lignes] == ["M001", "M002", "M003", "M004"] and colonnes[0] == "ID")
verifier("valide_par vide et statut « À valider » partout", all(r["valide_par"] == "" and r["Statut"] == registre.STATUT_A_VALIDER for r in lignes))
verifier("niveau et traitement repris tels quels", lignes[0]["Niveau"] == "Critique" and lignes[2]["Traitement"] == "Accepter" and lignes[1]["Risque résiduel"] == "Faible")
donnees = json.loads((D / lib.NOM_JSON_REGISTRE).read_text(encoding="utf-8"))
verifier("JSON : une entrée par risque, valide_par nul", len(donnees["risques"]) == 4 and all(r["valide_par"] is None for r in donnees["risques"]))
val = (D / "06-validation.md").read_text(encoding="utf-8")
verifier("06-validation : aucune décision écrite, plan de suivi présent", "Critique | tous les mois" in val and "À décider" in val and "Refusé |" not in val)
verifier("06-validation cite le référentiel d'homologation", "ANSSI-HOMOLOGATION" in val)
verifier("contrôle du registre : conforme", registre.verifier_registre(D) == [])

# --- une reconstruction CONSERVE les décisions ------------------------------------------------------------------------------
reg = (D / "registre-risques.md").read_text(encoding="utf-8").split(NL)
reg = [l.replace("| M002 |", "| M002 |", 1) for l in reg]
for i, l in enumerate(reg):
    if l.startswith("| M002 |"):
        cel = l.split("|")
        cel[-3] = " Alice · accepté · 2026-10-11 "   # colonne valide_par
        reg[i] = "|".join(cel)
(D / "registre-risques.md").write_text(NL.join(reg), encoding="utf-8")
with open(D / "06-validation.md", "a", encoding="utf-8") as f:
    f.write(NL + "## Validation humaine — 2026-10-11 10:00" + NL + NL + "- **valide_par** : Alice" + NL)
registre.ecrire_registre_et_validation(D)
_c, lignes = lib.lire_registre(D)
verifier("décision conservée après reconstruction (valide_par, statut)", "Alice" in lignes[1]["valide_par"] and lignes[1]["Statut"] == registre.STATUT_DECIDE)
verifier("section « Validation humaine » conservée", "## Validation humaine — 2026-10-11 10:00" in (D / "06-validation.md").read_text(encoding="utf-8"))

# --- contrôle : une menace manquante est vue ----------------------------------------------------------------------------------
copie = (D / "registre-risques.md").read_text(encoding="utf-8").split(NL)
(D / "registre-risques.md").write_text(NL.join(l for l in copie if not l.startswith("| M004 |")), encoding="utf-8")
verifier("menace absente du registre : détectée", any("M004" in p for p in registre.verifier_registre(D)))
registre.ecrire_registre_et_validation(D)

# --- synthèse ---------------------------------------------------------------------------------------------------------------------
n, pb = registre.ecrire_synthese(D)
syn = (D / "SYNTHESE.md").read_text(encoding="utf-8")
verifier("synthèse écrite par le code, chiffres du registre", n == 4 and pb == [] and "| Risques au registre | 4 |" in syn and "| Actifs analysés | 2 |" in syn)
verifier("répartition par niveau exacte", "| Niveau Critique | 1 (25 %) |" in syn and "| Niveau Faible | 1 (25 %) |" in syn)
verifier("risques prioritaires : le plus grave en tête", syn.find("| M001 |") < syn.find("| M002 |", syn.find("## 4.")))
verifier("décision conservée dans la synthèse", "Alice" in syn and "## 6. Décisions de l'analyste" in syn)
verifier("contrôle de la synthèse : conforme", registre.verifier_synthese(D) == [])
verifier("chaque action est liée à un risque du registre", "| Critique | M001 |" in syn)
(D / "SYNTHESE.md").write_text(syn + NL + "Le produit M365 est cité dans une phrase." + NL, encoding="utf-8")
verifier("« M365 » dans une phrase n'est pas pris pour un identifiant de risque", registre.verifier_synthese(D) == [])
(D / "SYNTHESE.md").write_text(syn + NL + "| M999 | actif | menace |" + NL, encoding="utf-8")
verifier("un identifiant inconnu en 1re cellule d'un tableau est signalé", any("M999" in p for p in registre.verifier_synthese(D)))
(D / "SYNTHESE.md").write_text(syn, encoding="utf-8")

# --- texte de lecture du modèle ---------------------------------------------------------------------------------------------------
faits = registre.faits_pour_le_modele(registre.chiffres(D, registre.risques_du_registre(D)))
bon = ("La direction doit retenir que le risque se concentre sur NordTMS, qui porte " + "des risques importants. " * 8
       + "Sur les 4 risques, 1 est critique et 1 est élevé ; le reste est à surveiller sans urgence.")
verifier("lecture valide : chiffres tous présents dans les faits", registre.lecture_valide(bon, faits) == (True, ""))
verifier("lecture refusée : nombre inventé", not registre.lecture_valide(bon + " Soit 87 menaces au total.", faits)[0])
verifier("lecture refusée : source citée", not registre.lecture_valide(bon + " Voir ISO27002-5.15.", faits)[0])
verifier("lecture refusée : trop courte", not registre.lecture_valide("Tout va bien.", faits)[0])
n, _ = registre.ecrire_synthese(D, lecture=bon)
verifier("lecture insérée et étiquetée dans la synthèse", "rédigée par le modèle" in (D / "SYNTHESE.md").read_text(encoding="utf-8"))

# --- jamais de registre vide qui écrase un registre existant ----------------------------------------------------------------------
avant = (D / "registre-risques.md").read_text(encoding="utf-8")
(D / "03-menaces.md").unlink()
n0, pb0 = registre.ecrire_registre_et_validation(D)
verifier("sans menaces : rien n'est écrasé, le problème est dit", n0 == 0 and pb0 and (D / "registre-risques.md").read_text(encoding="utf-8") == avant)

print("REGISTRE:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
