#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes du détecteur de menaces E21 (DETECTION-01 → DETECTION-08).

Exécution sans dépendance externe :
    python3 tools/reseau/tests/test_detection.py
Sortie attendue : DETECTION: N PASS, M FAIL, K SKIP (EXIT 0 seulement si 0 FAIL).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
DOSSIER_FIXTURES = Path(__file__).resolve().parent / "fixtures"
for chemin in (str(RACINE), str(DOSSIER_FIXTURES)):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from tools.reseau.detection import detect  # noqa: E402


try:
    import pytest

    _BaseSkip = pytest.skip.Exception
except ImportError:  # pragma: no cover
    pytest = None
    _BaseSkip = Exception


class SkipTest(_BaseSkip):
    """Test non exécutable dans cet environnement."""


def sauter(message: str):
    raise SkipTest(message)


def fixture(nom: str) -> Path:
    """Renvoie le chemin d'une fixture, en sautant le test si elle est absente."""
    chemin = DOSSIER_FIXTURES / nom
    if not chemin.is_file():
        sauter(f"fixture absente : {nom}")
    return chemin


def executer(*args: str) -> subprocess.CompletedProcess:
    """Lance le CLI du détecteur depuis la racine du dépôt."""
    return subprocess.run(
        [sys.executable, "-m", "tools.reseau.detection.detect", *args],
        cwd=str(RACINE),
        capture_output=True,
        text=True,
    )


def rapport_malveillants(chemin_rapport: Path) -> str:
    """Produit le rapport Markdown sur la fixture malveillante."""
    res = executer(str(fixture("evenements-malveillants.jsonl")), "--out", str(chemin_rapport))
    assert res.returncode == 0, f"CLI en échec : {res.stderr}"
    return chemin_rapport.read_text(encoding="utf-8")


def test_detection_01_familles_detectees():
    """DETECTION-01 : la fixture malveillante déclenche ≥ 6 familles distinctes."""
    with tempfile.TemporaryDirectory() as td:
        rapport = rapport_malveillants(Path(td) / "rapport.md")
    regles, _document = detect.charger_regles(detect.CHEMIN_REGLES_DEFAUT)
    evenements, _format = detect.lire_evenements(fixture("evenements-malveillants.jsonl"))
    alertes = detect.evaluer(regles, evenements)
    familles = {alerte.regle.famille for alerte in alertes}
    identifiants = {alerte.regle.identifiant for alerte in alertes}
    assert len(alertes) >= 6, f"alertes insuffisantes : {len(alertes)}"
    assert len(identifiants) >= 6, f"règles déclenchées insuffisantes : {sorted(identifiants)}"
    assert len(familles) >= 6, f"familles distinctes insuffisantes : {sorted(familles)}"
    # Le rapport Markdown doit refléter les mêmes déclenchements.
    tableau = re.findall(r"^\| (DET-\d{2}) \| ([^|]+?) \| (\d+) \|", rapport, re.MULTILINE)
    compte_par_regle = {identifiant: int(nombre) for identifiant, _famille, nombre in tableau}
    for identifiant in identifiants:
        assert compte_par_regle.get(identifiant, 0) >= 1, f"{identifiant} absent du tableau des occurrences"


def test_detection_02_benins_sans_alerte():
    """DETECTION-02 : la fixture bénine ne déclenche aucune alerte."""
    with tempfile.TemporaryDirectory() as td:
        sortie = Path(td) / "rapport-benins.md"
        res = executer(str(fixture("evenements-benins.jsonl")), "--out", str(sortie))
        assert res.returncode == 0, res.stderr
        rapport = sortie.read_text(encoding="utf-8")
    assert "Alertes déclenchées : 0" in rapport
    assert "Aucune alerte" in rapport
    assert "| DET-" in rapport, "le tableau des occurrences doit lister les règles"
    assert not re.search(r"^\| DET-\d{2} \| [^|]+ \| [1-9]\d* \|", rapport, re.MULTILINE)
    assert "Alertes déclenchées: 0" in res.stdout
    assert "Familles concernées: aucune" in res.stdout


def test_detection_03_identifiants_mitre():
    """DETECTION-03 : le rapport contient au moins un identifiant MITRE T####."""
    with tempfile.TemporaryDirectory() as td:
        rapport = rapport_malveillants(Path(td) / "rapport.md")
    assert re.search(r"T\d{4}", rapport), "aucun identifiant de technique MITRE dans le rapport"


def test_detection_04_regles_introuvables():
    """DETECTION-04 : un fichier de règles inexistant sort en erreur (code non nul)."""
    res = executer(str(fixture("evenements-malveillants.jsonl")), "--regles", "regles/inexistant.json")
    assert res.returncode != 0, "un fichier de règles absent doit être refusé"
    assert "erreur" in res.stderr.lower()
    assert "inexistant.json" in res.stderr


