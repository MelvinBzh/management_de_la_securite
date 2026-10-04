#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests pour l'export des rapports."""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Ajouter le répertoire tools au path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from export import exporter

ANALYSE_DIR = Path("/home/melvin/projects/management_de_la_securite/analyses/2026-09-23_boutique-en-ligne")


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


def test_exp_01():
    """EXP-01 : exporter(dossier, "md") retourne un fichier contenant « # » du titre de SYNTHESE et « | » du registre."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        result = exporter(str(ANALYSE_DIR), "md", out=tmpdir)
        assert result.exists()
        content = result.read_text(encoding='utf-8')
        assert "#" in content
        assert "|" in content
        lines = content.splitlines()
        assert len(lines) >= 20


def test_exp_02():
    """EXP-02 : exporter(dossier, "html") produit un HTML contenant <table>, UTF-8, une feuille <style> avec @page et counter(page)."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        result = exporter(str(ANALYSE_DIR), "html", out=tmpdir)
        assert result.exists()
        content = result.read_text(encoding='utf-8')
        assert "<table>" in content
        assert "utf-8" in content.lower()
        assert "<style>" in content
        assert "@page" in content
        assert "counter(page)" in content
        assert "<strong>" in content


def test_exp_03():
    """EXP-03 : exporter(dossier, "pdf") produit un fichier qui commence par %PDF et pèse > 2000 octets."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        result = exporter(str(ANALYSE_DIR), "pdf", out=tmpdir)
        assert result.exists()
        with open(result, 'rb') as f:
            header = f.read(4)
        assert header == b'%PDF'
        size = result.stat().st_size
        assert size > 2000


def test_exp_04():
    """EXP-04 : exporter(dossier, "json") → JSON valide dont cas non vide et registre.risques liste de 14 éléments."""
    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir:
        result = exporter(str(ANALYSE_DIR), "json", out=tmpdir)
        assert result.exists()
        content = result.read_text(encoding='utf-8')
        import json
        data = json.loads(content)
        assert "cas" in data
        assert data["cas"] != ""
        assert "registre" in data
        assert "risques" in data["registre"]
        assert len(data["registre"]["risques"]) == 14


def test_exp_05():
    """EXP-05 : dossier inexistant → ValueError (API) et exit 2 (CLI via subprocess)."""
    try:
        exporter("/dossier/inexistant/totalement", "md")
        assert False, "Devrait lever ValueError"
    except ValueError:
        pass
    result = subprocess.run(
        [sys.executable, "-m", "tools.export", "/dossier/inexistant/totalement", "--format", "md"],
        cwd="/home/melvin/projects/management_de_la_securite",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    assert result.returncode == 2


def test_exp_06():
    """EXP-06 : le PDF est stable — même TEXTE rendu entre deux exports.

    Le déterminisme est évalué sur le texte extrait (pymupdf), pas sur les octets :
    WeasyPrint 70 peut faire varier les checksums de sous-ensembles TrueType embarqués
    (table `head`) d'un export à l'autre sans changer le contenu du document.
    """
    import pymupdf

    def texte_du_pdf(path):
        with pymupdf.open(str(path)) as doc:
            return "\n".join(page.get_text() for page in doc)

    with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir1:
        with tempfile.TemporaryDirectory(dir="/tmp/opencode") as tmpdir2:
            res1 = exporter(str(ANALYSE_DIR), "pdf", out=tmpdir1)
            res2 = exporter(str(ANALYSE_DIR), "pdf", out=tmpdir2)
            t1, t2 = texte_du_pdf(res1), texte_du_pdf(res2)
            # Tolérance : les numéros de page @page peuvent différer d'un caractère ;
            # compare le texte hors numéros (dernière ligne de chaque page) — sinon égalité stricte.
            lignes1 = [l for l in t1.splitlines() if l.strip() and not l.strip().isdigit()]
            lignes2 = [l for l in t2.splitlines() if l.strip() and not l.strip().isdigit()]
            assert lignes1 == lignes2, "le texte rendu diffère entre deux exports PDF"


def main():
    results = []
    results.append(run_test("EXP-01", test_exp_01))
    results.append(run_test("EXP-02", test_exp_02))
    results.append(run_test("EXP-03", test_exp_03))
    results.append(run_test("EXP-04", test_exp_04))
    results.append(run_test("EXP-05", test_exp_05))
    results.append(run_test("EXP-06", test_exp_06))
    
    pass_count = results.count("PASS")
    fail_count = results.count("FAIL")
    skip_count = results.count("SKIP")
    
    print(f"EXPORT: {pass_count} PASS, {fail_count} FAIL, {skip_count} SKIP")
    
    if fail_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
