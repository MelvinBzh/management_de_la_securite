#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de l'inventaire réseau local-only E21 (RESEAU-01 → RESEAU-06).

Exécution sans dépendance externe :
    python3 tools/reseau/tests/test_inventaire.py
Sortie attendue : RESEAU: N PASS, M FAIL, K SKIP (EXIT 0 seulement si 0 FAIL).
"""
from __future__ import annotations

import io
import json
import os
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

from tools.reseau import inventaire  # noqa: E402


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
    chemin = DOSSIER_FIXTURES / nom
    assert chemin.is_file(), f"fixture absente : {nom}"
    return chemin


def test_reseau_01_fixture_sans_ip_mac():
    """RESEAU-01 : fixture → aucun IP/MAC du fixture dans rapport anonymisé."""
    with tempfile.TemporaryDirectory() as td:
        out_raw = Path(td) / "raw"
        out_anon = Path(td) / "anon"
        fixture_path = fixture("inventaire-fixture.json")
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.reseau.inventaire",
                "--out-raw",
                str(out_raw),
                "--out-anon",
                str(out_anon),
                "--fixtures",
                str(fixture_path),
            ],
            cwd=str(RACINE),
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0, res.stderr
        rapport = (out_anon / "inventaire-anonymise.md").read_text(encoding="utf-8")
        # Vérifie absence d'IP/MAC réels du fixture
        assert "192.168.1.10" not in rapport
        assert "192.168.1.20" not in rapport
        assert "aa:bb:cc:dd:ee:01" not in rapport
        assert "aa:bb:cc:dd:ee:02" not in rapport


def test_reseau_02_roles_attendus():
    """RESEAU-02 : les rôles attendus apparaissent (web, bdd…)."""
    with tempfile.TemporaryDirectory() as td:
        out_raw = Path(td) / "raw"
        out_anon = Path(td) / "anon"
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.reseau.inventaire",
                "--out-raw",
                str(out_raw),
                "--out-anon",
                str(out_anon),
                "--fixtures",
                str(fixture("inventaire-fixture.json")),
            ],
            cwd=str(RACINE),
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0
        rapport = (out_anon / "inventaire-anonymise.md").read_text(encoding="utf-8")
        # Doit contenir web et bdd (et autres services peuvent exister)
        assert "web" in rapport.lower()
        assert "bdd" in rapport.lower()


def test_reseau_03_expose_apparait():
    """RESEAU-03 : mention « exposé » pour service en 0.0.0.0."""
    with tempfile.TemporaryDirectory() as td:
        out_raw = Path(td) / "raw"
        out_anon = Path(td) / "anon"
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.reseau.inventaire",
                "--out-raw",
                str(out_raw),
                "--out-anon",
                str(out_anon),
                "--fixtures",
                str(fixture("inventaire-fixture.json")),
            ],
            cwd=str(RACINE),
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0
        rapport = (out_anon / "inventaire-anonymise.md").read_text(encoding="utf-8")
        assert "exposé" in rapport.lower()


def test_reseau_04_raw_json_ecrit():
    """RESEAU-04 : --out-raw écrit bien inventaire-raw.json."""
    with tempfile.TemporaryDirectory() as td:
        out_raw = Path(td) / "raw"
        out_anon = Path(td) / "anon"
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.reseau.inventaire",
                "--out-raw",
                str(out_raw),
                "--out-anon",
                str(out_anon),
                "--fixtures",
                str(fixture("inventaire-fixture.json")),
            ],
            cwd=str(RACINE),
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0
        raw_file = out_raw / "inventaire-raw.json"
        assert raw_file.is_file()
        data = json.loads(raw_file.read_text(encoding="utf-8"))
        assert isinstance(data, dict)


def test_reseau_05_sans_fixtures_ss_absent():
    """RESEAU-05 : sans fixtures, ss/ip absents → rapport mentionne indisponibles sans crash."""
    from tools.reseau import inventaire as inv

    def fake_run(cmd, capture_output=True, text=True, timeout=10, check=False):
        raise FileNotFoundError("commande introuvable")

    orig = subprocess.run
    try:
        subprocess.run = fake_run  # type: ignore
        with tempfile.TemporaryDirectory() as td:
            out_raw = Path(td) / "raw"
            out_anon = Path(td) / "anon"
            data = inv.collecter_local()
            inv.generer_rapport_anonymise(data, out_anon)
            rapport = (out_anon / "inventaire-anonymise.md").read_text(encoding="utf-8")
            assert "commandes indisponibles" in rapport.lower() or "indisponibles" in rapport.lower()
    finally:
        subprocess.run = orig


def test_reseau_06_reproductible():
    """RESEAU-06 : 2 runs avec fixtures → octets identiques."""
    with tempfile.TemporaryDirectory() as td1:
        with tempfile.TemporaryDirectory() as td2:
            for td, out_raw, out_anon in [
                (td1, Path(td1) / "raw", Path(td1) / "anon"),
                (td2, Path(td2) / "raw", Path(td2) / "anon"),
            ]:
                res = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "tools.reseau.inventaire",
                        "--out-raw",
                        str(out_raw),
                        "--out-anon",
                        str(out_anon),
                        "--fixtures",
                        str(fixture("inventaire-fixture.json")),
                    ],
                    cwd=str(RACINE),
                    capture_output=True,
                    text=True,
                )
                assert res.returncode == 0
            # La date de génération est à la seconde près : deux runs successifs
            # sont forcément différents sur cette ligne (test « bombe » flottant,
            # échouait dès que le second changeait entre les deux exécutions, ce
            # qui arrive presque toujours sur une CI lente). On neutralise CETTE
            # ligne et on compare tout le reste — c'est bien cela la valeur de
            # « reproductible » : rôles, tableau, mentions, absence d'IP/MAC.
            def _sans_date(brut: bytes) -> bytes:
                return re.sub(rb"^Date : .*$", b"Date : <neutralisee>", brut, flags=re.M)

            r1 = _sans_date((Path(td1) / "anon" / "inventaire-anonymise.md").read_bytes())
            r2 = _sans_date((Path(td2) / "anon" / "inventaire-anonymise.md").read_bytes())
            assert r1 == r2


TESTS = [
    ("RESEAU-01", "fixture → aucun IP/MAC dans rapport anonymisé", test_reseau_01_fixture_sans_ip_mac),
    ("RESEAU-02", "rôles attendus apparaissent (web, bdd…)", test_reseau_02_roles_attendus),
    ("RESEAU-03", "mention « exposé » pour service en 0.0.0.0", test_reseau_03_expose_apparait),
    ("RESEAU-04", "--out-raw écrit inventaire-raw.json", test_reseau_04_raw_json_ecrit),
    ("RESEAU-05", "ss/ip absents → gestion propre", test_reseau_05_sans_fixtures_ss_absent),
    ("RESEAU-06", "reproductible avec fixtures", test_reseau_06_reproductible),
]


def main() -> int:
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
    print(f"RESEAU: {compteurs['PASS']} PASS, {compteurs['FAIL']} FAIL, {compteurs['SKIP']} SKIP")
    return 0 if compteurs["FAIL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
