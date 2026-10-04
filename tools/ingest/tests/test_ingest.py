#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de l'ingestion documentaire E21 (T-ING-01 → T-ING-10).

Exécution sans dépendance externe :
    python3 tools/ingest/tests/test_ingest.py
Compatible pytest (si lancé avec `pytest tools/ingest/tests/test_ingest.py`) :
les fonctions `test_*` sont alors collectées, et les SKIP passent par pytest.skip.

Statuts : PASS · FAIL · SKIP (OCR absent). Sortie 0 si aucun FAIL.
"""
from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
DOSSIER_FIXTURES = Path(__file__).resolve().parent / "fixtures"
for chemin in (str(RACINE), str(DOSSIER_FIXTURES)):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

import gen_fixtures  # noqa: E402  (générateur de fixtures local)
from tools.ingest import parse_file  # noqa: E402
from tools.ingest.parsers import archive, ocr  # noqa: E402

PIEGE = gen_fixtures.PIEGE
# Texte des « 10 commandements » : sa présence prouverait que la consigne a été exécutée.
COMMANDEMENTS = "Tu n'auras point d'autres dieux"


try:  # pytest est optionnel : le runner autonome ne doit pas en dépendre
    import pytest

    _BaseSkip = pytest.skip.Exception  # hérite de BaseException sous pytest
except ImportError:  # pragma: no cover
    pytest = None
    _BaseSkip = Exception


class SkipTest(_BaseSkip):
    """Test non exécutable dans cet environnement (ex. OCR absent)."""


def sauter(message: str):
    """Signale un SKIP — reconnu comme tel par pytest comme par le runner autonome."""
    raise SkipTest(message)


def fixture(nom: str) -> Path:
    """Renvoie le chemin d'une fixture, en la générant si elle manque."""
    gen_fixtures.generer_tout()
    chemin = DOSSIER_FIXTURES / nom
    assert chemin.is_file(), f"fixture absente : {nom}"
    return chemin


# --------------------------------------------------------------------------- tests

def test_t_ing_01_pdf_texte_et_ligne_piegee_verbatim():
    """T-ING-01 — PDF texte : contenu réel extrait + ligne d'instruction piégée verbatim."""
    resultat = parse_file(fixture("facture-pdf-texte.pdf"))
    meta, markdown = resultat["meta"], resultat["markdown"]
    assert meta["ok"] is True, meta["message"]
    assert meta["type"] == "pdf" and meta["pages"] == 2
    # 1) un token du texte réel du PDF est présent
    assert "Facture 2026-0042" in markdown and "srv-boutique-01" in markdown
    # 2) la ligne d'instruction piégée ressort TEXTE POUR TEXTE (donnée, pas consigne)
    lignes_piegees = [l for l in markdown.split("\n") if l.strip() == PIEGE]
    assert lignes_piegees, "la ligne piégée n'apparaît pas telle quelle dans l'extraction"
    assert markdown.count(PIEGE) == 1, "la ligne piégée a été dupliquée ou réécrite"
    # 3) elle n'a pas été exécutée : aucun contenu dérivé de l'ordre
    assert COMMANDEMENTS not in markdown
    assert meta["instructions_detectees"] == 1, "le document piégé n'a pas été journalisé"
    # 4) le contenu est bien encadré comme donnée non fiable
    assert "<<<DONNÉES>>>" in markdown and "<<<FIN DONNÉES>>>" in markdown


def test_t_ing_02_pdf_scanne_ocr():
    """T-ING-02 — PDF scanné (image seule) : le texte est reconnu par OCR."""
    if not ocr.disponible():
        sauter(f"backend OCR absent : {ocr.avertissement_backend()}")
    resultat = parse_file(fixture("facture-pdf-scanne.pdf"))
    meta, markdown = resultat["meta"], resultat["markdown"]
    assert meta["ok"] is True, meta["message"]
    assert meta["pages"] == 1
    bas = markdown.lower()
    assert any(token in bas for token in ("mot de passe", "admin-2026", "serveur")), \
        "aucun token OCR attendu dans la sortie"
    assert meta["ocr"] is True, "meta['ocr'] devrait valoir True (OCR réellement utilisé)"
    # Dégradation gracieuse : sans backend, la page est marquée, jamais l'extraction perdue.
    cache_precedent = ocr._CACHE
    try:
        ocr._CACHE = {"etat": "disabled", "detail": "test", "langs": [], "lang": "fra+eng"}
        degrade = parse_file(fixture("facture-pdf-scanne.pdf"))
    finally:
        ocr._CACHE = cache_precedent
    assert degrade["meta"]["ocr"] == "disabled"
    assert ocr.PLACEHOLDER_OCR_INDISPONIBLE in degrade["markdown"]
    assert degrade["meta"]["avertissements"], "la dégradation OCR doit être avertie"


