#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de la boîte de validation (`web/validations.py`) et de la propagation ciblée sur une ligne."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402
from web import controles, lib, propagation, validations  # noqa: E402

ECHECS: list[str] = []


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


NL = chr(10)
D = Path(tempfile.mkdtemp(prefix="e21-valid-")) / "analyses" / "2026-01-01_x"
D.mkdir(parents=True)
(D / "intrants").mkdir()
w = lambda nom, lignes: (D / nom).write_text(NL.join(lignes) + NL, encoding="utf-8")  # noqa: E731

# --- l'index de connaissance du projet --------------------------------------------------------------------
dossier_c = travail.chemins(D)[0]
dossier_c.mkdir()
idx = Index(travail.chemins(D)[1])
E1 = idx.ajouter_element("fait", "audit.md", "Sauvegardes manuelles", "Les sauvegardes sont lancées à la main chaque vendredi", True)
E2 = idx.ajouter_element("fait", "pssi.md", "MFA", "Le MFA est obligatoire pour les comptes administrateurs", True)
idx.ajouter_contradiction("", "pssi.md", "Comptes désactivés sous 24 h", "audit.md", "Comptes de départs encore actifs", "c", "incompatibles", 1)
idx.ajouter_contradiction("", "a.md", "faible", "b.md", "faible aussi", "c", "peu sûr", 0)
idx.enregistrer_couverture("cont-restau", {"besoin": "cont-restau", "theme": "Continuité", "question": "Dernière restauration réussie ?",
                                           "statut": "inconnu", "reponse": "", "preuves": [], "contestations": [], "manque": "Journal",
                                           "a_valider": True, "pourquoi": "Aucune preuve.", "verification": "sans_objet", "priorite": 3})
idx.enregistrer_couverture("gouv-rssi", {"besoin": "gouv-rssi", "theme": "Gouvernance", "question": "Qui est le RSSI ?", "statut": "connu",
                                         "reponse": "M. X", "preuves": [], "contestations": [], "manque": "", "a_valider": False,
                                         "pourquoi": "", "verification": "soutenu", "priorite": 0})
idx.fermer()

# --- les livrables --------------------------------------------------------------------------------------------
w("03-menaces.md", ["# Menaces", "", "## Frontières", "", "| ID | Menace | Source |", "|---|---|---|",
                    f"| T-01 | Sauvegardes non testées [E{E1}] | STRIDE-D |", "| T-02 | Compte admin partagé | STRIDE-S |"])
w("04-evaluation.md", ["# Évaluation", "", "## Risques", "", "| Risque | Description | Probabilité |", "|---|---|---|",
                       f"| R-01 | Perte de données si les sauvegardes manuelles échouent [E{E1}] | Élevée |",
                       f"| R-02 | Compte admin sans MFA [E{E2}] | Moyenne |"])
w("05-traitement.md", ["# Traitement", "", "| Risque | Mesure |", "|---|---|", f"| R-01 | Automatiser les sauvegardes [E{E1}] |"])
w("registre-risques.md", ["# Registre", "", "| ID | Actif | Menace | Probabilité | valide_par | Date validation |", "|---|---|---|---|---|---|",
                          "| R-01 | Données | Perte de sauvegarde | Élevée | *À valider par l'analyste* | — |",
                          "| R-02 | Comptes | Compte sans MFA | Moyenne | *À valider par l'analyste* | — |"])
w("06-validation.md", ["# Validation"])
w("SYNTHESE.md", ["# Synthèse", "", "| Constat | Preuve |", "|---|---|", f"| Sauvegardes manuelles [E{E1}] | audit |"])

controles.enregistrer(D, 3, "Étape 3 · Menaces", "gemma4:12b", "non_conforme", "composants inventés", None, "x",
                      humaine=controles.pourquoi_et_quoi("reste_non_conforme", "composants inventés", ["03-menaces.md"]))
controles.enregistrer(D, 4, "Étape 4 · Évaluation", "gemma4:12b", "conforme", "", None, "x",
                      doutes=[f"[non soutenue] | R-01 | Perte de données si les sauvegardes manuelles échouent [E{E1}] | Élevée |",
                              f"[doute] | R-02 | Compte admin sans MFA [E{E2}] | Moyenne |",
                              "[doute] | R-99 | Ligne qui n'existe plus | Faible |"])

# --- construction ----------------------------------------------------------------------------------------------
items = validations.construire(D)
par_type = {t: [i for i in items if i["type"] == t] for t in validations.TYPES}
verifier("2 risques, 1 étape, 2 lignes (la ligne disparue est ignorée), 1 contradiction confirmée, 1 question",
         [len(par_type[t]) for t in ("risque", "etape", "ligne", "contradiction", "question")] == [2, 1, 2, 1, 1])
