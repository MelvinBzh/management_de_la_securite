#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes des contrôles de cohérence par le code (`web/coherence.py`) — aucun modèle."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402
from web import coherence  # noqa: E402

ECHECS: list[str] = []


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


NL = chr(10)
D = Path(tempfile.mkdtemp(prefix="e21-coh-"))
(D / "intrants").mkdir()
w = lambda nom, lignes: (D / nom).write_text(NL.join(lignes) + NL, encoding="utf-8")  # noqa: E731

w("01-actifs.md", ["# Actifs", "", "| ID | Actif | Type |", "|---|---|---|", "| A1 | **Site Lesquin** | site |", "| A2 | StockPilot WMS | logiciel |"])
w("03-menaces.md", ["# Menaces", "", "| ID | Actif | Catégorie | Source |", "|---|---|---|---|",
                    "| M1 | A1 | STRIDE-S | ISO27002-8.22 |", "| M2 | A9 | STRIDE-T | ISO27002-5.15 |", "| M1 | A1 | STRIDE-S | ISO27002-8.22 |"])
w("05-traitement.md", ["# Traitement", "", "| ID | Mesure |", "|---|---|", "| R1 | MFA, voir M1 |", "| R2 | À compléter |", "| R3 | Veille sur M7 |"])

# --- identifiants -------------------------------------------------------------------------------------------------
manque = coherence.identifiants_non_definis(D, ["03-menaces.md", "05-traitement.md"])
verifier("identifiant utilisé sans définition détecté (A9, M7)", set(manque) == {"A9", "M7"})
verifier("identifiants définis (A1, M1, R1…) non signalés", "A1" not in manque and "M1" not in manque and "R1" not in manque)
verifier("« A-1 » et « A1 » sont le même identifiant", coherence.identifiants_non_definis(D, ["03-menaces.md"]).get("A1") is None)

# --- doublons, textes d'attente --------------------------------------------------------------------------------------
verifier("ligne en double détectée", len(coherence.doublons(coherence.lire(D, "03-menaces.md"))) == 1)
verifier("texte d'attente détecté", len(coherence.textes_d_attente(coherence.lire(D, "05-traitement.md"))) == 1)
verifier("tableaux : en-tête et lignes de données séparés", coherence.tableaux(coherence.lire(D, "01-actifs.md"))[0]["entete"] == ["ID", "Actif", "Type"]
         and len(coherence.tableaux(coherence.lire(D, "01-actifs.md"))[0]["lignes"]) == 2)

# --- actifs manquants (index) ---------------------------------------------------------------------------------------------
dc = travail.chemins(D)[0]
dc.mkdir()
idx = Index(travail.chemins(D)[1])
idx.ajouter_entite("Yooz", "Yooz", "systeme", ["a.md", "b.md", "c.md"])
idx.ajouter_entite("StockPilot", "StockPilot WMS", "systeme", ["a.md", "b.md"])
idx.ajouter_entite("Site de Lesquin", "Site Lesquin", "site", ["a.md", "b.md"])
idx.ajouter_entite("Marie Dupont", "Marie Dupont", "personne", ["a.md", "b.md"])
idx.ajouter_entite("Veeam", "Veeam", "systeme", ["a.md"])
idx.fermer()
manquants = coherence.actifs_manquants(D, travail.chemins(D)[1])
verifier("actif multi-documents absent détecté (Yooz)", [m[0] for m in manquants] == ["Yooz"])
verifier("présent sous un alias ou sous son nom : non signalé (StockPilot, Site Lesquin)", all(m[0] not in ("StockPilot WMS", "Site Lesquin") for m in manquants))
verifier("une personne ou une entité à un seul document n'est pas exigée", all(m[0] not in ("Marie Dupont", "Veeam") for m in manquants))
verifier("sans index : aucun faux positif", coherence.actifs_manquants(D, D / "absent.sqlite") == [])

# --- nombres introuvables ---------------------------------------------------------------------------------------------------------
corpus = "Le CA 2025 est de 47,2 M€ avec 341 salariés. Postes fixes : 172 ; portables : 126. Budget 95 k€."
texte = NL.join([
    "| Chiffre d'affaires | 47.2 M€ [E1] |",            # formes décimales équivalentes : retrouvé
    "| Effectif | 352 salariés |",                      # introuvable
    "| Postes | 172 fixes et 126 portables |",         # retrouvé
    "| Mesure | ISO27002-8.22 et ISO 27002-5.15 |",     # références de norme : ignorées
    "| Exposition | probabilité 4,5 sur 10 |",          # score calculé : ignoré
    "| Année | 2024 |",                                 # année : ignorée
    "| Portée | 7 risques et 12 menaces |",            # comptage du livrable : ignoré
    "# 00 — Description du système",                     # titre : ignoré
    "style boundary1 fill:#ffccbc,stroke:#333,stroke-width:2px",   # Mermaid : ignoré
])
trouves = [n for n, _l in coherence.nombres_introuvables(texte, corpus)]
verifier("seul le chiffre réellement absent des documents est signalé (352)", trouves == ["352"])
verifier("milliers avec espace : 1 250 retrouvé dans « 1250 »", coherence.nombres_introuvables("| Budget | 1 250 k€ |", "budget 1250 k€") == [])

# --- contrôle global --------------------------------------------------------------------------------------------------------------------
corr, alertes = coherence.controler(D, ["01-actifs.md", "03-menaces.md", "05-traitement.md"], base_index=travail.chemins(D)[1], corpus=corpus)
verifier("corrections bloquantes : identifiants, actif manquant, doublon, texte d'attente",
         all(x in corr for x in ("A9", "Yooz", "double", "attente")))
verifier("les alertes sont au format parsable [nombre introuvable:n]", all(a.startswith("[nombre introuvable:") for a in alertes))
corr2, _ = coherence.controler(D, ["01-actifs.md"], corpus=corpus)
verifier("un livrable sain n'a aucune correction", corr2 == "")

print("COHERENCE:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
