#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests de l'interface (Streamlit AppTest) pour la page « Connaissances », le bloc « validation humaine » de l'étape ④
et l'affichage des citations. Aucun modèle, aucun réseau : l'index est construit avec de faux moteurs.

À lancer là où streamlit est installé (le conteneur) : `python web/tests/test_pages_connaissance.py`.
"""
from __future__ import annotations

import re
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


PAGE_CONN = "Connaissances du projet (lecture seule)"

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

# --- 3. étape ④ : un groupe à l'écran à la fois, avec pourquoi / quoi vérifier et le choix juste dessous ------------------------
d = racine / NOM
(d / "registre-risques.md").write_text(NL.join(["# Registre", "", "| ID | Actif | Menace | valide_par |", "|---|---|---|---|",
                                               "| R-01 | Site | Vol de comptes | *À valider par l'analyste* |"]), encoding="utf-8")
controles.enregistrer(d, 4, "Étape 4 · Évaluation", "gemma4:12b", "non_conforme", "", None, "x",
                      humaine=controles.pourquoi_et_quoi("illisible", "", ["04-evaluation.md"]), doutes=["| Site | PHP 8 [E1] |"])
app = ouvrir(racine, "④ Validation")
verifier("④ : aucune exception", not app.exception)
vue = next(r for r in app.radio if str(r.key) == "valid_vue")
options_vue = [str(o) for o in vue.options]
ordre_types = [o.split(" — ")[0] for o in options_vue]
verifier("④ : contradictions et questions viennent en premier, puis les risques",
         ordre_types.index(next(o for o in ordre_types if o.startswith("Risques"))) >=
         max(i for i, o in enumerate(ordre_types) if o.startswith(("Contradictions", "Questions"))) + 1
         if any(o.startswith(("Contradictions", "Questions")) for o in ordre_types) else True)
vue.set_value(next(o for o in options_vue if o.startswith("Risques")))
with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    app.run()
vue = next(r for r in app.radio if str(r.key) == "valid_vue")  # les éléments sont recréés à chaque run
verifier("④ : une vue par groupe (risques, étapes à valider…) avec le nombre restant à décider",
         any(o.startswith("Risques") and "à décider sur" in o for o in options_vue) and any("Étapes à valider" in o for o in options_vue))
tout = textes(app) + " " + " ".join(str(e.value) for e in app.subheader)
verifier("④ : le risque est devant l'analyste, avec pourquoi et quoi vérifier", "Pourquoi" in tout and "Quoi vérifier" in tout and "Risques de niveau" in tout)
verifier("④ : le contexte est consultable", any("contexte" in str(e.label).lower() for e in app.expander))
cartes = [r for r in app.radio if str(r.key).startswith("vdec_")]
verifier("④ : un choix par point, « À décider » par défaut, avec les trois décisions sur un risque",
         len(cartes) == 1 and cartes[0].value == "" and "Accepté tel quel" in [str(o) for o in cartes[0].options])
verifier("④ : un motif par point", len([t for t in app.text_area if str(t.key).startswith("vcom_")]) == 1
         and any("Motif" in str(t.label) for t in app.text_area))
verifier("④ : avancement visible", any("décidé" in str(e.value) for e in app.progress) if hasattr(app, "progress") else True)
verifier("④ : jamais le mot « indéterminé »", "indéterminé" not in tout.lower())
# la vue « étapes à valider » : pourquoi / quoi vérifier de l'étape
vue.set_value(next(o for o in options_vue if "Étapes à valider" in o))
with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    app.run()
tout_e = textes(app) + " " + " ".join(str(e.value) for e in app.subheader)
verifier("④ : la vue des étapes montre pourquoi, quoi vérifier et le fichier à relire", "Pourquoi" in tout_e and "04-evaluation.md" in tout_e)
# retour aux risques ; une décision depuis l'interface : le risque est enregistré au nom de l'analyste
vue = next(r for r in app.radio if str(r.key) == "valid_vue")
vue.set_value(next(str(o) for o in vue.options if str(o).startswith("Risques")))
with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    app.run()
app.text_input(key="valid_analyste").set_value("Marie")
for r in app.radio:
    if str(r.key).startswith("vdec_") and "Accepté tel quel" in [str(o) for o in r.options]:
        r.set_value("Accepté tel quel")  # AppTest expose les LIBELLÉS affichés
        break
bouton = next(b for b in app.button if str(b.label).startswith("Enregistrer"))
with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    bouton.click().run()
verifier("④ : aucune exception après enregistrement", not app.exception)
registre_apres = (d / "registre-risques.md").read_text(encoding="utf-8")
verifier("④ : la décision est écrite dans le registre au nom de l'analyste", "Marie" in registre_apres and "accepté" in registre_apres)

# --- 3 bis. ④ un registre de plus de cent risques : un niveau à la fois, les dix premiers, « accepter d'un coup » confirmé -----
lignes_reg = ["# Registre", "", "| ID | Actif | Menace | Niveau | Traitement | Risque résiduel | valide_par |", "|---|---|---|---|---|---|---|"]
for i in range(1, 26):
    lignes_reg.append(f"| M{i:03d} | A{i:02d} — actif {i} | menace numéro {i} | {'Critique' if i <= 12 else 'Moyen'} | Réduire | Faible | |")
(d / "registre-risques.md").write_text(NL.join(lignes_reg) + NL, encoding="utf-8")
app = ouvrir(racine, "④ Validation")
verifier("④ registre de 25 risques : aucune exception", not app.exception)
vue = next(r for r in app.radio if str(r.key) == "valid_vue")
options_vue = [str(o) for o in vue.options]
vue.set_value(next(o for o in options_vue if "Risques Critique" in o))
with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    app.run()
vue = next(r for r in app.radio if str(r.key) == "valid_vue")
verifier("④ une vue par niveau : Critique (12) et Moyen (13)",
         any("Risques Critique" in o and "12 à décider sur 12" in o for o in options_vue)
         and any("Risques Moyen" in o and "13 à décider sur 13" in o for o in options_vue))
cartes_risque = [r for r in app.radio if str(r.key).startswith("vdec_") and "Accepté tel quel" in [str(o) for o in r.options]]
verifier("④ le niveau Critique est devant l'analyste : 10 cartes à la fois, enregistrables juste dessous", len(cartes_risque) == 10
         and any(str(b.label) == "Enregistrer ces 10 décisions" for b in app.button))
verifier("④ le tableau du niveau montre ses 12 risques et leur décision",
         any(len(df.value) == 12 and "Décision" in list(df.value.columns) for df in app.dataframe))
vue.set_value(next(o for o in options_vue if "Risques Moyen" in o))
with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    app.run()
bouton_bloc = next((b for b in app.button if str(b.key) == "valid_bulk_Moyen"), None)
verifier("④ « accepter d'un coup » est refusé tant que le tableau n'est pas confirmé", bouton_bloc is not None and bouton_bloc.disabled)
next(c for c in app.checkbox if str(c.key) == "valid_bulk_ok_Moyen").set_value(True)
with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    app.run()
app.text_input(key="valid_analyste").set_value("Marie")
bouton_bloc = next(b for b in app.button if str(b.key) == "valid_bulk_Moyen")
with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    bouton_bloc.click().run()
verifier("④ « accepter d'un coup » : aucune exception", not app.exception)
reg_apres = (d / "registre-risques.md").read_text(encoding="utf-8")
decides_moyens = [l for l in reg_apres.splitlines() if re.match(r"\| M0(1[3-9]|2[0-5]) \|", l) and "Marie" in l and "accepté" in l]
decides_critiques = [l for l in reg_apres.splitlines() if re.match(r"\| M0(0[1-9]|1[0-2]) \|", l) and "Marie" in l]
verifier("④ les 13 risques moyens sont acceptés au nom de l'analyste", len(decides_moyens) == 13)
verifier("④ les risques critiques non décidés ne sont pas touchés", decides_critiques == [])

# --- 4. ③ Résultats : citations lisibles, aucun HTML venu du livrable ---------------------------------------------------------
index = Index(travail.chemins(d)[1])
ident = index.base.execute("SELECT id FROM elements WHERE genre='fait' LIMIT 1").fetchone()[0]
index.fermer()
(d / "SYNTHESE.md").write_text(f"# Synthèse{NL}{NL}Le site est en PHP [E{ident}].{NL}<script>alert(1)</script>{NL}", encoding="utf-8")
app = ouvrir(racine, "③ Résultats")
verifier("③ : aucune exception avec des citations", not app.exception)
verifier("③ : le registre (25 risques) s'affiche en tableau défilant, pas en 25 lignes de Markdown",
         any(len(df.value) == 25 and "valide_par" in list(df.value.columns) for df in app.dataframe))
rendu = " ".join(str(e.value) for e in app.markdown)
verifier("③ : la citation devient une note avec infobulle", "<sup title=" in rendu and "PHP 7.4" in rendu)
avec_html = [str(e.value) for e in app.markdown if "<sup title=" in str(e.value)]
verifier("③ : le HTML du livrable est neutralisé dans le rendu qui autorise du HTML", avec_html and all("<script>" not in x for x in avec_html))

print("PAGES-CONNAISSANCE:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
