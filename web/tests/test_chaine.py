# -*- coding: utf-8 -*-
"""Tests autonomes du pilote de chaîne (`web/chaine.py`) : `python3 web/tests/test_chaine.py`."""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from web import chaine, lib  # noqa: E402

ECHECS = []


def verifier(nom, condition):
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


def dossier_avec(fichiers):
    d = Path(tempfile.mkdtemp())
    for nom, texte in fichiers.items():
        (d / nom).write_text(texte, encoding="utf-8")
    return d


TABLE = "| ID | a |\n|---|---|\n" + "".join(f"| R-{i} | x |\n" for i in range(1, 7))

verifier("ordre fixe : 7 étapes, e21-analyse-existant en premier", len(chaine.ETAPES) == 7 and chaine.ETAPES[0][0] == "e21-analyse-existant")
verifier("consigne sans guillemet double ni contenu d'intrant", '"' not in chaine.consigne("e21-menaces", "2026-01-01_x", ["03-menaces.md"]))
verifier("étape 6 : valide_par laissé vide", "VIDE" in chaine.consigne("e21-validation-suivi", "d", ["06-validation.md"]))
d = dossier_avec({"03-menaces.md": "# Menaces\n" + TABLE + "x" * 400})
verifier("livrable correct accepté", chaine.livrables_manquants(d, ["03-menaces.md"]) == [])
verifier("livrable absent refusé", chaine.livrables_manquants(d, ["04-evaluation.md"]) == ["04-evaluation.md"])
d = dossier_avec({"03-menaces.md": "# Menaces\n" + "x" * 500})
verifier("tableau sans lignes refusé", chaine.livrables_manquants(d, ["03-menaces.md"]) == ["03-menaces.md"])
d = dossier_avec({"03-menaces.md": "# M\n" + TABLE + "CVE-2026-12345 " + "x" * 400})
verifier("CVE de remplissage refusé", chaine.livrables_manquants(d, ["03-menaces.md"]) == ["03-menaces.md"])
d = dossier_avec({"05-traitement.md": "# T\n" + TABLE + "CVE-2021-44228 " + "x" * 400})
verifier("CVE réel accepté", chaine.livrables_manquants(d, ["05-traitement.md"]) == [])
verifier("source ISO inconnue détectée", chaine.sources_inconnues("ISO27002-8.1") == ["ISO27002-8.1"])
verifier("source ISO connue acceptée", chaine.sources_inconnues("ISO27002-5.15 STRIDE-S") == [])
verifier("ANSSI inventé refusé", chaine.sources_inconnues("ANSSI-INVENTE") == ["ANSSI-INVENTE"])
verifier("ANSSI-HYGIENE numéroté accepté", chaine.sources_inconnues("ANSSI-HYGIENE-3.2") == [])
d = dossier_avec({"05-traitement.md": "# T\n" + TABLE + "ISO27002-8.1 " + "x" * 400})
verifier("livrable à source inconnue refusé", chaine.livrables_manquants(d, ["05-traitement.md"]) == ["05-traitement.md"])
d = dossier_avec({"registre-risques.md": "x", "03-menaces.md": "x"})
retires = chaine.purger_hors_etape(d, 3, time.time() - 5)
verifier("livrable d'une étape ultérieure écarté", retires == ["registre-risques.md"] and (d / "03-menaces.md").exists())
d = dossier_avec({"registre-risques.md": "| R001 | x |\n| R-02 |\n"})
verifier("registre : R001 et R-02 reconnus", lib.risques_du_registre(d) == ["R001", "R-02"])
d = dossier_avec({"registre-risques.md": "| R-01 |", "06-validation.md": "# v"})
lib.valider_registre(d, "Analyste", ["R-01"])
verifier("validation humaine consignée", "valide_par** : Analyste" in (d / "06-validation.md").read_text(encoding="utf-8"))
for args in (("", ["R-01"]), ("A", ["R-99"])):
    try:
        lib.valider_registre(d, *args)
        verifier("validation invalide refusée", False)
    except ValueError:
        verifier("validation invalide refusée", True)

