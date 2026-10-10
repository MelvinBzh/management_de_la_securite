#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de l'interface (Streamlit AppTest) pour la page « Connaissances », le bloc « validation humaine » de l'étape ④
et l'affichage des citations. Aucun modèle, aucun réseau : l'index est construit avec de faux moteurs.

À lancer là où streamlit est installé (le conteneur) : `python web/tests/test_pages_connaissance.py`.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from streamlit.testing.v1 import AppTest  # noqa: E402

from tools.connaissance import couverture, fiches, ingestion, relations, travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402
from web import controles, lib  # noqa: E402

APP = RACINE / "web" / "app.py"
ECHECS: list[str] = []


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


NL = chr(10)
NOM = "2026-01-01_test"


def moteurs() -> ingestion.Moteurs:
    def faits(nom, contenu):
        return [fiches.Fait(nom, "Le site est en PHP", "Le site est développé en PHP 7.4", True)]

    def rels(nom, contenu):
        return [relations.Entite(nom, "K. Benali", "personne")], []

    def croiser(index, **_):
        return []

    def evaluer(index, besoin, vec=None, **_):
        return couverture.Reponse(besoin, couverture.INCONNU, "", (), "Journal de restauration", "sans_objet", True, "Aucune preuve.")

    return ingestion.Moteurs(faits, rels, lambda t, **_: [[1.0, 0.0, 1.0] for _ in t], croiser, evaluer)


def projet(avec_index: bool) -> Path:
    racine = Path(tempfile.mkdtemp(prefix="e21-pages-"))
    dossier = racine / NOM
    (dossier / "intrants").mkdir(parents=True)
    (dossier / "intrants" / "inventaire.md.md").write_text("# Inventaire" + NL + "Le site est développé en PHP 7.4. " * 30, encoding="utf-8")
    if avec_index:
        assert travail.executer(dossier, moteurs=moteurs()) == 0
    return racine


def ouvrir(racine: Path, page: str) -> AppTest:
    with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
        app = AppTest.from_file(str(APP), default_timeout=90)
        app.session_state["projet_courant"] = NOM
        app.session_state["nav"] = page
        app.run()
    return app


def textes(app: AppTest) -> str:
    return " ".join(str(e.value) for e in list(app.markdown) + list(app.caption) + list(app.info) + list(app.warning) + list(app.success))


PAGE_CONN = "ⓘ Connaissances (lecture seule)"

# --- 1. page « Connaissances » sans rien de construit ----------------------------------------------------------
app = ouvrir(projet(False), PAGE_CONN)
verifier("Connaissances sans index : aucune exception", not app.exception)
verifier("Connaissances sans index : message clair (rien de construit)", "Rien n'est encore construit" in textes(app))
verifier("les boutons de mise à jour sont proposés", any(b.label.startswith("Mettre à jour") for b in app.button))

# --- 2. page « Connaissances » avec un index ------------------------------------------------------------------------
racine = projet(True)
app = ouvrir(racine, PAGE_CONN)
verifier("Connaissances avec index : aucune exception", not app.exception)
verifier("5 onglets : documents, faits, entités, contradictions, savoir/ignorance", len(app.tabs) == 5)
verifier("le document lu et son état sont affichés", len(app.dataframe) >= 1 and "inventaire.md.md" in app.dataframe[0].value.to_string())
verifier("l'état du travail est affiché (À jour)", "À jour" in textes(app))
verifier("le « non documenté » est expliqué comme une question, pas comme une absence", "n'en parlent pas" in textes(app) or "PAS une preuve" in textes(app))
verifier("page en lecture seule : aucun champ de saisie de contenu", not app.text_area)

# --- 3. étape ④ : « nécessite une validation humaine » avec pourquoi et quoi vérifier ------------------------------------
d = racine / NOM
(d / "registre-risques.md").write_text(NL.join(["# Registre", "", "| ID | Actif | Menace | valide_par |", "|---|---|---|---|",
                                               "| R-01 | Site | Vol de comptes | *À valider par l'analyste* |"]), encoding="utf-8")
controles.enregistrer(d, 4, "Étape 4 · Évaluation", "gemma4:12b", "non_conforme", "", None, "x",
                      humaine=controles.pourquoi_et_quoi("illisible", "", ["04-evaluation.md"]), doutes=["| Site | PHP 8 [E1] |"])
app = ouvrir(racine, "④ Validation")
verifier("④ : aucune exception avec des contrôles à valider", not app.exception)
tout = textes(app)
verifier("④ : bloc « Nécessite une validation humaine »", "Nécessite une validation humaine" in tout)
verifier("④ : le pourquoi et le quoi vérifier sont affichés", "Pourquoi" in tout and "Quoi vérifier" in tout and "04-evaluation.md" in tout)
verifier("④ : les lignes en doute sont proposées à la relecture", any("Lignes à relire" in str(e.label) for e in app.expander))
verifier("④ : jamais le mot « indéterminé »", "indéterminé" not in tout.lower())

# --- 4. ③ Résultats : citations lisibles, aucun HTML venu du livrable ---------------------------------------------------------
index = Index(travail.chemins(d)[1])
ident = index.base.execute("SELECT id FROM elements WHERE genre='fait' LIMIT 1").fetchone()[0]
index.fermer()
(d / "SYNTHESE.md").write_text(f"# Synthèse{NL}{NL}Le site est en PHP [E{ident}].{NL}<script>alert(1)</script>{NL}", encoding="utf-8")
app = ouvrir(racine, "③ Résultats")
verifier("③ : aucune exception avec des citations", not app.exception)
rendu = " ".join(str(e.value) for e in app.markdown)
verifier("③ : la citation devient une note avec infobulle", "<sup title=" in rendu and "PHP 7.4" in rendu)
avec_html = [str(e.value) for e in app.markdown if "<sup title=" in str(e.value)]
verifier("③ : le HTML du livrable est neutralisé dans le rendu qui autorise du HTML", avec_html and all("<script>" not in x for x in avec_html))

print("PAGES-CONNAISSANCE:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
