#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de la production par lots (`web/lots.py`) — aucun modèle."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402
from web import lots  # noqa: E402

ECHECS: list[str] = []


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


NL = chr(10)
D = Path(tempfile.mkdtemp(prefix="e21-lots-"))
(D / "connaissance").mkdir()
idx = Index(travail.chemins(D)[1])
idx.ajouter_entite("StockPilot", "StockPilot WMS", "systeme", ["a.md", "b.md", "c.md"])
idx.ajouter_entite("Sage X3", "Sage X3", "systeme", ["a.md"])
idx.ajouter_entite("Paie RH", "Données de paie", "donnee", ["a.md", "b.md"])
idx.ajouter_entite("FortiGate", "FortiGate", "materiel", ["a.md", "b.md"])
idx.ajouter_entite("Lesquin", "Site Lesquin", "site", ["a.md"])
idx.ajouter_entite("OPSITEL", "OPSITEL", "prestataire", ["a.md", "b.md"])
idx.ajouter_entite("Marie Dupont", "Marie Dupont", "personne", ["a.md", "b.md"])
idx.ajouter_entite("ISO 27001", "ISO 27001", "norme", ["a.md", "b.md"])

# --- plan de l'étape 1 : trois thèmes, candidats issus de l'index, jamais les personnes ni les normes -----------------
plan1 = lots.plan_etape(D, 1, idx)
liste1 = plan1["01-actifs.md"]
verifier("étape 1 : trois lots par thème", [l.index for l in liste1] == [1, 2, 3])
verifier("candidats classés par nombre de documents (StockPilot d'abord)", liste1[0].entrees[0].startswith("StockPilot WMS (cité par 3 documents)"))
verifier("ni personnes ni normes parmi les candidats", all("Marie" not in e and "ISO" not in e for l in liste1 for e in l.entrees))
verifier("lot matériel et sites : FortiGate et Site Lesquin", any("FortiGate" in e for e in liste1[1].entrees) and any("Lesquin" in e for e in liste1[1].entrees))
verifier("le plan sans index n'invente rien", lots.plan_etape(D, 1, None) == {})
verifier("étape sans lots (2, 6, 7) : en une passe", lots.plan_etape(D, 2, idx) == {} and lots.plan_etape(D, 7, idx) == {})

# --- 03 depuis les actifs ----------------------------------------------------------------------------------------------------
actifs = ["# Actifs", "", "| ID | Actif | Type | Description |", "|---|---|---|---|"] + \
    [f"| A{n:02d} | Actif {n} | Logiciel | desc {n} |" for n in range(1, 13)] + ["| A13 | Entreprise | Site | hors périmètre : la société elle-même |"]
(D / "01-actifs.md").write_text(NL.join(actifs) + NL, encoding="utf-8")
plan3 = lots.plan_etape(D, 3, idx)["03-menaces.md"]
verifier("03 : 12 actifs réels en lots de 5 (5 + 5 + 2) puis le lot des frontières", [len(l.attendus) for l in plan3] == [5, 5, 2, 0])
verifier("03 : un actif « hors périmètre » n'est pas à traiter", all("A13" not in l.attendus for l in plan3))
verifier("03 : les attendus sont les identifiants d'actifs", plan3[0].attendus == ("A01", "A02", "A03", "A04", "A05"))
verifier("03 : le lot des frontières joint 00-description.md et 02-methodes.md", "00-description.md" in plan3[-1].pieces_en_plus)

# --- 04 depuis les menaces, 05 depuis les évaluations ---------------------------------------------------------------------------
menaces = ["# M", "", "| ID | Actif | Cat | Desc | CVE | Src |", "|---|---|---|---|---|---|"] + \
    [f"| M{n:02d} | A01 | STRIDE-S | desc {n} | — | STRIDE-S |" for n in range(1, 18)]