# --- routage par agent et contrôle bloquant ------------------------------------------------
ins = {"qwen3.5:9b", "granite4:7b-a1b-h", "gemma4:12b", "qwen3:14b", "llama3.1:8b"}
verifier("routage : extraction sur qwen3.5 (granite écarté)", chaine.choisir_modele("e21-analyse-existant", 1, ins, "d") == "ollama/qwen3.5:9b")
verifier("routage : granite n'apparaît plus nulle part", all("granite" not in m for l in chaine.ROUTAGE.values() for m in l) and all("granite" not in m for l in chaine.JUGES.values() for m in l) and "granite" not in chaine.JUGES)
verifier("routage : raisonnement sur qwen3.5", chaine.choisir_modele("e21-menaces", 1, ins, "d") == "ollama/qwen3.5:9b")
verifier("routage : la 2e tentative change de modèle", chaine.choisir_modele("e21-analyse-existant", 2, ins, "d") == "ollama/qwen3:14b")
verifier("routage : repli si le modèle manque", chaine.choisir_modele("e21-menaces", 1, {"qwen3:14b"}, "d") == "ollama/qwen3:14b")
verifier("routage : jamais un modèle à 4/6 d'outils pour écrire", all(m not in ("llama3.1:8b", "mistral:7b", "gemma4:12b", "qwen3-vl:8b") for l in chaine.ROUTAGE.values() for m in l))
verifier("juge : autre famille que le producteur (qwen -> gemma)", chaine.choisir_juge("ollama/qwen3.5:9b", ins, "d") == "ollama/gemma4:12b")
verifier("juge : gemma relu par qwen", chaine.choisir_juge("ollama/gemma4:12b", ins, "d") == "ollama/qwen3.5:9b")
verifier("juge : défaut si aucune autre famille", chaine.choisir_juge("ollama/qwen3.5:9b", {"qwen3.5:9b"}, "d") == "d")
verifier("verdict CONFORME lu", chaine.analyser_verdict("txt\nRESULTAT-CONTROLE: CONFORME") == (True, ""))
conforme, corr = chaine.analyser_verdict("a\nRESULTAT-CONTROLE: NON CONFORME\n1. CVE inventé")
verifier("verdict NON CONFORME + corrections lus", conforme is False and "CVE inventé" in corr)
verifier("verdict illisible = None (jamais « indéterminé » affiché)", chaine.analyser_verdict("rien") == (None, ""))
verifier("le premier verdict prime sur une citation ultérieure", chaine.analyser_verdict("RESULTAT-CONTROLE: CONFORME"+chr(10)+"RESULTAT-CONTROLE: NON CONFORME")[0] is True)
verifier("l'écho de la consigne ne déclenche aucun verdict", chaine.analyser_verdict(chaine.consigne_controle("d", 3, ["03-menaces.md"]))[0] is None)
verifier("le juge reçoit le livrable AVANT les intrants", chaine.pieces_controle(dossier_avec({"SYNTHESE.md": "x" * 20000}), ["SYNTHESE.md"])[0].endswith("SYNTHESE.md"))
verifier("M01 reconnu comme identifiant de risque", lib.risques_du_registre(dossier_avec({"registre-risques.md": "| M01 | x | M13 | R-02 |"})) == ["M01", "M13", "R-02"])
verifier("verdict en gras reconnu", chaine.analyser_verdict("**RESULTAT-CONTROLE: CONFORME**")[0] is True)
verifier("diagnostic : source inexistante nommée", "ISO27002-8.1" in chaine.diagnostiquer(dossier_avec({"05-traitement.md": "# T\n" + TABLE + "ISO27002-8.1 " + "x" * 400}), ["05-traitement.md"]))
verifier("consigne : liste des sources autorisées", "ISO27002-5.15" in chaine.consigne("e21-menaces", "d", ["03-menaces.md"]))
verifier("consigne de contrôle : lecture seule", "AUCUN fichier" in chaine.consigne_controle("d", 3, ["03-menaces.md"]))