def test_detection_05_entrees_limites():
    """DETECTION-05 : fichier vide → rapport sans alerte (exit 0) ; CSV accepté."""
    with tempfile.TemporaryDirectory() as td:
        vide = Path(td) / "vide.jsonl"
        vide.write_text("", encoding="utf-8")
        sortie = Path(td) / "rapport-vide.md"
        res = executer(str(vide), "--out", str(sortie))
        assert res.returncode == 0, res.stderr
        rapport = sortie.read_text(encoding="utf-8")
    assert "Événements analysés : 0" in rapport
    assert "Alertes déclenchées : 0" in rapport
    assert "Aucune alerte" in rapport

    # Même exigence de robustesse pour le second format d'entrée : un flux CSV
    # est évalué à l'identique et conserve ses lignes source verbatim.
    with tempfile.TemporaryDirectory() as td:
        flux = Path(td) / "evenements.csv"
        flux.write_text(
            "ts,source,dest,port,type,detail,octets\n"
            "2026-05-04T06:10:00Z,192.0.2.30,203.0.113.20,443,transfert,export massif,200000000\n"
            "2026-05-04T08:00:00Z,203.0.113.30,203.0.113.20,443,http-200,GET /catalogue -> 200,\n",
            encoding="utf-8",
        )
        rapport_csv = Path(td) / "rapport-csv.md"
        res_csv = executer(str(flux), "--out", str(rapport_csv))
        assert res_csv.returncode == 0, res_csv.stderr
        contenu = rapport_csv.read_text(encoding="utf-8")
    assert "format : CSV" in contenu
    assert "| DET-07 | exfiltration | 1 |" in contenu, "l'exfiltration CSV doit être détectée"
    assert "2026-05-04T06:10:00Z,192.0.2.30,203.0.113.20,443,transfert,export massif,200000000" in contenu


def test_detection_06_detail_verbatim():
    """DETECTION-06 : le détail d'un événement malveillant est repris verbatim."""
    with tempfile.TemporaryDirectory() as td:
        rapport = rapport_malveillants(Path(td) / "rapport.md")
    evenements = [
        json.loads(ligne)
        for ligne in fixture("evenements-malveillants.jsonl").read_text(encoding="utf-8").splitlines()
        if ligne.strip()
    ]
    brut = [e for e in evenements if e.get("type") == "transfert" and int(e.get("octets", 0)) >= 150000000]
    assert brut, "fixture malveillante sans événement de transfert volumineux"
    detail = brut[0]["detail"]
    assert detail in rapport, f"détail absent du rapport : {detail!r}"


def test_detection_07_reproductible():
    """DETECTION-07 : deux exécutions produisent exactement les mêmes octets."""
    with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
        r1 = Path(td1) / "rapport.md"
        r2 = Path(td2) / "rapport.md"
        assert executer(str(fixture("evenements-malveillants.jsonl")), "--out", str(r1)).returncode == 0
        assert executer(str(fixture("evenements-malveillants.jsonl")), "--out", str(r2)).returncode == 0
        octets1 = r1.read_bytes()
        octets2 = r2.read_bytes()
    assert octets1 == octets2, "le rapport n'est pas reproductible d'un run à l'autre"


def test_detection_08_option_out():
    """DETECTION-08 : --out écrit le rapport demandé et rien n'est écrit ailleurs."""
    with tempfile.TemporaryDirectory() as td:
        sortie = Path(td) / "sous" / "rapport.md"
        res = executer(str(fixture("evenements-malveillants.jsonl")), "--out", str(sortie))
        assert res.returncode == 0, res.stderr
        assert sortie.is_file(), "--out n'a pas produit de fichier"
        contenu = sortie.read_text(encoding="utf-8")
        assert contenu.startswith("# Rapport de détection E21")
        assert "## Occurrences par règle" in contenu
        assert "## Alertes" in contenu
        assert str(sortie) in res.stdout


TESTS = [
    ("DETECTION-01", "≥ 6 familles distinctes sur la fixture malveillante", test_detection_01_familles_detectees),
    ("DETECTION-02", "0 alerte sur la fixture bénine", test_detection_02_benins_sans_alerte),
    ("DETECTION-03", "identifiant MITRE T#### dans le rapport", test_detection_03_identifiants_mitre),
    ("DETECTION-04", "--regles inexistant → exit non nul", test_detection_04_regles_introuvables),
    ("DETECTION-05", "entrées limites : fichier vide et flux CSV", test_detection_05_entrees_limites),
    ("DETECTION-06", "détail d'un événement malveillant repris verbatim", test_detection_06_detail_verbatim),
    ("DETECTION-07", "rapport reproductible (2 runs identiques)", test_detection_07_reproductible),
    ("DETECTION-08", "--out écrit le rapport demandé", test_detection_08_option_out),
]


def main() -> int:
    """Exécute tous les tests et renvoie 0 seulement si aucun échec."""
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
        except Exception as exc:
            compteurs["FAIL"] += 1
            print(f"FAIL {identifiant} — {libelle} : {type(exc).__name__} : {exc}")
        else:
            compteurs["PASS"] += 1
            print(f"PASS {identifiant} — {libelle}")
    print(f"DETECTION: {compteurs['PASS']} PASS, {compteurs['FAIL']} FAIL, {compteurs['SKIP']} SKIP")
    return 0 if compteurs["FAIL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())