#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mise à jour incrémentale : coupure en cours de route (reprise sans rien refaire ni dupliquer) et décisions anciennes (sans empreinte).

Aucun modèle, aucun réseau.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import zlib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import couverture, delta, fiches, ingestion, travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402
from web import lib, lots, miseajour, propagation, registre, validations  # noqa: E402

ECHECS: list[str] = []
NL = chr(10)


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


def document(sujet: str, *lignes: str) -> str:
    return f"# {sujet}\n\n" + "\n".join(lignes) + "\n" + ("Texte de remplissage sans importance pour le test. " * 8) + "\n"


def vecteur_de(texte: str) -> list[float]:
    v = [0.0] * 64
    for mot in texte.lower().replace(":", " ").replace(".", " ").split():
        v[zlib.crc32(mot.encode()) % 64] += 1.0
    return v


M = ingestion.Moteurs(lambda n, c: [fiches.Fait(n, l, l, True) for l in c.splitlines() if l.startswith("Fait")], lambda n, c: ([], []),
                      lambda t, **_: [vecteur_de(x) for x in t], lambda i, **_: [],
                      lambda i, b, vec=None, **_: couverture.Reponse(b, couverture.INCONNU, "", (), "", "sans_objet", True, ""))


def projet(prefixe: str):
    D = Path(tempfile.mkdtemp(prefix=prefixe))
    (D / "intrants").mkdir()
    idx = Index(travail.chemins(D)[1]) if travail.chemins(D)[1].parent.mkdir(parents=True, exist_ok=True) is None else None
    ingestion.traiter_document(idx, "a.md", document("A", "Fait : le serveur NordTMS expose une base SQL sans journal d'audit"), M)
    idx.ajouter_entite("NordTMS", "NordTMS", "systeme", ["a.md"])
    idx.base.commit()
    a1 = idx.base.execute("SELECT id FROM elements WHERE doc = 'a.md' AND genre = 'fait'").fetchone()[0]

    def tableau(fichier, lignes):
        titre, cols = lots.ENTETES[fichier]
        (D / fichier).write_text(NL.join([titre, "", "| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"] + lignes) + NL,
                                 encoding="utf-8")
    tableau("01-actifs.md", [f"| A01 | NordTMS | Logiciel / Service | ERP de transport | Critique | [E{a1}] |"])
    tableau("03-menaces.md", [f"| M001 | A01 — NordTMS | STRIDE-T | Altération des tournées par un accès SQL non contrôlé [E{a1}] | — | STRIDE-T |"])
    tableau("04-evaluation.md", [f"| M001 | A01 — NordTMS (STRIDE-T) Altération [E{a1}] | Moyen | Élevé | Élevé | Base sans journal [E{a1}] |"])
    tableau("05-traitement.md", [f"| M001 | A01 — NordTMS (STRIDE-T) niveau Élevé | Réduire | Journaliser les accès [E{a1}] | ANSSI-HYGIENE-3 | Moyen |"])
    (D / "02-methodes.md").write_text("# Méthodes\n\nSTRIDE.\n", encoding="utf-8")
    registre.ecrire_registre_et_validation(D)
    delta.ecrire_baseline(D, idx, signature="s0")
    return D, idx, a1


# ===================================================================================================================================
# A. coupure après la création de l'actif : la reprise complète sans doublon
# ===================================================================================================================================
D, idx, a1 = projet("e21-maj-coupure-")
ingestion.traiter_document(idx, "c.md", document("C", "Fait : la plateforme Yooz dématérialise les factures fournisseurs",
                                                 "Fait : Yooz est hébergée chez l'éditeur en mode SaaS"), M)
idx.ajouter_entite("Yooz", "Yooz", "systeme", ["c.md"])
idx.base.commit()
c1 = idx.base.execute("SELECT id FROM elements WHERE doc = 'c.md' AND genre = 'fait' ORDER BY id").fetchone()[0]
etat = {"coupure": True}


def generer(consigne, schema):
    if schema is miseajour.SCHEMA_ACTIFS:
        return {"actifs": [{"candidat": "Yooz", "est_actif": True, "type": "Logiciel / Service", "sensibilite": "Sensible",
                            "description": f"Plateforme de dématérialisation des factures [E{c1}]", "preuves": [c1]}]}
    if schema is miseajour.SCHEMA_REVISION:
        return {"changement": False}
    if schema is miseajour.SCHEMA_MENACES:
        if etat["coupure"]:
            raise RuntimeError("Ollama ne répond plus")
        return {"menaces": [{"categorie": "STRIDE-S", "description": f"Usurpation d'un compte fournisseur [E{c1}]", "cve": "—", "preuves": [c1]}]}
    if schema is miseajour.SCHEMA_EVALUATION:
        return {"evaluations": [{"id": i, "probabilite": "Moyen", "impact": "Moyen", "justification": f"SaaS [E{c1}]"}
                                for i in re.findall(r"^- (M\d+) \|", consigne, re.M)]}
    if schema is miseajour.SCHEMA_TRAITEMENT:
        return {"traitements": [{"id": i, "traitement": "Réduire", "contre_mesures": "MFA", "sources": ["ISO27002-5.15"], "residuel": "Faible"}
                                for i in re.findall(r"^- (M\d+) \|", consigne, re.M)]}
    return {}