# --- ancrage dans les informations d'origine ----------------------------------------------------
base = "le site php sur hebergement mutualise ; fibrepay paie ; back-office admin ; ssh"
verifier("nginx absent des intrants détecté", "nginx" in chaine.termes_non_fondes("Le serveur nginx héberge le site.", base))
verifier("terme présent dans les intrants accepté", chaine.termes_non_fondes("Le site PHP utilise SSH.", base) == [])
verifier("sigle usuel (HTTPS) toléré", chaine.termes_non_fondes("Flux HTTPS vers l'API.", base) == [])
verifier("terme surveillé (DPO) détecté", "dpo" in [x.lower() for x in chaine.termes_non_fondes("Le DPO valide.", base)])
verifier("sigle légitime hors liste (CNIL) non signalé", chaine.termes_non_fondes("La CNIL contrôle.", base) == [])
d = dossier_avec({"01-actifs.md": "# A\nLe CTO administre nginx."})
(d / "intrants").mkdir()
(d / "intrants" / "a.md.md").write_text("Site PHP, FibrePay, back-office admin.", encoding="utf-8")
verifier("faits inventés remontés pour un fichier de faits", "nginx" in chaine.faits_non_fondes(d, ["01-actifs.md"]))
verifier("les recommandations (étape 5) ne sont pas contrôlées", chaine.faits_non_fondes(d, ["05-traitement.md"]) == "")
verifier("relecture : consigne en lecture seule et sans exécution", "AUCUN outil" in chaine.consigne_relecture("d"))

d = dossier_avec({"00-description.md": "x", "SYNTHESE.md": "y", "RAPPORT-CONTROLE.md": "z", "questions-auto.md": "q"})
archive = chaine.archiver_precedent(d)
verifier("run précédent archivé (non détruit)", archive is not None and (archive / "SYNTHESE.md").read_text() == "y")
verifier("les livrables ne sont plus à la racine (pas de faux succès)", not (d / "00-description.md").exists() and (d / "questions-auto.md").exists())
verifier("rien à archiver : pas de dossier vide créé", chaine.archiver_precedent(dossier_avec({"questions-auto.md": "q"})) is None)

# --- validation humaine risque par risque ----------------------------------------------------
REG = ("# Registre" + chr(10) + chr(10) + "| ID | Actif | Menace | `valide_par` | Date validation |" + chr(10)
       + "|----|---|---|---|---|" + chr(10) + "| M01 | Site | Spoofing | *À valider par l'analyste* | — |" + chr(10)
       + "| M02 | Base | Fuite | *À valider par l'analyste* | — |" + chr(10))
d = dossier_avec({"registre-risques.md": REG, "06-validation.md": "# v" + chr(10)})
colonnes, risques = lib.lire_registre(d)
verifier("registre lu : 2 risques, colonnes nommées", len(risques) == 2 and risques[0]["Actif"] == "Site" and "ID" in colonnes)
bilan = lib.enregistrer_decisions(d, "Mélanie", {"M01": {"decision": "accepte", "commentaire": ""}, "M02": {"decision": "refuse", "commentaire": "hors périmètre | test"}})
registre = (d / "registre-risques.md").read_text(encoding="utf-8")
verifier("valide_par renseigné pour M01 dans le registre", "Mélanie · accepté" in registre)
verifier("refus consigné avec son motif (sans casser le tableau)", "REFUSÉ" in registre and "hors périmètre / test" in registre)
verifier("décisions tracées dans 06-validation.md", "Refusé" in (d / "06-validation.md").read_text(encoding="utf-8"))
verifier("bilan des décisions", bilan["acceptes"] == 1 and bilan["refuses"] == 1 and bilan["en_attente"] == 0)
verifier("le tableau reste lisible après édition", len(lib.lire_registre(d)[1]) == 2)
for mauvais in (("", {"M01": {"decision": "accepte"}}), ("A", {}), ("A", {"M99": {"decision": "accepte"}}), ("A", {"M01": {"decision": "peut-etre"}})):
    try:
        lib.enregistrer_decisions(d, *mauvais)
        verifier("décision invalide refusée", False)
    except ValueError:
        verifier("décision invalide refusée", True)
verifier("commande : dossier réel affiché (pas la date du jour)", "analyses/2026-01-01_x" in lib.construire_commande("x", "2026-01-01_x"))

# --- pièces jointes : tous les intrants d'un gros cas (22 documents ≈ 40 Ko) ----------------------
d = dossier_avec({})
(d / "intrants").mkdir()
for i in range(22):
    (d / "intrants" / f"doc{i:02}.md.md").write_text("x" * 1800, encoding="utf-8")
