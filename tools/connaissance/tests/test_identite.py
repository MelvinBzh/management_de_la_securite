#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de la carte d'identité des documents (`identite`) — aucun modèle."""
from __future__ import annotations

import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import identite  # noqa: E402

RESULTATS: list[tuple[str, bool]] = []


def verifier(nom: str, condition: bool) -> None:
    RESULTATS.append((nom, bool(condition)))


for nom, type_attendu, rang in (
    ("Rapport_financier_2025.pdf.md", "rapport financier", 5), ("Audit_interne_SI_2026-06.docx.md", "audit", 5),
    ("Budget_SI_et_inventaire_materiel.xlsx.md", "données de référence", 5), ("Journal_incidents_2025-2026.md", "données de référence", 5),
    ("Registre_RGPD_traitements.xlsx.md", "données de référence", 5), ("Schema_reseau_zones_v3.2.png.md", "données de référence", 5),
    ("COMEX_Septembre_2026.pptx.md", "présentation", 2), ("README_Presentation_entreprise.md", "présentation", 2),
    ("PSSI_NordVal_v2.1.docx.md", "politique ou procédure", 3), ("PRA_v1.3.docx.md", "politique ou procédure", 3),
    ("Charte_informatique_v3.docx.md", "politique ou procédure", 3), ("Organigramme_2026.png.md", "organigramme / compte rendu", 4),
    ("Truc_divers.md", "document", 3),
):
    c = identite.carte(nom)
    verifier(f"type de {nom}", c["type"] == type_attendu and c["rang"] == rang)

verifier("date : mois et année en toutes lettres (Septembre_2026)", identite.date_du_document("COMEX_Septembre_2026.pptx.md") == "2026-09")
verifier("date : AAAA-MM dans le nom", identite.date_du_document("Audit_interne_SI_2026-06.docx.md") == "2026-06")
verifier("date : jj/mm/aaaa dans le texte", identite.date_du_document("x.md", "<<<DONNÉES>>> Validée le 15/03/2023 par la direction") == "2023-03")
verifier("date : la plus récente du texte est retenue", identite.date_du_document("x.md", "<<<DONNÉES>>> 2021-04-01 puis mise à jour le 2024-11-05") == "2024-11")
verifier("date : une année future seule (horizon 2028) n'est pas une date", identite.date_du_document("Note_2026-2028.md") in ("2026", ""))
verifier("date : l'en-tête technique de l'ingestion est ignoré", identite.date_du_document("x.md", "# Extrait\n- Taille : 2030 octets\n<<<DONNÉES>>> sans date") == "")
a, b = identite.carte("COMEX_Septembre_2026.pptx.md"), identite.carte("Rapport_financier_2025.pdf.md")
cote, raison = identite.proposer(a, b)
verifier("proposition : le rapport financier l'emporte sur le diaporama", cote == "b" and "plus fiable" in raison)
cote, raison = identite.proposer({"type": "audit", "rang": 5, "date": "2024-01"}, {"type": "audit", "rang": 5, "date": "2026-02"})
verifier("proposition : à égalité, le plus récent", cote == "b" and "plus récent" in raison)
cote, raison = identite.proposer({"type": "audit", "rang": 5, "date": ""}, {"type": "audit", "rang": 5, "date": "2026-02"})
verifier("proposition : date manquante d'un côté, aucune proposition", cote == "" and "trancher" in raison)

echecs = [n for n, ok in RESULTATS if not ok]
for n, ok in RESULTATS:
    print(("PASS " if ok else "FAIL ") + n)
print(f"IDENTITE: {len(RESULTATS) - len(echecs)} PASS, {len(echecs)} FAIL")
sys.exit(1 if echecs else 0)
