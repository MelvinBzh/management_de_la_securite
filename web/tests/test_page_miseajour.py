#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Page ② : la carte « Mise à jour proposée » (AppTest, aucun modèle) et le lancement de la mise à jour."""
from __future__ import annotations

import sys
import tempfile
import zlib
from pathlib import Path
from unittest import mock

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from streamlit.testing.v1 import AppTest  # noqa: E402

from tools.connaissance import couverture, delta, fiches, ingestion, travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402
from web import lib, lots, miseajour, registre, run_agent  # noqa: E402

APP = RACINE / "web" / "app.py"
ECHECS: list[str] = []
NL = chr(10)
NOM = "2026-01-01_test"


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


def document(sujet: str, *lignes: str) -> str:
    return f"# {sujet}\n\n" + "\n".join(lignes) + "\n" + ("Texte de remplissage sans importance pour le test. " * 8) + "\n"


def vecteur_de(texte: str) -> list[float]:
    v = [0.0] * 64
    for mot in texte.lower().replace(":", " ").replace(".", " ").split():
        v[zlib.crc32(mot.encode()) % 64] += 1.0
    return v


def moteurs():
    def faits(nom, contenu):
        return [fiches.Fait(nom, l, l, True) for l in contenu.splitlines() if l.startswith("Fait")]
    return ingestion.Moteurs(faits, lambda n, c: ([], []), lambda t, **_: [vecteur_de(x) for x in t],
                             lambda index, **_: [], lambda index, besoin, vec=None, **_: couverture.Reponse(
                                 besoin, couverture.INCONNU, "", (), "", "sans_objet", True, ""))


racine = Path(tempfile.mkdtemp(prefix="e21-pagemaj-"))
D = racine / NOM
(D / "intrants").mkdir(parents=True)
chemin_index = travail.chemins(D)[1]
chemin_index.parent.mkdir(parents=True, exist_ok=True)
idx = Index(chemin_index)
M = moteurs()
ingestion.traiter_document(idx, "a.md", document("A", "Fait : le serveur NordTMS est hébergé à Lesquin"), M)
idx.ajouter_entite("NordTMS", "NordTMS", "systeme", ["a.md"])
idx.base.commit()
a1 = idx.base.execute("SELECT id FROM elements WHERE doc = 'a.md' AND genre = 'fait'").fetchone()[0]
titre, colonnes = lots.ENTETES["01-actifs.md"]
(D / "01-actifs.md").write_text(NL.join([titre, "", "| " + " | ".join(colonnes) + " |", "|" + "|".join("---" for _ in colonnes) + "|",
                                         f"| A01 | NordTMS | Logiciel / Service | ERP de transport à Lesquin | Critique | [E{a1}] |"]) + NL,
                                encoding="utf-8")
delta.ecrire_baseline(D, idx, signature="s0")
# un document est ajouté depuis
ingestion.traiter_document(idx, "c.md", document("C", "Fait : la plateforme Yooz dématérialise les factures fournisseurs",
                                                 "Fait : Yooz est hébergée chez l'éditeur en mode SaaS"), M)
idx.ajouter_entite("Yooz", "Yooz", "systeme", ["c.md"])
idx.base.commit()
idx.fermer()
(D / "intrants" / "c.md.md").write_text("# C\n" + "Yooz est la plateforme de dématérialisation. " * 20, encoding="utf-8")


def ouvrir() -> AppTest:
    with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
        app = AppTest.from_file(str(APP), default_timeout=90)
        app.session_state["projet_courant"] = NOM
        app.session_state["nav"] = "② Lancer l'analyse"
        app.run()
    return app


# il faut au moins une étape « terminée » pour que la page considère qu'il existe des livrables
for f in ("03-menaces.md", "04-evaluation.md", "05-traitement.md"):   # tableaux au format actuel (une ligne chacun)
    t, cols = lots.ENTETES[f]
    (D / f).write_text(NL.join([t, "", "| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|",
                                "| M001 | A01 — NordTMS | STRIDE-T | altération " + f"[E{a1}]" + " | — | STRIDE-T |"[: 0] +
                                " | ".join(["x"] * (len(cols) - 1)) + " |"]) + NL, encoding="utf-8")
for f in ("02-methodes.md", "06-validation.md", "registre-risques.md", "SYNTHESE.md", "00-description.md"):
    if not (D / f).is_file():
        (D / f).write_text(f"# {f}\n" + "x " * 60 + NL, encoding="utf-8")
# une ligne dont la citation ne correspond à aucune preuve depuis avant (jamais prise en compte) : proposée, jamais cochée d'office
with open(D / "01-actifs.md", "a", encoding="utf-8") as f_actifs:
    f_actifs.write("| A02 | Ancien outil | Logiciel / Service | Outil sans preuve dans le dossier [E9999] | Interne | [E9999] |" + NL)