verifier("22 documents de 1,8 Ko tous joints", len(chaine.pieces_jointes(d)) == 22 and chaine.pieces_omises(d) == [])
(d / "intrants" / "gros.md.md").write_text("y" * 30000, encoding="utf-8")
verifier("un document hors budget est signalé, pas ignoré en silence", chaine.pieces_omises(d) == ["gros.md.md"])
(d / "01-actifs.md").write_text("# A" + "z" * 600, encoding="utf-8")
verifier("les livrables précédents passent avant les intrants", chaine.pieces_jointes(d)[0].endswith("01-actifs.md"))

# --- boucle de verdict : trois contrôleurs jusqu'à un verdict lisible ------------------------------------
verifier("3 contrôleurs : gemma, qwen, gemma", chaine.juges_en_alternance("ollama/qwen3.5:9b", ins, "d") == ["ollama/gemma4:12b", "ollama/qwen3.5:9b", "ollama/gemma4:12b"])
appels = []
def faux_controleur(reponses):
    suite = iter(reponses)
    def lancer(modele, texte, pieces):
        appels.append((modele, texte))
        return next(suite)
    return lancer
appels.clear()
r = chaine.obtenir_verdict(faux_controleur(["blabla", "RESULTAT-CONTROLE: CONFORME"]), ["a", "b", "a"], "C", [])
verifier("verdict illisible puis lisible : le 2e contrôleur tranche", r == (True, "", "b") and len(appels) == 2)
appels.clear()
r = chaine.obtenir_verdict(faux_controleur(["x", "y", "z"]), ["a", "b", "a"], "C", [])
verifier("trois réponses illisibles : None, 3 essais, rappel de format au 3e", r == (None, "", "a") and len(appels) == 3 and "RAPPEL" in appels[2][1] and "RAPPEL" not in appels[0][1])
appels.clear()
r = chaine.obtenir_verdict(faux_controleur(["RESULTAT-CONTROLE: NON CONFORME" + chr(10) + "1. nginx inventé"]), ["a", "b", "a"], "C", [])
verifier("non conforme lisible : corrections gardées, un seul appel", r[0] is False and "nginx" in r[1] and len(appels) == 1)

# --- rapports de contrôle numérotés par version -------------------------------------------------
from web import controles  # noqa: E402
d = dossier_avec({})
v1 = "# Menaces" + chr(10) + "Le serveur nginx héberge le site." + chr(10) + "Spoofing du back-office." + chr(10)
v2 = "# Menaces" + chr(10) + "Le site est hébergé sur un mutualisé." + chr(10) + "Spoofing du back-office." + chr(10)
e1 = controles.enregistrer(d, 3, "Étape 3 · Menaces", "gemma4:12b", "non_conforme", "nginx absent des intrants", None, v1)
e2 = controles.enregistrer(d, 3, "Étape 3 · Menaces", "gemma4:12b", "conforme", "", v1, v2)
verifier("contrôles numérotés 1 puis 2", (e1["numero"], e2["numero"]) == (1, 2))
verifier("versions de l'étape 1 puis 2", (e1["version"], e2["version"]) == (1, 2))
verifier("première version annoncée comme telle", "Première version" in e1["changements"])
verifier("ce qui a changé : ligne retirée et ajoutée", "Retiré : Le serveur nginx" in e2["changements"] and "Ajouté : Le site est hébergé" in e2["changements"])
rapport = (d / "RAPPORT-CONTROLE.md").read_text(encoding="utf-8")
verifier("rapport lisible : numéro, version, verdict", "Contrôle n°1 — Étape 3 · Menaces, version 1 : NON CONFORME" in rapport and "Contrôle n°2" in rapport and "version 2 : CONFORME" in rapport)
verifier("rapport : ce qui n'allait pas", "nginx absent des intrants" in rapport)
verifier("rien à valider quand la reprise est conforme", controles.a_valider(d) == [])
controles.enregistrer(d, 4, "Étape 4 · Évaluation", "gemma4:12b", "non_conforme", "", None, "x", humaine=controles.pourquoi_et_quoi("illisible", "", ["04-evaluation.md"]))
att = controles.a_valider(d)
verifier("illisible : validation humaine avec pourquoi ET quoi vérifier", len(att) == 1 and "verdict exploitable" in att[0]["humaine"]["pourquoi"] and "04-evaluation.md" in att[0]["humaine"]["quoi"])
texte_rapport = (d / "RAPPORT-CONTROLE.md").read_text(encoding="utf-8")
verifier("le rapport affiche « nécessite une validation humaine », jamais « indéterminé »", "NÉCESSITE UNE VALIDATION HUMAINE" in texte_rapport and "indéterminé" not in texte_rapport.lower())
controles.enregistrer(d, 5, "Étape 5 · Traitement", "gemma4:12b", "non_conforme", "CVE-2099-1 inventé", None, "x")
controles.marquer_humaine(d, 5, *controles.pourquoi_et_quoi("reste_non_conforme", "CVE-2099-1 inventé", ["05-traitement.md"]))
verifier("non conforme après reprises : le pourquoi cite le point signalé", any("CVE-2099-1" in a["humaine"]["pourquoi"] for a in controles.a_valider(d)))
verifier("deux étapes à valider listées", len(controles.a_valider(d)) == 2)
verifier("rapport sans contrôle : message clair", "Aucun contrôle" in controles.rapport_markdown([]))
d2 = dossier_avec({"00-description.md": "x", "controles.json": "[]", "RAPPORT-CONTROLE.md": "z"})
arch = chaine.archiver_precedent(d2)
verifier("un relancement archive aussi le journal des contrôles (numérotation repart de 1)", arch is not None and (arch / "controles.json").is_file() and not (d2 / "controles.json").exists())

