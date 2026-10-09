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

print("RESULTAT", "OK" if not ECHECS else f"{len(ECHECS)} ÉCHEC(S)")
sys.exit(1 if ECHECS else 0)