(D / "03-menaces.md").write_text(NL.join(menaces) + NL, encoding="utf-8")
plan4 = lots.plan_etape(D, 4, idx)["04-evaluation.md"]
verifier("04 : 17 menaces en lots de 8 (8 + 8 + 1)", [len(l.attendus) for l in plan4] == [8, 8, 1])
verifier("04 : les identifiants sont ceux des menaces", plan4[0].attendus[0] == "M01" and plan4[2].attendus == ("M17",))
verifier("05 depuis 04 : vide tant que 04 n'existe pas", lots.plan_etape(D, 5, idx) == {})

# --- validation d'une partie -----------------------------------------------------------------------------------------------------
lot3 = plan3[2]   # attendus A11, A12
bonne = NL.join(["| - | A11 Actif 11 | STRIDE-S | Description [E1] | — | STRIDE-S |", "| - | A12 Actif 12 | STRIDE-T | Description [E2] | — | STRIDE-T |"])
lignes, pb = lots.valider_partie(lot3, bonne)
verifier("partie valide : 2 lignes, aucun problème", len(lignes) == 2 and pb == [])
_, pb = lots.valider_partie(lot3, bonne.split(NL)[0])
verifier("élément attendu absent signalé (A12)", any("A12" in p for p in pb))
_, pb = lots.valider_partie(lot3, "| - | A11 | STRIDE-S |")
verifier("mauvais nombre de colonnes signalé", any("colonnes" in p for p in pb))
_, pb = lots.valider_partie(lot3, "")
verifier("partie vide : aucune ligne de tableau valide", pb and "aucune ligne" in pb[0])
entete_et_cloture = "```markdown" + NL + "| ID | Actif concerné | Catégorie (grille) | Description | CVE si connue | Source |" + NL + "|---|---|---|---|---|---|" + NL + bonne + NL + "```"
lignes, pb = lots.valider_partie(lot3, entete_et_cloture)
verifier("clôture de code et en-tête recopiés par le modèle : ignorés", len(lignes) == 2 and pb == [])
lot4 = plan4[2]   # attendu M17
_, pb = lots.valider_partie(lot4, "| M99 | x | Faible | j | Faible | j | Faible | j |")
verifier("04 : un identifiant inattendu n'est pas une ligne valide", any("inattendu" in p for p in pb) and any("M17" in p for p in pb))
lignes, pb = lots.valider_partie(lot4, "| **M17** | menace | Moyenne | j | Élevé | j | Élevé | j |")
verifier("04 : identifiant en gras accepté", len(lignes) == 1 and pb == [])

# --- préfixes que les modèles ajoutent devant les lignes (numéro, tiret, citation) ------------------------------------------------
prefixes = NL.join(["1: | - | A11 Actif 11 | STRIDE-S | Description [E1] | — | STRIDE-S |",
                    "- | - | A12 Actif 12 | STRIDE-T | Description [E2] | — | STRIDE-T |"])
lignes, pb = lots.valider_partie(lot3, prefixes)
verifier("lignes préfixées par « 1: » ou « - » : lues, pas rejetées", len(lignes) == 2 and pb == [])
sans_pipe_final = "| - | A11 Actif 11 | STRIDE-S | Description [E1] | — | STRIDE-S" + NL + "| - | A12 | STRIDE-T | Description [E2] | — | STRIDE-T"
lignes, pb = lots.valider_partie(lot3, sans_pipe_final)
verifier("ligne sans barre finale : lue", len(lignes) == 2 and pb == [])

# --- consigne, entrées ----------------------------------------------------------------------------------------------------------
c = lots.consigne_lot(lot3, 4, "2026-01-01_x", "STRIDE-S, STRIDE-T")
verifier("consigne : fichier de partie, 6 colonnes, « - » pour l'ID, sources autorisées",
         "analyses/2026-01-01_x/parties/03-menaces.3.md" in c and "exactement 6 colonnes" in c and "« - »" in c and "STRIDE-S, STRIDE-T" in c)
c4 = lots.consigne_lot(lot4, 3, "2026-01-01_x", "", ["élément non traité : M17"])
verifier("consigne 04 : l'ID est repris tel quel ; reprise = partie réécrite en entier avec les manquants",
         "EXACTEMENT l'identifiant" in c4 and "EN ENTIER" in c4 and "M17" in c4 and "Matrice" in c4)