verifier("identifiants stables d'un appel à l'autre", [i["id"] for i in items] == [i["id"] for i in validations.construire(D)])
ligne1 = next(i for i in par_type["ligne"] if "R-01" in i["ligne"])
verifier("ligne : le contexte donne la section, l'en-tête du tableau et la ligne",
         "Risques" in ligne1["contexte"] and "| Risque | Description | Probabilité |" in ligne1["contexte"] and "R-01" in ligne1["contexte"])
verifier("ligne : la preuve citée est jointe avec son extrait exact", any(p["id"] == E1 and "à la main" in p["extrait"] for p in ligne1["preuves"]))
verifier("ligne non soutenue passe avant la ligne en doute", par_type["ligne"][0]["id"] == ligne1["id"])
verifier("ligne : pourquoi et quoi vérifier renseignés", ligne1["pourquoi"] and "extrait" in ligne1["quoi"])
r1 = next(i for i in par_type["risque"] if i["titre"].startswith("R-01"))
verifier("risque : lignes liées (évaluation, traitement)", "04-evaluation.md" in r1["contexte"] and "05-traitement.md" in r1["contexte"])
verifier("étape : pourquoi/quoi du contrôle et début du livrable en contexte", "composants inventés" in par_type["etape"][0]["contexte"] and "Menaces" in par_type["etape"][0]["contexte"])
verifier("contradiction faible (non confirmée) exclue", all("faible" not in i["contexte"] for i in par_type["contradiction"]))
verifier("question : « non documenté » expliqué, jamais « n'existe pas »", "non documenté" in par_type["question"][0]["titre"] and "pas une preuve" in par_type["question"][0]["pourquoi"])
verifier("le connu sans doute n'est pas proposé", all("RSSI" not in i["titre"] for i in items))
verifier("chaque point propose des choix", all(i["choix"] for i in items))
contra = par_type["contradiction"][0]
verifier("contradiction : les choix nomment les documents et permettent de changer la valeur",
         any("pssi.md" in l for _c, l in contra["choix"]) and any("audit.md" in l for _c, l in contra["choix"]) and any(c == "autre" for c, _l in contra["choix"]))
verifier("avancement : 0 décidé sur 7", validations.resume(items)["decides"] == 0 and validations.resume(items)["total"] == 7)

# --- enregistrement ------------------------------------------------------------------------------------------------
def tente(saisies):
    try:
        validations.enregistrer(D, "Marie", saisies, items)
        return ""
    except ValueError as exc:
        return str(exc)

try:
    validations.enregistrer(D, "  ", {ligne1["id"]: {"decision": "ok"}}, items)
    nom_requis = False
except ValueError as exc:
    nom_requis = "nom est requis" in str(exc)
verifier("sans nom : refusé", nom_requis)
verifier("commentaire obligatoire pour « à corriger »", "commentaire est obligatoire" in tente({ligne1["id"]: {"decision": "corrige", "commentaire": ""}}))
verifier("décision inconnue refusée", "inconnue" in tente({ligne1["id"]: {"decision": "pirate", "commentaire": "x"}}))
verifier("rien de choisi : refusé", "Aucune décision" in tente({ligne1["id"]: {"decision": "", "commentaire": ""}}))

ligne2 = next(i for i in par_type["ligne"] if "R-02" in i["ligne"])
bilan = validations.enregistrer(D, "Marie", {
    ligne1["id"]: {"decision": "corrige", "commentaire": "Les sauvegardes sont maintenant automatisées depuis le 1er octobre"},
    ligne2["id"]: {"decision": "ok", "commentaire": ""},
    r1["id"]: {"decision": "modifie", "commentaire": "Probabilité moyenne : sauvegardes automatisées"},
    par_type["question"][0]["id"]: {"decision": "repondu", "commentaire": "Dernière restauration : 12 septembre 2026"},
}, items)
verifier("4 décisions enregistrées", bilan["enregistres"] == 4)
apres = {i["id"]: i for i in validations.construire(D)}
verifier("les décisions reviennent à la reconstruction", apres[ligne1["id"]]["decision"] == "corrige" and apres[ligne2["id"]]["decision"] == "ok"
         and apres[ligne1["id"]]["analyste"] == "Marie")
verifier("le risque décidé est écrit dans le registre (valide_par)", "Marie" in (D / "registre-risques.md").read_text(encoding="utf-8"))
verifier("avancement : 4 décidés", validations.resume(list(apres.values()))["decides"] == 4)
attente = propagation.en_attente(D)
verifier("une ligne à corriger et un risque modifié sont en attente de propagation",
         sorted(bool(a.get("cible")) for a in attente) == [False, True])