app = ouvrir()
verifier("page ② : aucune exception", not app.exception)
anciennes = [c for c in app.checkbox if str(c.key) == "maj_revoir_anciennes"]
verifier("page ② : les lignes à citation sans preuve forment un groupe à part, décoché par défaut",
         len(anciennes) == 1 and anciennes[0].value is False and not [c for c in app.checkbox if str(c.key) == "maj_revoir"])
textes = " ".join(str(e.value) for e in list(app.markdown) + list(app.caption) + list(app.subheader) + list(app.info) + list(app.warning))
verifier("page ② : « Mise à jour proposée » affichée avec ce qui va changer", "Mise à jour proposée" in textes and "ajouté(s)" in textes)
cases = [c for c in app.checkbox if str(c.key).startswith("maj_creer")]
verifier("page ② : la création de l'actif Yooz est cochée par défaut", len(cases) == 1 and cases[0].value is True)
verifier("page ② : le message dit que le reste est conservé et que rien n'est supprimé sans confirmation",
         "reste **identique**" in textes or "identique" in textes)
bouton = next((b for b in app.button if str(b.key) == "appliquer_maj"), None)
verifier("page ② : bouton « Appliquer la mise à jour »", bouton is not None)

# décocher la création puis appliquer : le choix est mémorisé et la mise à jour est lancée (sans exécuter de processus)
cases[0].set_value(False)
lances = []


def faux_lancer(cas, dossier=None, modele=None, env=None, pilote=False, synthese=False, reprendre=False, maj=False):
    lances.append({"cas": cas, "pilote": pilote, "maj": maj, "reprendre": reprendre})
    return {"pid": 1, "fichier_log": str(D / "intrants" / "chaine-x.log"), "dossier": str(D), "proc": None, "commande": "x", "modele": "auto"}


with mock.patch.object(lib, "DOSSIER_ANALYSES", racine), mock.patch.object(run_agent, "lancer", faux_lancer), \
        mock.patch.object(run_agent, "enregistrer_etat", lambda *a, **k: None), \
        mock.patch("web.reglages.decider_lancement", lambda r: {"modele": "ollama/qwen3.5:9b", "config": {}, "repli": False, "raison": ""}):
    app.run()
    next(b for b in app.button if str(b.key) == "appliquer_maj").click().run()
verifier("page ② : la mise à jour est lancée en mode « mise à jour » (pas « tout refaire »)",
         lances and lances[0]["maj"] is True and lances[0]["pilote"] is True and lances[0]["reprendre"] is False)
plan = miseajour.lire_plan(D)
creer = next(i for i in plan["items"] if i["type"] == "creer_actif")
verifier("le choix de l'analyste (décoché) est mémorisé dans le plan", creer["coche"] is False)

# --- page ④ : une décision sur une ligne modifiée revient « à confirmer » avec un avertissement ----------------------------------
import json  # noqa: E402
from web import validations  # noqa: E402

(D / "registre-risques.md").write_text(NL.join([
    "# Registre", "", "| ID | Actif | Menace | Niveau | Traitement | valide_par | Statut |", "|---|---|---|---|---|---|---|",
    "| M001 | A01 — NordTMS | STRIDE-T — altération des tournées | Élevé | Réduire | Marie · accepté · 2026-10-11 | À confirmer |"]) + NL,
    encoding="utf-8")
(D / "validations.json").write_text(json.dumps({"decisions": {validations.identifiant("risque", "M001"): {
    "decision": "accepte", "commentaire": "", "analyste": "Marie", "date": "2026-10-11 10:00", "type": "risque",
    "titre": "M001 — A01 — NordTMS · altération", "libelle_decision": "Accepté tel quel", "contenu": "ancienne-empreinte"}}}), encoding="utf-8")
with mock.patch.object(lib, "DOSSIER_ANALYSES", racine):
    app4 = AppTest.from_file(str(APP), default_timeout=90)
    app4.session_state["projet_courant"] = NOM
    app4.session_state["nav"] = "④ Validation"
    app4.run()
verifier("page ④ : aucune exception", not app4.exception)
avertissements = " ".join(str(w.value) for w in app4.warning)
verifier("page ④ : « À confirmer » : la ligne a changé depuis la décision, avec l'ancienne décision",
         "À confirmer" in avertissements and "Accepté tel quel" in avertissements and "Marie" in avertissements)
carte = [r for r in app4.radio if str(r.key).startswith("vdec_")]
verifier("page ④ : la carte est de nouveau « à décider »", carte and carte[0].value == "")

print("PAGE-MAJ:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