verifier("la consigne ne contient aucun contenu de document", "desc 17" not in c4 and "Actif 11" not in c)
e = lots.contenu_entrees(lot3, 4, None, "")
verifier("entrées : liste de contrôle obligatoire", "OBLIGATOIRE" in e and "A11" in e)
e1 = lots.contenu_entrees(liste1[0], 3, ["Veeam (systeme, cité par 2 documents)"], "")
verifier("entrées du lot 1 : candidats indicatifs + supplément à ajouter OBLIGATOIREMENT", "candidats" in e1 and "AJOUTER OBLIGATOIREMENT" in e1 and "Veeam" in e1)

# --- doublons entre lots : le même actif décrit deux fois est fusionné, les preuves réunies -------------------------------------------
dup = [["-", "**FleetTrack**", "Logiciel", "Télématique [E1]", "Haute", "Critique", "[E1]"],
       ["-", "Microsoft 365", "Logiciel", "Mail", "Haute", "Critique", "[E2]"],
       ["-", "FleetTrack", "Prestataire", "Autre description", "Moyenne", "Sensible", "[E1][E9]"]]
fusion, n_f = lots.fusionner_doublons(dup)
verifier("même actif décrit par deux lots : une seule ligne, la première description gardée", n_f == 1 and len(fusion) == 2 and fusion[0][3] == "Télématique [E1]")
verifier("les preuves des deux descriptions sont réunies sans doublon", fusion[0][-1] == "[E1] [E9]")

# --- ciblage d'une reprise ---------------------------------------------------------------------------------------------------------
cibles = lots.lots_concernes(plan3, "A02 : composant inventé. A12 : source inconnue.")
verifier("reprise : seuls les lots dont un identifiant est cité sont refaits", [l.index for l in cibles] == [1, 3])
verifier("reprise : aucun lot concerné si rien ne les désigne", lots.lots_concernes(plan3, "formulation générale sans identifiant") == [])
sup = lots.supplements_actifs([("Veeam", "systeme", 2), ("Pare-feu de bordure", "materiel", 2), ("OPSITEL", "prestataire", 3)], liste1)
verifier("actifs manquants affectés au lot de leur type", sorted(sup) == ["01-actifs:1", "01-actifs:2", "01-actifs:3"])
verifier("un actif manquant fait refaire son lot", [l.index for l in lots.lots_concernes(liste1, "", {"01-actifs:2": ["x"]})] == [2])

# --- assemblage ------------------------------------------------------------------------------------------------------------------------
(D / "parties").mkdir()
for lot, rows in ((plan3[0], [f"| - | A{n:02d} Actif {n} | STRIDE-S | d [E1] | — | STRIDE-S |" for n in range(1, 6)]),
                  (plan3[2], [bonne.split(NL)[0].replace("A11", "A11"), bonne.split(NL)[1]])):
    lots.fichier_partie(D, lot).write_text(NL.join(rows), encoding="utf-8")
n = lots.assembler(D, "03-menaces.md", plan3)
final = (D / "03-menaces.md").read_text(encoding="utf-8")
verifier("assemblage : 7 lignes (parties absentes ignorées)", n == 7)
verifier("assemblage : titre, en-tête, séparateur", final.startswith("# Menaces (étape 3)") and "| ID | Actif concerné | Catégorie (grille) | Description | CVE si connue | Source |" in final and "|---|---|---|---|---|---|" in final)
verifier("assemblage : identifiants posés par le code, dans l'ordre", "| M01 |" in final and "| M07 |" in final and "| M08 |" not in final)
(D / "04-evaluation.md").unlink(missing_ok=True)
lots.fichier_partie(D, plan4[2]).write_text("| M17 | menace | Moyenne | j | Élevé | j | Élevé | j |", encoding="utf-8")
lots.assembler(D, "04-evaluation.md", plan4)
ev = (D / "04-evaluation.md").read_text(encoding="utf-8")
verifier("04 assemblé : matrice rappelée, identifiant de la menace conservé", "Matrice probabilité" in ev and "| M17 |" in ev)

print("LOTS:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