# --- propagation sur une ligne : réécriture contrôlée + impacts en aval ----------------------------------------------------
orig = f"| R-01 | Perte de données si les sauvegardes manuelles échouent [E{E1}] | Élevée |"
def reecrire(consigne):
    if "UNE ligne" in consigne:
        return {"lignes": [{"numero": 1, "nouvelle": f"| R-01 | Perte de données limitée : sauvegardes automatisées (analyste) [E{E1}] | Faible |"}]}
    return {"lignes": []}
index = Index(travail.chemins(D)[1])
traces = propagation.propager(D, reecrire=reecrire, index=index, base="sauvegardes", termes=lambda t, b: [], journal=lambda *_: None)
index.fermer()
eval_apres = (D / "04-evaluation.md").read_text(encoding="utf-8")
verifier("la ligne visée est réécrite, l'autre intacte", "sauvegardes automatisées (analyste)" in eval_apres and "| R-02 | Compte admin sans MFA" in eval_apres)
ligne_trace = next(t for t in traces if t["risque"] == "04-evaluation.md")
verifier("la trace garde l'avant et l'après", ligne_trace["modifiees"][0]["avant"] == orig and "Faible" in ligne_trace["modifiees"][0]["apres"])
v = validations.lire_fichier(D)
aval_fichiers = sorted(a["fichier"] for a in v["aval"])
verifier("impacts en aval créés pour les lignes plus loin qui citent la même preuve (traitement, synthèse)",
         aval_fichiers == ["05-traitement.md", "SYNTHESE.md"])
verifier("jamais d'impact créé en amont de la ligne modifiée", all(a["fichier"] not in ("03-menaces.md", "04-evaluation.md") for a in v["aval"]))
items2 = validations.construire(D)
aval = [i for i in items2 if i["type"] == "aval"]
verifier("les impacts apparaissent dans la boîte de validation avec avant/après", len(aval) == 2 and "avant :" in aval[0]["contexte"] and "après :" in aval[0]["contexte"])
verifier("le point « ligne » corrigé n'est plus à relire (la ligne a changé)", all(i["ligne"] != orig for i in items2 if i["type"] == "ligne"))

# --- retrait d'une ligne, ligne introuvable, réécriture refusée -------------------------------------------------------------------------
cible = next(i for i in aval if i["fichier"] == "05-traitement.md")
validations.enregistrer(D, "Marie", {cible["id"]: {"decision": "corrige", "commentaire": "Retirer : sauvegardes déjà automatisées"}}, items2)
traite = propagation.propager(D, reecrire=lambda c: {"lignes": [{"numero": 1, "nouvelle": "| trop | de | colonnes | ici |"}]},
                              index=None, base="", termes=lambda t, b: [], journal=lambda *_: None)
verifier("réécriture refusée (colonnes) : ligne laissée telle quelle et motif donné",
         "Automatiser les sauvegardes" in (D / "05-traitement.md").read_text(encoding="utf-8") and traite[0]["refusees"] and "colonnes" in traite[0]["refusees"][0]["motif"])
validations.enregistrer(D, "Marie", {cible["id"]: {"decision": "ok", "commentaire": ""}}, items2)

propagation.enregistrer_decision(D, "", "retire", "ligne inutile", "Marie", cible={"fichier": "03-menaces.md", "ligne": "| T-02 | Compte admin partagé | STRIDE-S |", "type": "ligne"})
propagation.enregistrer_decision(D, "", "retire", "déjà fait", "Marie", cible={"fichier": "03-menaces.md", "ligne": "| ligne fantôme | x | y |", "type": "ligne"})
t3 = propagation.propager(D, reecrire=lambda c: {}, index=None, base="", termes=lambda t, b: [], journal=lambda *_: None)
verifier("ligne retirée du livrable", "T-02" not in (D / "03-menaces.md").read_text(encoding="utf-8") and "T-01" in (D / "03-menaces.md").read_text(encoding="utf-8"))
verifier("ligne introuvable : message clair, rien de cassé", any("n'existe plus" in t["message"] for t in t3))
verifier("plus rien en attente après propagation", propagation.en_attente(D) == [])
trace_md = (D / "PROPAGATION.md").read_text(encoding="utf-8")
verifier("PROPAGATION.md décrit les lignes retirées et réécrites", "ligne retirée" in trace_md and "Réécrit" in trace_md)

# --- export lisible ----------------------------------------------------------------------------------------------------------------
md = validations.exporter_markdown(validations.construire(D))
verifier("export : sections par type, état, pourquoi, quoi vérifier, preuves",
         "## Risques du registre" in md and "**État**" in md and "**Quoi vérifier**" in md and "preuve [E" in md)

print("VALIDATIONS:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
