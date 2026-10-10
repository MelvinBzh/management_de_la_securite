#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de la propagation des décisions (`web/propagation.py`) — aucun modèle contacté."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance.index import Index  # noqa: E402
from web import lib, propagation  # noqa: E402

ECHECS: list[str] = []


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


NL = chr(10)
REGISTRE = NL.join([
    "# Registre", "",
    "| ID | Actif | Menace | Probabilité | valide_par | Date validation |", "|---|---|---|---|---|---|",
    "| R-01 | Site | Vol de comptes | Forte | *À valider par l'analyste* | — |",
    "| R-10 | Base | Fuite | Moyenne | *À valider par l'analyste* | — |",
    "| R-02 | ERP | Panne | Moyenne | *À valider par l'analyste* | — |", ""])
MENACES = NL.join(["# Menaces", "", "| Menace | Risque | Source |", "|---|---|---|",
                   "| Vol de comptes | R-01 | STRIDE-S |", "| Fuite | R-10 | STRIDE-I |", ""])
EVAL = NL.join(["# Évaluation", "", "| Risque | Probabilité | Impact |", "|---|---|---|",
                "| R-01 | Forte | Grave |", "| R-02 | Moyenne | Moyen |", ""])


def projet() -> Path:
    d = Path(tempfile.mkdtemp(prefix="e21-prop-")) / "analyses" / "2026-01-01_x"
    d.mkdir(parents=True)
    (d / "registre-risques.md").write_text(REGISTRE, encoding="utf-8")
    (d / "03-menaces.md").write_text(MENACES, encoding="utf-8")
    (d / "04-evaluation.md").write_text(EVAL, encoding="utf-8")
    (d / "06-validation.md").write_text("# V" + NL, encoding="utf-8")
    return d


def termes_simples(texte: str, base: str) -> list[str]:
    return ["nginx"] if "nginx" in texte.lower() and "nginx" not in base else []


d = projet()
liees = propagation.lignes_liees(d, "R-01")
verifier("lignes liées : R-01 trouvé dans le registre, les menaces et l'évaluation", sorted({n for n, _p, _l in liees}) == ["03-menaces.md", "04-evaluation.md", "registre-risques.md"])
verifier("lignes liées : R-01 ne capte pas R-10", not any("R-10" in l for _n, _p, l in liees))
verifier("lignes liées : R-1 (préfixe) ne capte rien", propagation.lignes_liees(d, "R-1") == [])

lib.enregistrer_decisions(d, "Marie", {
    "R-01": {"decision": "modifie", "commentaire": "Probabilité faible : le MFA est déployé"},
    "R-10": {"decision": "refuse", "commentaire": "Hors périmètre"},
    "R-02": {"decision": "accepte", "commentaire": ""}})
verifier("seules les décisions modifié/refusé sont à propager", sorted(x["risque"] for x in propagation.en_attente(d)) == ["R-01", "R-10"])

appels = []
def bon_modele(consigne):
    appels.append(consigne)
    lignes = [l for l in consigne.split(NL) if l[:2].rstrip(".").isdigit() and "R-01" in l]
    sortie = []
    for l in lignes:
        numero = int(l.split(".")[0])
        texte = l.split("] ", 1)[1]
        if "registre" in l or "Forte" in l:
            nouveau = texte.replace("Forte", "Faible (analyste)")
            nouveau = nouveau.replace("| *À valider par l'analyste* |", "| MODÈLE-A-ÉCRASÉ |")  # le modèle tente de toucher valide_par
            sortie.append({"numero": numero, "nouvelle": nouveau})
    return {"lignes": sortie}

