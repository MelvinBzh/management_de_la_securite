#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de la mise à jour incrémentale des livrables (`web/miseajour.py`) — aucun modèle, aucun réseau.

Un petit projet complet (index des preuves, livrables 01 à 05, registre, décisions de l'analyste) est mis à jour après
l'ajout d'un document, la modification d'un autre, puis le retrait d'un troisième. On vérifie CE QUI CHANGE et surtout ce qui
ne change pas : les lignes inchangées restent identiques à l'octet près, les numéros ne sont jamais réutilisés, les décisions
de l'analyste sur une ligne modifiée reviennent « à confirmer ».
"""
from __future__ import annotations

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


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


NL = chr(10)


def document(sujet: str, *lignes: str) -> str:
    return f"# {sujet}\n\n" + "\n".join(lignes) + "\n" + ("Texte de remplissage sans importance pour le test. " * 8) + "\n"


def vecteur_de(texte: str) -> list[float]:
    v = [0.0] * 64
    for mot in texte.lower().replace(":", " ").replace(".", " ").split():
        v[zlib.crc32(mot.encode()) % 64] += 1.0
    return v


def moteurs():
    def faits(nom, contenu):
        return [fiches.Fait(nom, l, l, True) for l in contenu.splitlines() if l.startswith("Fait")]
    return ingestion.Moteurs(faits, lambda n, c: ([], []), lambda t, **_: [vecteur_de(x) for x in t],
                             lambda index, **_: [], lambda index, besoin, vec=None, **_: couverture.Reponse(
                                 besoin, couverture.INCONNU, "", (), "", "sans_objet", True, ""))


D = Path(tempfile.mkdtemp(prefix="e21-maj-"))
(D / "intrants").mkdir()
chemin_index = travail.chemins(D)[1]
chemin_index.parent.mkdir(parents=True, exist_ok=True)
idx = Index(chemin_index)
M = moteurs()


def eid(doc: str, fragment: str) -> int:
    return idx.base.execute("SELECT id FROM elements WHERE doc = ? AND genre = 'fait' AND extrait LIKE ?", (doc, f"%{fragment}%")).fetchone()[0]


ingestion.traiter_document(idx, "a.md", document("A", "Fait : le serveur NordTMS est hébergé à Lesquin"), M)
ingestion.traiter_document(idx, "b.md", document("B", "Fait : le parc compte 126 portables Dell non chiffrés"), M)
idx.ajouter_entite("NordTMS", "NordTMS", "systeme", ["a.md"])
idx.ajouter_entite("Portables Dell", "Portables Dell", "materiel", ["b.md"])
idx.base.commit()
a1, b1 = eid("a.md", "NordTMS"), eid("b.md", "126 portables")

# --- livrables 01 à 05 (comme après une première analyse) -----------------------------------------------------------------------------
def tableau(fichier: str, lignes: list[str]) -> None:
    titre, colonnes = lots.ENTETES[fichier]
    (D / fichier).write_text(NL.join([titre, "", "| " + " | ".join(colonnes) + " |", "|" + "|".join("---" for _ in colonnes) + "|"] + lignes) + NL,
                             encoding="utf-8")


tableau("01-actifs.md", [f"| A01 | NordTMS | Logiciel / Service | ERP de transport hébergé à Lesquin | Critique | [E{a1}] |",
                         f"| A02 | Portables Dell | Matériel | Parc de 126 portables non chiffrés | Interne | [E{b1}] |"])
tableau("03-menaces.md", [f"| M001 | A01 — NordTMS | STRIDE-T | Altération des tournées par un accès SQL non contrôlé [E{a1}] | — | STRIDE-T |",
                          f"| M002 | A02 — Portables Dell | STRIDE-I | Vol d'un des 126 portables non chiffrés [E{b1}] | — | STRIDE-I |"])
tableau("04-evaluation.md", [f"| M001 | A01 — NordTMS (STRIDE-T) Altération des tournées [E{a1}] | Moyen | Élevé | Élevé | Accès SQL sans journal [E{a1}] |",
                             f"| M002 | A02 — Portables Dell (STRIDE-I) Vol d'un portable [E{b1}] | Moyen | Moyen | Moyen | Portables non chiffrés [E{b1}] |"])
tableau("05-traitement.md", [f"| M001 | A01 — NordTMS (STRIDE-T) niveau Élevé | Réduire | Journaliser les accès SQL [E{a1}] | ANSSI-HYGIENE-3 | Moyen |",
                             f"| M002 | A02 — Portables Dell (STRIDE-I) niveau Moyen | Réduire | Chiffrer les disques [E{b1}] | ISO27002-8.13 | Faible |"])
(D / "02-methodes.md").write_text("# Méthodes\n\nGrille STRIDE et LINDDUN.\n", encoding="utf-8")
registre.ecrire_registre_et_validation(D)
# décisions de l'analyste sur M001 et M002 (enregistrées comme le fait le site)
lib.DOSSIER_ANALYSES = D.parent
points = validations.construire(D)
risque = {p["titre"].split(" — ")[0]: p for p in points if p["type"] == "risque"}
validations.enregistrer(D, "Marie", {risque["M001"]["id"]: {"decision": "accepte", "commentaire": ""},
                                     risque["M002"]["id"]: {"decision": "accepte", "commentaire": ""}}, points)
DESCRIPTION = NL.join(["# Description du système", "", "ERP de transport NordTMS hébergé à Lesquin ; parc de portables Dell."]) + NL
(D / "00-description.md").write_text(DESCRIPTION, encoding="utf-8")
delta.ecrire_baseline(D, idx, signature="s0")
avant = {f: (D / f).read_text(encoding="utf-8") for f in ("01-actifs.md", "03-menaces.md", "04-evaluation.md", "05-traitement.md")}
ligne = lambda fichier, ident, source=None: next(l for l in (source or {fichier: (D / fichier).read_text(encoding="utf-8")})[fichier].splitlines()  # noqa: E731
                                                  if l.startswith(f"| {ident} |"))

# --- écriture sûre ----------------------------------------------------------------------------------------------------------------------
tmp = Path(tempfile.mkdtemp(prefix="e21-maj-ecr-"))
(tmp / "03-menaces.md").write_text(avant["03-menaces.md"], encoding="utf-8")
miseajour.ecrire_lignes(tmp, "03-menaces.md", [["M003", "A09 — X", "STRIDE-S", "d", "—", "STRIDE-S"]])
res = (tmp / "03-menaces.md").read_text(encoding="utf-8")
verifier("ligne ajoutée à la fin du tableau, les autres identiques à l'octet près",
         all(l in res for l in avant["03-menaces.md"].splitlines() if l.startswith("| M00")) and "| M003 | A09 — X |" in res)
ids = miseajour.reserver_ids(tmp, "M", ["M001", "M002", "M003"], 2)
verifier("identifiants réservés à la suite, jamais réutilisés", ids == ["M004", "M005"]
         and miseajour.reserver_ids(tmp, "M", ["M001"], 1) == ["M006"])

# --- les documents changent -----------------------------------------------------------------------------------------------------------
ingestion.traiter_document(idx, "b.md", document("B", "Fait : le parc compte 132 portables Dell non chiffrés"), M)
ingestion.traiter_document(idx, "c.md", document("C", "Fait : la plateforme Yooz dématérialise les factures fournisseurs",
                                                 "Fait : Yooz est hébergée chez l'éditeur en mode SaaS"), M)
idx.ajouter_entite("Yooz", "Yooz", "systeme", ["c.md"])
idx.base.commit()
b1_nouveau, c1, c2 = eid("b.md", "132 portables"), eid("c.md", "plateforme Yooz"), eid("c.md", "hébergée")

plan = miseajour.preparer_plan(D, idx)
par_id = {i["id"]: i for i in plan["items"]}
verifier("plan : création de l'actif Yooz proposée et cochée", "creer:yooz" in par_id and par_id["creer:yooz"]["coche"])
verifier("plan : A02 révisé (le parc passe de 126 à 132)", "reviser:A02" in par_id and "126" in par_id["reviser:A02"]["raison"])
verifier("plan : les lignes citant l'ancienne preuve sont à revoir (01 et 03), pas celles de NordTMS",
         "revoir:03-menaces.md:M002" in par_id and "revoir:01-actifs.md:A02" in par_id and not any("M001" in k or "A01" in k for k in par_id))
verifier("plan : aucun retrait n'est coché (jamais automatique)", not any(i["type"] == "retirer_actif" and i["coche"] for i in plan["items"]))
verifier("plan : état visible (documents ajoutés/modifiés)", plan["documents"]["ajoutes"] == ["c.md"] and plan["documents"]["modifies"] == ["b.md"])


def generer(consigne: str, schema: dict) -> dict:
    if schema is miseajour.SCHEMA_ACTIFS:
        return {"actifs": [{"candidat": "Yooz", "est_actif": True, "type": "Logiciel / Service", "sensibilite": "Sensible",
                            "description": f"Plateforme de dématérialisation des factures fournisseurs, hébergée chez l'éditeur [E{c1}] [E{c2}]",
                            "preuves": [c1, c2]}]}
    if schema is miseajour.SCHEMA_REVISION:
        return {"changement": True, "description": f"Parc de 132 portables non chiffrés [E{b1_nouveau}]", "sensibilite": "Interne",
                "preuves": [b1_nouveau], "raison": "le parc est passé de 126 à 132"}
    if schema is miseajour.SCHEMA_MENACES:
        if "| A03 |" not in consigne:   # le modèle n'invente pas de menaces Yooz pour un autre actif
            return {"menaces": []}
        return {"menaces": [
            {"categorie": "STRIDE-S", "description": f"Usurpation d'un compte fournisseur pour détourner un paiement [E{c1}]", "cve": "—", "preuves": [c1]},
            {"categorie": "LINDDUN-I", "description": f"Fuite de factures hébergées chez l'éditeur SaaS [E{c2}]", "cve": "—", "preuves": [c2]}]}
    if schema is miseajour.SCHEMA_EVALUATION:
        return {"evaluations": [{"id": i, "probabilite": "Élevé", "impact": "Élevé", "justification": f"Exposition SaaS [E{c2}]"}
                                for i in re.findall(r"^- (M\d+) \|", consigne, re.M)]}
    if schema is miseajour.SCHEMA_TRAITEMENT:
        return {"traitements": [{"id": i, "traitement": "Réduire", "contre_mesures": "MFA et revue des accès", "sources": ["ISO27002-5.15"],
                                 "residuel": "Moyen"} for i in re.findall(r"^- (M\d+) \|", consigne, re.M)]}
    if schema is propagation.SCHEMA:
        original = re.search(r"LIGNE \(numéro 1\) :\n1\. (.*)\n", consigne).group(1)
        return {"lignes": [{"numero": 1, "nouvelle": original.replace("126", "132").replace(f"[E{b1}]", f"[E{b1_nouveau}]")}]}
    return {}


def faux_preuves(requetes, budget=9000):
    return "(preuves du dossier)"


journal = []
r1 = miseajour.executer(D, index=idx, generer=generer, preuves=faux_preuves, termes=lambda t, b: [], assainir=lambda t: (t, 0),
                        sources="STRIDE-S, STRIDE-T, STRIDE-I, LINDDUN-I, ISO27002-5.15, ANSSI-HYGIENE-3", base_texte="",
                        journal=journal.append, avec_lecture=False)
verifier("mise à jour terminée", r1["statut"] == "ok" and r1["risques"] == 4)
res = r1["resultat"]
verifier("un actif créé (A03), une ligne révisée, deux menaces nouvelles évaluées et traitées",
         [c["id"] for c in res["crees"]] == ["A03"] and any(r["id"] == "A02" for r in res["revises"])
         and {"M003", "M004"} <= set(res["evalues"]) and {"M003", "M004"} <= set(res["traites"]))
apres = {f: (D / f).read_text(encoding="utf-8") for f in avant}
for f, ident in (("01-actifs.md", "A01"), ("03-menaces.md", "M001"), ("04-evaluation.md", "M001"), ("05-traitement.md", "M001")):
    verifier(f"{f} : la ligne {ident} (non concernée) est identique à l'octet près", ligne(f, ident, apres) == ligne(f, ident, avant))
verifier("01 : A02 révisée (132) et A03 Yooz créée avec preuves", "132 portables" in ligne("01-actifs.md", "A02", apres)
         and f"[E{c1}]" in ligne("01-actifs.md", "A03", apres) and "| Yooz |" in ligne("01-actifs.md", "A03", apres))
verifier("01 : l'ancienne preuve disparue n'est plus citée", f"[E{b1}]" not in ligne("01-actifs.md", "A02", apres))
verifier("03 : M002 corrigée, M003 et M004 créées pour A03", "132" in ligne("03-menaces.md", "M002", apres)
         and "A03 — Yooz" in ligne("03-menaces.md", "M003", apres) and "A03 — Yooz" in ligne("03-menaces.md", "M004", apres))
verifier("04 : niveau calculé par le programme (Élevé × Élevé = Critique)", "| Critique |" in ligne("04-evaluation.md", "M003", apres))
verifier("05 : traitement des nouveaux risques", "MFA et revue des accès" in ligne("05-traitement.md", "M004", apres))

# --- description : le texte d'origine est conservé, une section « Compléments » est tenue par le code --------------------------------------
desc = (D / "00-description.md").read_text(encoding="utf-8")
verifier("description : texte d'origine conservé tel quel, section « Compléments » ajoutée à la fin",
         desc.startswith(DESCRIPTION.rstrip(NL)) and desc.count(miseajour.TITRE_COMPLEMENT) == 1
         and "A03 — Yooz" in desc and "`c.md`" in desc and "modifié : `b.md`" in desc)
verifier("description : compléments recalculés sans doublon (idempotent)", not miseajour.completer_description(D)
         and (D / "00-description.md").read_text(encoding="utf-8") == desc)

# --- le registre et les décisions -----------------------------------------------------------------------------------------------------
_c, lignes_reg = lib.lire_registre(D)
statuts = {r["ID"]: r["Statut"] for r in lignes_reg}
verifier("registre : 4 risques, M001 inchangé reste « décidé »", len(lignes_reg) == 4 and statuts["M001"] == registre.STATUT_DECIDE)
verifier("registre : M002 modifiée depuis la décision → « à confirmer »", statuts["M002"] == registre.STATUT_A_CONFIRMER)
verifier("registre : les nouveaux risques sont à valider", statuts["M003"] == registre.STATUT_A_VALIDER and statuts["M004"] == registre.STATUT_A_VALIDER)
points = validations.construire(D)
risques = {p["titre"].split(" — ")[0]: p for p in points if p["type"] == "risque"}
verifier("page de validation : M001 reste décidé", risques["M001"]["decision"] == "accepte" and not risques["M001"].get("a_confirmer"))
verifier("page de validation : M002 revient à confirmer, l'ancienne décision reste visible",
         risques["M002"].get("a_confirmer") and risques["M002"]["decision"] == "" and "CHANGÉ" in risques["M002"]["pourquoi"]
         and risques["M002"]["decision_precedente"]["analyste"] == "Marie")
verifier("synthèse : « à confirmer » n'est pas compté comme décidé", "| Risques décidés par un analyste | 1 sur 4 |" in (D / "SYNTHESE.md").read_text(encoding="utf-8"))
verifier("06-validation : les décisions à confirmer sont signalées", "à confirmer" in (D / "06-validation.md").read_text(encoding="utf-8"))

# --- trace lisible, état appliqué, idempotence --------------------------------------------------------------------------------------
rapport = (D / miseajour.NOM_RAPPORT).read_text(encoding="utf-8")
verifier("rapport MISE-A-JOUR.md : créé, révisé, avant → après", "Actifs créés" in rapport and "A03" in rapport and "avant :" in rapport)
verifier("le journal des changements est conservé", (D / miseajour.NOM_JOURNAL).is_file())
verifier("état appliqué mis à jour : plus rien à faire", miseajour.plan_vide(miseajour.preparer_plan(D, idx)))
verifier("relancer ne fait rien", miseajour.executer(D, index=idx, generer=generer, preuves=faux_preuves, termes=lambda t, b: [],
                                                     assainir=lambda t: (t, 0), sources="STRIDE-S", base_texte="",
                                                     journal=lambda *_: None)["statut"] == "rien")

# --- un document retiré : le retrait est PROPOSÉ, jamais automatique ------------------------------------------------------------------
idx.supprimer_document("c.md")
idx.base.execute("DELETE FROM entites WHERE nom = 'Yooz'")
idx.base.commit()
plan2 = miseajour.preparer_plan(D, idx)
retrait = next((i for i in plan2["items"] if i["id"] == "retirer:A03"), None)
verifier("retrait de A03 proposé, case décochée", retrait is not None and not retrait["coche"])
avant2 = {f: (D / f).read_text(encoding="utf-8") for f in avant}
r2 = miseajour.executer(D, index=idx, generer=lambda c, s: {}, preuves=faux_preuves, termes=lambda t, b: [], assainir=lambda t: (t, 0),
                        sources="STRIDE-S", base_texte="", journal=lambda *_: None, avec_lecture=False)
verifier("sans confirmation, l'actif et ses menaces restent (à revoir)", "| A03 |" in (D / "01-actifs.md").read_text(encoding="utf-8")
         and r2["statut"] == "ok" and len(r2["a_revoir"]) >= 1)
# la proposition de retrait PERSISTE (calculée sur l'état des preuves) ; l'analyste la coche
plan3 = miseajour.preparer_plan(D, idx)
verifier("le retrait reste proposé tant qu'il n'est pas réglé", any(i["id"] == "retirer:A03" and not i["coche"] for i in plan3["items"]))
for i in plan3["items"]:
    if i["id"] == "retirer:A03":
        i["coche"] = True
miseajour.ecrire_plan(D, plan3)
r3 = miseajour.executer(D, index=idx, generer=lambda c, s: {}, preuves=faux_preuves, termes=lambda t, b: [], assainir=lambda t: (t, 0),
                        sources="STRIDE-S", base_texte="", journal=lambda *_: None, avec_lecture=False)
verifier("retrait confirmé : l'actif et ses 2 menaces disparaissent des 4 livrables", r3["resultat"]["retires"]
         and r3["resultat"]["retires"][0]["id"] == "A03" and "| A03 |" not in (D / "01-actifs.md").read_text(encoding="utf-8")
         and "| M003 |" not in (D / "03-menaces.md").read_text(encoding="utf-8")
         and "| M004 |" not in (D / "05-traitement.md").read_text(encoding="utf-8"))
desc3 = (D / "00-description.md").read_text(encoding="utf-8")
verifier("description : le retrait confirmé apparaît, l'actif retiré n'est plus listé comme ajouté",
         desc3.count(miseajour.TITRE_COMPLEMENT) == 1 and "Actifs retirés" in desc3 and "A03 — Yooz**, retiré" in desc3
         and "### Actifs ajoutés" not in desc3 and desc3.startswith(DESCRIPTION.rstrip(NL)))
verifier("un identifiant retiré n'est jamais réattribué", miseajour.reserver_ids(D, "A", ["A01", "A02"], 1) == ["A04"]
         and miseajour.reserver_ids(D, "M", ["M001", "M002"], 1) == ["M005"])

# --- ce que le test RÉEL a montré : un plan ne doit pas se noyer dans les défauts antérieurs ------------------------------------------------
# (1) une citation qui ne correspond à aucune preuve depuis avant n'est PAS une conséquence des documents changés : proposée, jamais cochée ;
# (2) un terme générique n'est pas un actif ; un nom déjà inventorié (mots distinctifs dans un actif) n'est pas un nouvel actif ;
# (3) un sujet déjà cité par les documents d'origine sans avoir été retenu reste proposé, mais décoché.
E = Path(tempfile.mkdtemp(prefix="e21-maj-plan-"))
(E / "intrants").mkdir()
chemin_e = travail.chemins(E)[1]
chemin_e.parent.mkdir(parents=True, exist_ok=True)
idx2 = Index(chemin_e)
ingestion.traiter_document(idx2, "x.md", document("X", "Fait : le serveur Alpha est hébergé à Lyon",
                                                  "Fait : les machines tournent sous Hyper-V"), M)
idx2.ajouter_entite("Alpha", "Alpha", "systeme", ["x.md"])
idx2.ajouter_entite("Hyper-V", "Hyper-V", "systeme", ["x.md"])
idx2.base.commit()
alpha = idx2.base.execute("SELECT id FROM elements WHERE doc = 'x.md' AND extrait LIKE '%Alpha%'").fetchone()[0]


def tableau_dans(dossier: Path, fichier: str, lignes: list[str]) -> None:
    titre, colonnes = lots.ENTETES[fichier]
    (dossier / fichier).write_text(NL.join([titre, "", "| " + " | ".join(colonnes) + " |", "|" + "|".join("---" for _ in colonnes) + "|"]
                                           + lignes) + NL, encoding="utf-8")


tableau_dans(E, "01-actifs.md", [f"| A01 | Alpha | Logiciel / Service | Serveur Alpha, accessible par passerelle VPN [E{alpha}] | Critique | [E{alpha}] |",
                                 "| A02 | Legacy | Logiciel / Service | Ancien outil documenté nulle part [E999] | Interne | [E999] |"])
tableau_dans(E, "03-menaces.md", [f"| M001 | A01 — Alpha | STRIDE-S | Usurpation [E{alpha}] | — | STRIDE-S |",
                                  "| M002 | A02 — Legacy | STRIDE-T | Altération [E999] | — | STRIDE-T |"])
tableau_dans(E, "04-evaluation.md", [f"| M001 | A01 Alpha (STRIDE-S) | Moyen | Élevé | Élevé | Exposé [E{alpha}] |",
                                     "| M002 | A02 Legacy (STRIDE-T) | Moyen | Moyen | Moyen | Inconnu [E999] |"])
tableau_dans(E, "05-traitement.md", [f"| M001 | A01 Alpha (STRIDE-S) | Réduire | MFA [E{alpha}] | ISO27002-5.15 | Moyen |",
                                     "| M002 | A02 Legacy (STRIDE-T) | Réduire | Revue [E999] | ISO27002-5.15 | Faible |"])
delta.ecrire_baseline(E, idx2, signature="s0")
ingestion.traiter_document(idx2, "y.md", document("Y", "Fait : le serveur Veeam sauvegarde chaque semaine vers un NAS",
                                                  "Fait : la salle serveurs du siège est partagée avec le prestataire externe",
                                                  "Fait : les machines Hyper-V sont gérées par la passerelle Alpha"), M)
idx2.ajouter_entite("Veeam", "Veeam", "materiel", ["y.md"])
idx2.ajouter_entite("salle serveurs", "salle serveurs", "site", ["y.md"])
idx2.ajouter_entite("prestataire externe", "prestataire externe", "prestataire", ["y.md"])
idx2.ajouter_entite("passerelle Alpha", "passerelle Alpha", "materiel", ["y.md"])
idx2.ajouter_entite("Hyper-V", "Hyper-V", "systeme", ["x.md", "y.md"])  # cité par l'ancien document ET par le nouveau
idx2.base.commit()
plan_e = miseajour.preparer_plan(E, idx2)
ids_e = {i["id"]: i for i in plan_e["items"]}
verifier("plan : un sujet apporté par le seul document ajouté est proposé ET coché (Veeam)",
         "creer:veeam" in ids_e and ids_e["creer:veeam"]["coche"])
verifier("plan : un sujet déjà cité par un ancien document reste proposé mais décoché (Hyper-V)",
         "creer:hyper v" in ids_e and not ids_e["creer:hyper v"]["coche"] and "origine" in ids_e["creer:hyper v"]["raison"])
verifier("plan : un terme générique n'est pas proposé comme actif (salle serveurs, prestataire externe)",
         not any(k in ids_e for k in ("creer:salle serveurs", "creer:prestataire externe"))
         and {"salle serveurs", "prestataire externe"} <= {e["nom"] for e in plan_e["ecartes"]})
verifier("plan : un nom déjà inventorié n'est pas un nouvel actif (passerelle Alpha ⊂ A01)", "creer:passerelle alpha" not in ids_e
         and "passerelle Alpha" not in {e["nom"] for e in plan_e["ecartes"]})
anciennes = [i for i in plan_e["items"] if i["type"] == "revoir_ligne"]
verifier("plan : les lignes qui citent une preuve inexistante depuis avant sont proposées mais JAMAIS cochées",
         {i["cible"] for i in anciennes} == {"A02", "M002"} and all(i["donnees"]["origine"] == "ancienne" and not i["coche"] for i in anciennes))
verifier("plan : aucune ligne de l'actif sain (A01, M001) n'est à revoir", not any(i["cible"] in ("A01", "M001") for i in anciennes))
verifier("plan : un actif dont les citations n'ont jamais existé n'est pas proposé au retrait", not any(i["type"] == "retirer_actif" for i in plan_e["items"]))
# un choix de l'analyste est conservé d'un calcul à l'autre
ids_e["revoir:01-actifs.md:A02"]["coche"] = True
miseajour.ecrire_plan(E, plan_e)
verifier("plan : la case cochée par l'analyste est conservée au recalcul",
         next(i for i in miseajour.preparer_plan(E, idx2)["items"] if i["id"] == "revoir:01-actifs.md:A02")["coche"])

# --- livrables d'une ancienne version (autres colonnes) : mise à jour refusée avec un message clair ------------------------------------
ancien = Path(tempfile.mkdtemp(prefix="e21-maj-ancien-"))
for f in ("01-actifs.md", "03-menaces.md", "04-evaluation.md", "05-traitement.md"):
    (ancien / f).write_text("# x\n\n| ID | Nom | Type | Description | Valeur | Sensibilité | Preuve |\n|---|---|---|---|---|---|---|\n| A1 | a | b | c | d | e | f |\n",
                            encoding="utf-8")
verifier("format ancien reconnu", "colonnes" in miseajour.format_ancien(ancien))
verifier("format actuel : rien à signaler", miseajour.format_ancien(D) == "")

print("MISEAJOUR:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
