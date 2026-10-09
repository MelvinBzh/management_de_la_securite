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
verifier("routage : extraction sur le modèle rapide", chaine.choisir_modele("e21-analyse-existant", 1, ins, "d") == "ollama/granite4:7b-a1b-h")
verifier("routage : raisonnement sur qwen3.5", chaine.choisir_modele("e21-menaces", 1, ins, "d") == "ollama/qwen3.5:9b")
verifier("routage : la 2e tentative change de modèle", chaine.choisir_modele("e21-analyse-existant", 2, ins, "d") == "ollama/qwen3.5:9b")
verifier("routage : repli si le modèle manque", chaine.choisir_modele("e21-menaces", 1, {"qwen3:14b"}, "d") == "ollama/qwen3:14b")
verifier("routage : jamais un modèle à 4/6 d'outils pour écrire", all(m not in ("llama3.1:8b", "mistral:7b", "gemma4:12b", "qwen3-vl:8b") for l in chaine.ROUTAGE.values() for m in l))
verifier("juge : autre famille que le producteur (qwen -> gemma)", chaine.choisir_juge("ollama/qwen3.5:9b", ins, "d") == "ollama/gemma4:12b")
verifier("juge : granite relu par qwen", chaine.choisir_juge("ollama/granite4:7b-a1b-h", ins, "d") == "ollama/qwen3.5:9b")
verifier("juge : défaut si aucune autre famille", chaine.choisir_juge("ollama/qwen3.5:9b", {"qwen3.5:9b"}, "d") == "d")
verifier("verdict CONFORME lu", chaine.analyser_verdict("txt\nRESULTAT-CONTROLE: CONFORME") == (True, ""))
conforme, corr = chaine.analyser_verdict("a\nRESULTAT-CONTROLE: NON CONFORME\n1. CVE inventé")
verifier("verdict NON CONFORME + corrections lus", conforme is False and "CVE inventé" in corr)
verifier("verdict illisible = indéterminé", chaine.analyser_verdict("rien") == (None, ""))
verifier("le premier verdict prime sur une citation ultérieure", chaine.analyser_verdict("RESULTAT-CONTROLE: CONFORME"+chr(10)+"RESULTAT-CONTROLE: NON CONFORME")[0] is True)
verifier("l'écho de la consigne ne déclenche aucun verdict", chaine.analyser_verdict(chaine.consigne_controle("d", 3, ["03-menaces.md"]))[0] is None)
verifier("le juge reçoit le livrable AVANT les intrants", chaine.pieces_controle(dossier_avec({"SYNTHESE.md": "x" * 20000}), ["SYNTHESE.md"])[0].endswith("SYNTHESE.md"))
verifier("M01 reconnu comme identifiant de risque", lib.risques_du_registre(dossier_avec({"registre-risques.md": "| M01 | x | M13 | R-02 |"})) == ["M01", "M13", "R-02"])
verifier("verdict en gras reconnu", chaine.analyser_verdict("**RESULTAT-CONTROLE: CONFORME**")[0] is True)
verifier("diagnostic : source inexistante nommée", "ISO27002-8.1" in chaine.diagnostiquer(dossier_avec({"05-traitement.md": "# T\n" + TABLE + "ISO27002-8.1 " + "x" * 400}), ["05-traitement.md"]))
verifier("consigne : liste des sources autorisées", "ISO27002-5.15" in chaine.consigne("e21-menaces", "d", ["03-menaces.md"]))
verifier("consigne de contrôle : lecture seule", "AUCUN fichier" in chaine.consigne_controle("d", 3, ["03-menaces.md"]))

print("RESULTAT", "OK" if not ECHECS else f"{len(ECHECS)} ÉCHEC(S)")
sys.exit(1 if ECHECS else 0)