index = Index(":memory:")
e1 = index.ajouter_element("fait", "audit.md", "MFA déployé", "Le MFA est déployé sur tous les comptes", True)
trace = propagation.propager(d, reecrire=bon_modele, index=index, base="vol de comptes", termes=termes_simples, journal=lambda *_: None)
verifier("deux décisions propagées, une trace chacune", sorted(t["risque"] for t in trace) == ["R-01", "R-10"])
registre = (d / "registre-risques.md").read_text(encoding="utf-8")
verifier("la ligne liée du registre est réécrite", "Faible (analyste)" in registre)
verifier("la colonne valide_par n'est JAMAIS réécrite par le modèle", "MODÈLE-A-ÉCRASÉ" not in registre and "Marie · accepté avec modification" in registre)
verifier("une ligne non liée (R-02) reste identique", "| R-02 | ERP | Panne | Moyenne |" in registre and "| R-10 | Base | Fuite | Moyenne |" in registre)
verifier("l'évaluation liée est réécrite, sa ligne non liée intacte", "Faible (analyste)" in (d / "04-evaluation.md").read_text(encoding="utf-8") and "| R-02 | Moyenne | Moyen |" in (d / "04-evaluation.md").read_text(encoding="utf-8"))
verifier("les menaces non concernées par le modèle restent identiques", (d / "03-menaces.md").read_text(encoding="utf-8") == MENACES)
refus = next(t for t in trace if t["risque"] == "R-10")
verifier("risque refusé : aucune ligne réécrite, motif tracé", refus["modifiees"] == [] and "écarté" in refus["message"] and len(appels) == 1)
verifier("la trace PROPAGATION.md garde l'avant et l'après", "avant :" in (d / "PROPAGATION.md").read_text(encoding="utf-8") and "après :" in (d / "PROPAGATION.md").read_text(encoding="utf-8"))
verifier("le modèle a reçu la décision de l'analyste et des preuves", "MFA est déployé" in appels[0] and f"[E{e1}]" in appels[0])
verifier("décisions marquées propagées : plus rien en attente", propagation.en_attente(d) == [])
apres = len(appels)
propagation.propager(d, reecrire=bon_modele, index=index, base="", termes=termes_simples, journal=lambda *_: None)
verifier("relancer ne rappelle pas le modèle", len(appels) == apres)

# --- contrôles du code sur une ligne réécrite ---------------------------------------------------------------
orig = "| R-01 | Site | Vol de comptes | Forte | *À valider* | — |"
def ctrl(nouvelle, est_registre=True, ids=lambda i: i == 7):
    return propagation.controler_ligne(orig, nouvelle, "R-01", ids_existants=ids, base="vol de comptes", termes=termes_simples,
                                       admin=[4, 5], est_registre=est_registre)
verifier("contrôle : colonne en trop refusée", ctrl("| R-01 | Site | Vol | Forte | x | — | y |")[0] == orig)
verifier("contrôle : identifiant de risque disparu refusé", "identifiant" in ctrl("| R-99 | Site | Vol | Forte | x | — |")[1])
verifier("contrôle : preuve inexistante refusée", "[E9]" in ctrl("| R-01 | Site | Vol [E9] | Forte | x | — |")[1])
verifier("contrôle : preuve existante acceptée", ctrl("| R-01 | Site | Vol [E7] | Faible | *À valider* | — |")[1] == "")
verifier("contrôle : composant inventé refusé", "nginx" in ctrl("| R-01 | Site nginx | Vol | Forte | x | — |")[1])
verifier("contrôle : ce n'est plus un tableau refusé", "tableau" in ctrl("Le risque est faible.")[1])
verifier("contrôle : valide_par et date restaurés", ctrl("| R-01 | Site | Vol | Faible | PIRATE | 2099 |")[0].endswith("| *À valider* | — |"))

# --- le modèle tombe en panne : rien n'est cassé ----------------------------------------------------------------
d2 = projet()
lib.enregistrer_decisions(d2, "Marie", {"R-01": {"decision": "modifie", "commentaire": "faible"}})
def panne(_c):
    raise RuntimeError("Ollama injoignable")
t2 = propagation.propager(d2, reecrire=panne, base="", termes=termes_simples, journal=lambda *_: None)
verifier("panne du modèle : lignes intactes et motif donné", (d2 / "03-menaces.md").read_text(encoding="utf-8") == MENACES and "impossible" in t2[0]["message"])

print("PROPAGATION:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
