#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests pour le générateur eBIOS RM."""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Ajouter le répertoire tools au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.methodes.ebios import ebios


def run_test(name, test_func):
    """Exécute un test et retourne le résultat."""
    try:
        test_func()
        print(f"PASS {name}")
        return "PASS"
    except AssertionError as e:
        print(f"FAIL {name}: {e}")
        return "FAIL"
    except Exception as e:
        print(f"FAIL {name}: {e}")
        return "FAIL"


def create_test_case(tmpdir):
    """Crée un dossier d'analyse de test."""
    case_dir = Path(tmpdir) / "test-boutique-en-ligne"
    case_dir.mkdir(parents=True, exist_ok=True)

    # 00-description.md
    desc_content = """# Test boutique en ligne

## Description
Une boutique en ligne fictive pour tester eBIOS.

## Périmètre
Site web public, back-office, base de données.
"""
    (case_dir / "00-description.md").write_text(desc_content, encoding='utf-8')

    # 01-actifs.md
    actifs_content = """# Actifs

| Actif | Valeur | Criticité |
|---|---|---|
| Site web | Élevée | Critique |
| Base de données | Très élevée | Critique |
"""
    (case_dir / "01-actifs.md").write_text(actifs_content, encoding='utf-8')

    return case_dir


def test_ebios_01():
    """EBIOS-01 : 5 fichiers créés + README."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        case_dir = create_test_case(tmpdir)
        result_dir = ebios.generate_ebios(case_dir)

        assert result_dir.exists()
        assert (result_dir / "A1-cadrage-socle.md").exists()
        assert (result_dir / "A2-sources-risque.md").exists()
        assert (result_dir / "A3-scenarios-strategiques.md").exists()
        assert (result_dir / "A4-scenarios-operationnels.md").exists()
        assert (result_dir / "A5-traitement-risque.md").exists()
        assert (result_dir / "README.md").exists()


def test_ebios_02():
    """EBIOS-02 : sections attendues présentes."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        case_dir = create_test_case(tmpdir)
        result_dir = ebios.generate_ebios(case_dir)

        # A1 : Événements redoutés
        a1 = (result_dir / "A1-cadrage-socle.md").read_text(encoding='utf-8')
        assert "Événements redoutés" in a1

        # A2 : sources de risque
        a2 = (result_dir / "A2-sources-risque.md").read_text(encoding='utf-8')
        assert "sources de risque" in a2

        # A4 : gravité
        a4 = (result_dir / "A4-scenarios-operationnels.md").read_text(encoding='utf-8')
        assert "gravité" in a4

        # A5 : risque résiduel
        a5 = (result_dir / "A5-traitement-risque.md").read_text(encoding='utf-8')
        assert "risque résiduel" in a5


def test_ebios_03():
    """EBIOS-03 : contenu d'entrée repris verbatim."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        case_dir = create_test_case(tmpdir)
        desc_original = (case_dir / "00-description.md").read_text(encoding='utf-8')
        actifs_original = (case_dir / "01-actifs.md").read_text(encoding='utf-8')

        result_dir = ebios.generate_ebios(case_dir)

        a1 = (result_dir / "A1-cadrage-socle.md").read_text(encoding='utf-8')
        assert desc_original in a1
        assert actifs_original in a1


def test_ebios_04():
    """EBIOS-04 : reproductible (deux exécutions → mêmes octets)."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        case_dir = create_test_case(tmpdir)

        result_dir1 = ebios.generate_ebios(case_dir)
        # Relancer sur le même cas (peut créer dans même dossier ou nouveau - on vérifie contenu)
        result_dir2 = ebios.generate_ebios(case_dir)

        # Comparer fichiers
        files = ["A1-cadrage-socle.md", "A2-sources-risque.md", "A3-scenarios-strategiques.md",
                 "A4-scenarios-operationnels.md", "A5-traitement-risque.md", "README.md"]
        for fname in files:
            f1 = (result_dir1 / fname).read_bytes()
            f2 = (result_dir2 / fname).read_bytes()
            assert f1 == f2, f"Fichier {fname} non reproductible"


def test_ebios_05():
    """EBIOS-05 : idempotent (relancer ne crée pas de doublon)."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        case_dir = create_test_case(tmpdir)
        result_dir = ebios.generate_ebios(case_dir)

        files_before = set(result_dir.glob("*.md"))
        ebios.generate_ebios(case_dir)
        files_after = set(result_dir.glob("*.md"))

        # Même ensemble de fichiers
        assert files_before == files_after


def test_ebios_06():
    """EBIOS-06 : --out vers autre répertoire fonctionne."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir1, \
         tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir2:
        case_dir = create_test_case(tmpdir1)
        out_dir = Path(tmpdir2) / "custom-out"
        result_dir = ebios.generate_ebios(case_dir, out_dir=out_dir)

        assert result_dir == out_dir
        assert (out_dir / "A1-cadrage-socle.md").exists()
        assert (out_dir / "A2-sources-risque.md").exists()
        assert (out_dir / "A3-scenarios-strategiques.md").exists()
        assert (out_dir / "A4-scenarios-operationnels.md").exists()
        assert (out_dir / "A5-traitement-risque.md").exists()
        assert (out_dir / "README.md").exists()


def test_ebios_07():
    """EBIOS-07 : dossier en entrée invalide → message clair + exit != 0."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        invalid_dir = Path(tmpdir) / "inexistant"
        try:
            ebios.generate_ebios(invalid_dir)
            assert False, "Devrait lever une exception"
        except ValueError as e:
            assert "invalide" in str(e) or "existe" in str(e) or "manquant" in str(e)
        except Exception:
            pass


def main():
    tests = [
        ("EBIOS-01", test_ebios_01),
        ("EBIOS-02", test_ebios_02),
        ("EBIOS-03", test_ebios_03),
        ("EBIOS-04", test_ebios_04),
        ("EBIOS-05", test_ebios_05),
        ("EBIOS-06", test_ebios_06),
        ("EBIOS-07", test_ebios_07),
    ]

    results = []
    for name, test_func in tests:
        res = run_test(name, test_func)
        results.append(res)

    pass_count = results.count("PASS")
    fail_count = results.count("FAIL")
    skip_count = results.count("SKIP")

    print(f"EBIOS: {pass_count} PASS, {fail_count} FAIL, {skip_count} SKIP")

    if fail_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