# --- mode « dossier de preuves » : les documents ne sont plus relus ---------------------------------
dp = dossier_avec({"01-actifs.md": "# A" + "z" * 600})
(dp / "intrants").mkdir()
(dp / "intrants" / "gros.md.md").write_text("y" * 3000, encoding="utf-8")
(dp / "connaissance").mkdir()
(dp / "connaissance" / "preuves-etape-2.md").write_text("# Dossier de preuves", encoding="utf-8")
pj = chaine.pieces_jointes(dp, dp / "connaissance" / "preuves-etape-2.md")
verifier("preuves : le dossier de preuves remplace les intrants", any(p.endswith("preuves-etape-2.md") for p in pj) and not any("gros.md" in p for p in pj))
verifier("preuves : les livrables précédents restent joints", any(p.endswith("01-actifs.md") for p in pj))
verifier("sans preuves : comportement d'avant (intrants joints)", any("gros.md" in p for p in chaine.pieces_jointes(dp)))
c_p = chaine.consigne("e21-menaces", "d", ["03-menaces.md"], avec_preuves=True)
verifier("consigne preuves : ne pas relire les documents, citer [E…]", "DOSSIER DE PREUVES" in c_p and "[E12]" in c_p and "n'ouvre aucun autre fichier" in c_p and "intrants/ et" not in c_p)
verifier("consigne sans preuves : inchangée", "Lis les intrants" in chaine.consigne("e21-menaces", "d", ["03-menaces.md"]))
verifier("sans Ollama : pas de connaissance, lecture directe", chaine.preparer_connaissance(dp, False) is False)
cc, dd = chaine.controle_citations(dp, ["01-actifs.md"])
verifier("sans index : le contrôle de citations ne bloque jamais", cc == "" and dd == [])

NL_ = chr(10)
# --- une reprise n'est « prête » qu'une fois le livrable réécrit (sinon l'agent est coupé avant de corriger) ---------
import os as _os
dr = dossier_avec({"03-menaces.md": "# M" + NL_ + "| a | b |" + NL_ + "|---|---|" + NL_ + "".join(f"| ligne {i} | detail du composant {i} |" + NL_ for i in range(1, 9)) + "x" * 400})
verifier("reprise : un livrable ancien est valide mais PAS prêt", chaine.livrables_manquants(dr, ["03-menaces.md"]) == [] and not chaine.pret_depuis(dr, ["03-menaces.md"], time.time() + 5))
verifier("reprise : prêt une fois réécrit depuis le début de l'appel", chaine.pret_depuis(dr, ["03-menaces.md"], time.time() - 60))
verifier("livrable absent : jamais prêt", not chaine.pret_depuis(dr, ["04-evaluation.md"], 0))

print("RESULTAT", "OK" if not ECHECS else f"{len(ECHECS)} ÉCHEC(S)")
sys.exit(1 if ECHECS else 0)