parametres = dict(preuves=lambda r, b=0: "(preuves)", termes=lambda t, b: [], assainir=lambda t: (t, 0),
                  sources="STRIDE-S, STRIDE-T, ISO27002-5.15, ANSSI-HYGIENE-3", base_texte="", journal=lambda *_: None, avec_lecture=False)
try:
    miseajour.executer(D, index=idx, generer=generer, **parametres)
    interrompu = False
except RuntimeError:
    interrompu = True
actifs = (D / "01-actifs.md").read_text(encoding="utf-8")
verifier("coupure : l'actif créé est écrit, les menaces non", interrompu and "| A02 | Yooz |" in actifs
         and "A02 — Yooz" not in (D / "03-menaces.md").read_text(encoding="utf-8"))
verifier("coupure : l'état appliqué n'a PAS avancé (la mise à jour sera reprise)", "c.md" not in delta.lire_baseline(D)["documents"])
verifier("coupure : l'actif à compléter est noté", "A02" in miseajour._lire_en_cours(D))
verifier("coupure : le livrable n'est jamais laissé à moitié écrit (aucun fichier temporaire)", not list(D.glob("*.tmp")))
etat["coupure"] = False
r = miseajour.executer(D, index=idx, generer=generer, **parametres)
actifs = (D / "01-actifs.md").read_text(encoding="utf-8")
verifier("reprise : un seul actif Yooz (pas de doublon), menaces établies pour A02",
         r["statut"] == "ok" and actifs.count("| Yooz |") == 1 and "A02 — Yooz" in (D / "03-menaces.md").read_text(encoding="utf-8"))
verifier("reprise : évaluation et traitement complétés", "| M002 |" in (D / "04-evaluation.md").read_text(encoding="utf-8")
         and "| M002 |" in (D / "05-traitement.md").read_text(encoding="utf-8"))
verifier("reprise : état appliqué avancé, plus rien à faire, marqueur effacé", miseajour.plan_vide(miseajour.preparer_plan(D, idx))
         and miseajour._lire_en_cours(D) == [])
verifier("reprise : la ligne M001 d'origine est restée identique", "| M001 | A01 — NordTMS | STRIDE-T |" in (D / "03-menaces.md").read_text(encoding="utf-8"))

# ===================================================================================================================================
# B. décision enregistrée AVANT le suivi (sans empreinte) : une ligne modifiée par la mise à jour revient « à confirmer »
# ===================================================================================================================================
D, idx, a1 = projet("e21-maj-ancienne-decision-")
lib.DOSSIER_ANALYSES = D.parent
points = validations.construire(D)
risque = next(p for p in points if p["type"] == "risque")
validations.enregistrer(D, "Marie", {risque["id"]: {"decision": "accepte", "commentaire": ""}}, points)
# on simule une décision d'une version antérieure : pas d'empreinte
donnees = json.loads((D / "validations.json").read_text(encoding="utf-8"))
for d in donnees["decisions"].values():
    d.pop("contenu", None)
(D / "validations.json").write_text(json.dumps(donnees), encoding="utf-8")
# le document change : le fait cité par M001 est remplacé
ingestion.traiter_document(idx, "a.md", document("A", "Fait : le serveur NordTMS expose une base SQL avec journal d'audit désormais activé"), M)
idx.base.commit()
nouveau = idx.base.execute("SELECT id FROM elements WHERE doc = 'a.md' AND genre = 'fait'").fetchone()[0]


def generer_b(consigne, schema):
    if schema is propagation.SCHEMA:
        original = re.search(r"LIGNE \(numéro 1\) :\n1\. (.*)\n", consigne).group(1)
        return {"lignes": [{"numero": 1, "nouvelle": original.replace("non contrôlé", "journalisé").replace(f"[E{a1}]", f"[E{nouveau}]")}]}
    if schema is miseajour.SCHEMA_REVISION:
        return {"changement": False}
    if schema is miseajour.SCHEMA_EVALUATION:
        return {"evaluations": [{"id": i, "probabilite": "Faible", "impact": "Moyen", "justification": f"Journal activé [E{nouveau}]"}
                                for i in re.findall(r"^- (M\d+) \|", consigne, re.M)]}
    if schema is miseajour.SCHEMA_TRAITEMENT:
        return {"traitements": [{"id": i, "traitement": "Accepter", "contre_mesures": "Aucune", "sources": ["ANSSI-HYGIENE-3"], "residuel": "Faible"}
                                for i in re.findall(r"^- (M\d+) \|", consigne, re.M)]}
    return {}


r = miseajour.executer(D, index=idx, generer=generer_b, **parametres)
verifier("décision ancienne : la mise à jour a modifié M001", r["statut"] == "ok" and "journalisé" in (D / "03-menaces.md").read_text(encoding="utf-8"))
points = validations.construire(D)
risque = next(p for p in points if p["type"] == "risque")
verifier("décision ancienne : adoptée AVANT la modification, donc la ligne modifiée revient « à confirmer »",
         risque.get("a_confirmer") and risque["decision"] == "")
_c, lignes = lib.lire_registre(D)
verifier("décision ancienne : le registre dit « à confirmer »", lignes[0]["Statut"] == registre.STATUT_A_CONFIRMER)

print("MAJ-REPRISE:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
