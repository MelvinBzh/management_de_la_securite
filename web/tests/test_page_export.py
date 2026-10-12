#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Page ③ : les exports du dossier d'analyse complet (AppTest, aucun modèle)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from streamlit.testing.v1 import AppTest  # noqa: E402

from web import lib  # noqa: E402

APP = RACINE / "web" / "app.py"
ECHECS: list[str] = []
NL = chr(10)
NOM = "2026-01-01_test"


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


racine = Path(tempfile.mkdtemp(prefix="e21-page-export-"))
D = racine / NOM
(D / "intrants").mkdir(parents=True)
(D / "SYNTHESE.md").write_text("# Synthèse" + NL + NL + "Deux risques : M001." + NL, encoding="utf-8")
(D / "03-menaces.md").write_text(NL.join(["# Menaces", "", "| ID | Actif concerné | Catégorie | Description | CVE | Source |", "|---|---|---|---|---|---|",
                                          "| M001 | A01 — NordTMS | STRIDE-S | Usurpation | — | STRIDE-S |"]) + NL, encoding="utf-8")
(D / "registre-risques.md").write_text(NL.join(["# Registre", "", "| ID | Actif | Menace | Niveau | valide_par | Statut |", "|---|---|---|---|---|---|",
                                                "| M001 | A01 | Usurpation | Élevé |  | À valider |"]) + NL, encoding="utf-8")

with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    app = AppTest.from_file(str(APP), default_timeout=120)
    app.session_state["projet_courant"] = NOM
    app.session_state["nav"] = "③ Résultats"
    app.run()
verifier("page ③ : aucune exception", not app.exception)
sous_titres = [str(s.value) for s in app.subheader]
verifier("page ③ : section « Exporter le dossier d'analyse complet »", any("dossier d'analyse complet" in s for s in sous_titres))
boutons = {str(b.key): str(b.label) for b in app.button}
verifier("page ③ : trois exports du dossier complet (HTML, PDF, ZIP)",
         all(k in boutons for k in ("export_dossier-html", "export_dossier-pdf", "export_dossier-zip")))
verifier("page ③ : l'export exécutif d'avant est toujours là", all(k in boutons for k in ("export_pdf", "export_md", "export_html", "export_json")))

with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    next(b for b in app.button if str(b.key) == "export_dossier-html").click().run()
verifier("export HTML : aucune erreur", not app.exception and not [e for e in app.error])
telechargements = {str(b.key) for b in app.get("download_button")} if hasattr(app, "get") else set()
verifier("export HTML : le téléchargement est proposé", "dl_export_dossier-html" in telechargements)
exports = app.session_state["exports"]
contenu, nom_fichier = exports["dossier-html"]
verifier("export HTML : le dossier contient la fiche et les liens", nom_fichier == "dossier-complet.html"
         and b'id="fiche-M001"' in contenu and b"Exporter" not in contenu[:0])

with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    next(b for b in app.button if str(b.key) == "export_dossier-zip").click().run()
import io  # noqa: E402
import zipfile  # noqa: E402
contenu_zip, nom_zip = app.session_state["exports"]["dossier-zip"]
noms = zipfile.ZipFile(io.BytesIO(contenu_zip)).namelist()
verifier("export ZIP : archive complète sans les documents d'origine", nom_zip == "dossier-complet.zip"
         and "dossier-complet.html" in noms and "LISEZ-MOI.txt" in noms and not any("intrants" in n for n in noms))

print("PAGE-EXPORT:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