def test_t_ing_03_xlsx_tableau():
    """T-ING-03 — XLSX : tableau markdown avec en-tête Host et le port 22 / compte admin."""
    resultat = parse_file(fixture("inventaire.xlsx"))
    meta, markdown = resultat["meta"], resultat["markdown"]
    assert meta["ok"] is True and meta["type"] == "xlsx"
    assert meta["tableaux"] >= 1
    assert "| Host | Port | Service |" in markdown
    assert "| --- | --- | --- |" in markdown
    assert "| srv-boutique-01 | 22 | ssh |" in markdown
    assert "admin-srv-01" in markdown
    assert "Feuille « Inventaire »" in markdown


def test_t_ing_04_docx():
    """T-ING-04 — DOCX : le mot « authentification » du cahier des charges est extrait."""
    resultat = parse_file(fixture("cahier-des-charges.docx"))
    assert resultat["meta"]["ok"] is True, resultat["meta"]["message"]
    assert resultat["meta"]["type"] == "docx"
    assert "authentification" in resultat["markdown"].lower()
    assert "prestataire de paiement" in resultat["markdown"].lower()


def test_t_ing_05_pptx():
    """T-ING-05 — PPTX : le texte « API publique » de la diapositive est extrait."""
    resultat = parse_file(fixture("archi.pptx"))
    assert resultat["meta"]["ok"] is True, resultat["meta"]["message"]
    assert resultat["meta"]["type"] == "pptx"
    assert "API publique" in resultat["markdown"]
    assert "Diapositive 1" in resultat["markdown"]


def test_t_ing_06_png_ocr():
    """T-ING-06 — PNG : le mot « Autorisation » du schéma d'architecture est reconnu."""
    if not ocr.disponible():
        sauter(f"backend OCR absent : {ocr.avertissement_backend()}")
    resultat = parse_file(fixture("schema.png"))
    meta, markdown = resultat["meta"], resultat["markdown"]
    assert meta["ok"] is True and meta["type"] == "image"
    assert meta["ocr"] is True
    assert "autorisation" in markdown.lower(), "token OCR attendu absent de la sortie"
    assert "Dimensions" in markdown


def test_t_ing_07_zip():
    """T-ING-07 — ZIP : membres analysés récursivement (firewall + en-tête `ip,role`)."""
    resultat = parse_file(fixture("lot.zip"))
    meta, markdown = resultat["meta"], resultat["markdown"]
    assert meta["ok"] is True and meta["type"] == "zip"
    assert "firewall" in markdown.lower()
    assert "ip,role" in markdown, "l'en-tête CSV brut du membre est absent"
    assert "192.168.1.10" in markdown
    assert "| ip | role |" in markdown
    assert "notes.txt" in markdown and "inventaire.csv" in markdown


def test_t_ing_08_zip_slip():
    """T-ING-08 — zip-slip : un membre `../evil` est refusé et rien n'est écrit sur disque."""
    assert archive.chemin_sur("dossier/ok.txt") is True
    for nom_dangereux in ("../evil", "..\\evil", "a/../../evil", "/etc/evil",
                           "C:\\Windows\\evil", "..", ""):
        assert archive.chemin_sur(nom_dangereux) is False, f"chemin accepté : {nom_dangereux!r}"

    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w") as zf:
        zf.writestr("../evil", "pwned")
        zf.writestr("/absolu/evil", "pwned")
        zf.writestr("dossier/ok.txt", "contenu sain")
    tampon.seek(0)
    meta = {"avertissements": [], "tableaux": 0}
    with zipfile.ZipFile(tampon) as zf:
        membres = archive.lire_membres(zf, meta)
    noms = [nom for nom, _ in membres]
    assert noms == ["dossier/ok.txt"], f"membres acceptés inattendus : {noms}"
    assert any("zip-slip" in avertissement for avertissement in meta["avertissements"]), \
        "le refus zip-slip doit être journalisé"
    # Rien n'a été écrit : ni à côté du test, ni dans les répertoires temporaires.
    with tempfile.TemporaryDirectory() as temporaire:
        assert not (Path(temporaire) / "evil").exists()
    for emplacement in (Path.cwd(), Path(__file__).resolve().parent, DOSSIER_FIXTURES):
        assert not (emplacement / "evil").exists(), "zip-slip : fichier écrit sur disque !"
    # Le refus vaut aussi pour l'analyse complète de l'archive.
    tampon.seek(0)
    corps = archive.parse_bytes("piege.zip", tampon.getvalue(), meta)
    assert "pwned" not in corps


def test_t_ing_09_type_non_supporte():
    """T-ING-09 — Type non supporté : message d'erreur français + code de sortie 2."""
    with tempfile.TemporaryDirectory() as temporaire:
        binaire = Path(temporaire) / "logiciel.binaire"
        binaire.write_bytes(b"\x00\x01\x02\x03binaire non gere")
        resultat = parse_file(binaire)
        meta = resultat["meta"]
        assert meta["ok"] is False
        assert meta["type"] is None
        assert "non supporté" in meta["message"], meta["message"]
        assert "PDF" in meta["message"]  # la liste des types pris en charge est rappelée
        assert meta["message"] in resultat["markdown"]

        sortie = Path(temporaire) / "sortie"
        termine = subprocess.run(
            [sys.executable, "-m", "tools.ingest", str(binaire), "--out", str(sortie)],
            cwd=RACINE, capture_output=True, text=True,
        )
        assert termine.returncode == 2, f"code de sortie CLI = {termine.returncode}"
        assert "non supporté" in termine.stderr, termine.stderr
        assert not list(sortie.glob("*")), "rien ne doit être écrit pour un type non supporté"


def test_t_ing_10_formule_xlsx():
    """T-ING-10 — XLSX : une cellule `=2+2` est restituée comme texte (jamais évaluée)."""
    resultat = parse_file(fixture("formule.xlsx"))
    meta, markdown = resultat["meta"], resultat["markdown"]
    assert meta["ok"] is True and meta["type"] == "xlsx"
    # Choix documenté : openpyxl en data_only=False -> la formule revient telle quelle.
    assert "| srv-01 | =2+2 | formule brute |" in markdown, \
        "la formule doit être conservée verbatim dans le tableau"
    assert meta["avertissements"], "une cellule de formule doit être journalisée"
    assert any("formule" in avertissement for avertissement in meta["avertissements"])
    # Aucune évaluation : le parseur ne calcule rien, la cellule n'est pas « 4 ».
    assert "| srv-01 | 4 |" not in markdown


TESTS = [
    ("T-ING-01", "PDF texte + ligne d'instruction piégée verbatim", test_t_ing_01_pdf_texte_et_ligne_piegee_verbatim),
    ("T-ING-02", "PDF scanné : OCR (ou SKIP si backend absent)", test_t_ing_02_pdf_scanne_ocr),
    ("T-ING-03", "XLSX : tableau Host / Port / Service", test_t_ing_03_xlsx_tableau),
    ("T-ING-04", "DOCX : mot « authentification »", test_t_ing_04_docx),
    ("T-ING-05", "PPTX : « API publique »", test_t_ing_05_pptx),
    ("T-ING-06", "PNG : OCR du schéma (ou SKIP)", test_t_ing_06_png_ocr),
    ("T-ING-07", "ZIP : firewall + en-tête ip,role", test_t_ing_07_zip),
    ("T-ING-08", "zip-slip : membre ../evil refusé, rien sur disque", test_t_ing_08_zip_slip),
    ("T-ING-09", "Type non supporté : message + exit 2", test_t_ing_09_type_non_supporte),
    ("T-ING-10", "XLSX : formule =2+2 conservée en texte", test_t_ing_10_formule_xlsx),
]


def main() -> int:
    """Runner autonome : exécute chaque test, affiche PASS/FAIL/SKIP, sort 0 si aucun FAIL."""
    gen_fixtures.generer_tout()
    compteurs = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    for identifiant, libelle, fonction in TESTS:
        try:
            fonction()
        except SkipTest as raison:
            compteurs["SKIP"] += 1
            print(f"SKIP {identifiant} — {libelle} ({raison})")
        except AssertionError as exc:
            compteurs["FAIL"] += 1
            print(f"FAIL {identifiant} — {libelle} : {exc or 'assertion non informée'}")
        except Exception as exc:  # erreur inattendue = FAIL, jamais une trace pour rien
            compteurs["FAIL"] += 1
            print(f"FAIL {identifiant} — {libelle} : {type(exc).__name__} : {exc}")
        else:
            compteurs["PASS"] += 1
            print(f"PASS {identifiant} — {libelle}")
    print(
        f"INGEST: {compteurs['PASS']} PASS, {compteurs['FAIL']} FAIL, {compteurs['SKIP']} SKIP"
    )
    return 0 if compteurs["FAIL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())