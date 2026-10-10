#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test d'intégration du pilote (`chaine.derouler`) avec de FAUX agents : aucun opencode, aucun modèle.

On vérifie le déroulé complet : étapes, contrôles numérotés, reprises avec corrections, validation humaine, relecture finale,
code de sortie. Les agents sont scriptés : ils écrivent des livrables valides et répondent ce que le test décide.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from web import chaine, controles, lib  # noqa: E402

ECHECS: list[str] = []


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


NL = chr(10)


def livrable(nom: str, variante: str = "a") -> str:
    lignes = [f"# {nom}", "", "| Élément | Détail | Variante |", "|---|---|---|"]
    lignes += [f"| ligne {i} | description du composant numéro {i} du système | {variante} |" for i in range(1, 9)]
    return NL.join(lignes) + NL


class Scenario:
    """Faux agents : écrivent les livrables demandés, répondent aux contrôles selon un script."""

    def __init__(self, controles_par_etape: dict | None = None, finale: list | None = None):
        self.script = {k: list(v) for k, v in (controles_par_etape or {}).items()}
        self.finale = list(finale or [])
        self.messages_etapes: list[tuple[str, str]] = []
        self.versions: dict[str, int] = {}

    def lancer(self, cli, agent, modele, message, pieces=None, pret=None):
        if agent != "e21-controle":
            self.messages_etapes.append((agent, message))
            for chemin in re.findall(r"analyses/[^ ,.]+/([\w.\-]+\.md)", message):
                if chemin in ("06-validation.md", "registre-risques.md", "SYNTHESE.md") or chemin[:2].isdigit():
                    self.versions[chemin] = self.versions.get(chemin, 0) + 1
                    (self.dossier / chemin).write_text(livrable(chemin, f"v{self.versions[chemin]}"), encoding="utf-8")
            return 0, ""
        if message.startswith("Relecture finale"):
            return 0, (self.finale.pop(0) if self.finale else "RESULTAT-CONTROLE: CONFORME")
        numero = int(re.search(r"Étape (\d)", message).group(1))
        suite = self.script.get(numero)
        return 0, (suite.pop(0) if suite else "RESULTAT-CONTROLE: CONFORME")


def derouler(scenario: Scenario) -> tuple[int, Path]:
    racine = Path(tempfile.mkdtemp(prefix="e21-derouler-"))
    lib.DOSSIER_ANALYSES = racine
    dossier = racine / "2026-01-01_test"
    (dossier / "intrants").mkdir(parents=True)
    (dossier / "intrants" / "a.md.md").write_text("Site e-commerce PHP hébergé sur un mutualisé. " * 20, encoding="utf-8")
    scenario.dossier = dossier
    chaine._lancer_agent = scenario.lancer
    chaine.modeles_declares = lambda cli: set()
    chaine.preparer_connaissance = lambda d, auto: False  # la connaissance est testée ailleurs
    chaine.ids_connus = lambda chemin=None: set()
    code = chaine.derouler("test", "2026-01-01_test", "ollama/x", "opencode")
    return code, dossier


# --- 1. tout est conforme ---------------------------------------------------------------------------------------
code, d = derouler(Scenario())
entrees = controles.lire(d)
verifier("tout conforme : code de sortie 0", code == 0)
verifier("8 contrôles numérotés 1 à 8 (7 étapes + relecture finale)", [e["numero"] for e in entrees] == list(range(1, 9)))
verifier("tous conformes, rien à valider", all(e["verdict"] == "conforme" for e in entrees) and controles.a_valider(d) == [])
verifier("le rapport lisible existe et nomme chaque étape", all(f"Étape {n}" in (d / "RAPPORT-CONTROLE.md").read_text(encoding="utf-8") for n in range(1, 8)))

# --- 2. non conforme puis reprise avec corrections, puis conforme ------------------------------------------------------
s2 = Scenario({3: ["RESULTAT-CONTROLE: NON CONFORME" + NL + "1. la ligne 4 cite un composant absent des intrants"]})
code, d = derouler(s2)
e3 = [e for e in controles.lire(d) if str(e["etape"]) == "3"]
verifier("reprise : deux contrôles pour l'étape 3, versions 1 et 2", [(e["version"], e["verdict"]) for e in e3] == [(1, "non_conforme"), (2, "conforme")])
verifier("reprise : les corrections sont redonnées à l'agent", any("composant absent des intrants" in m for a, m in s2.messages_etapes if a == "e21-menaces"))
verifier("reprise : « ce qui a changé » décrit la différence entre versions", "ligne(s)" in e3[1]["changements"] and "Première version" in e3[0]["changements"])
verifier("reprise réussie : code 0 et rien à valider", code == 0 and controles.a_valider(d) == [])

# --- 3. verdict illisible trois fois : validation humaine expliquée -----------------------------------------------------
s3 = Scenario({2: ["je ne sais pas", "peut-être", "hmm"]})
code, d = derouler(s3)
att = controles.a_valider(d)
verifier("illisible : code 2 (terminé avec validation humaine)", code == 2)
verifier("illisible : l'étape 2 nécessite une validation humaine, avec pourquoi et quoi vérifier",
         len(att) == 1 and str(att[0]["etape"]) == "2" and "verdict exploitable" in att[0]["humaine"]["pourquoi"] and "02-methodes.md" in att[0]["humaine"]["quoi"])
verifier("illisible : jamais le mot « indéterminé » dans le rapport", "indéterminé" not in (d / "RAPPORT-CONTROLE.md").read_text(encoding="utf-8").lower())

# --- 4. toujours non conforme après les reprises --------------------------------------------------------------------------
nc = "RESULTAT-CONTROLE: NON CONFORME" + NL + "1. fait inventé : un pare-feu applicatif"
s4 = Scenario({4: [nc, nc, nc]})
code, d = derouler(s4)
e4 = [e for e in controles.lire(d) if str(e["etape"]) == "4"]
att = controles.a_valider(d)
verifier("reprises épuisées : 3 contrôles pour l'étape 4", len(e4) == 3 and [e["version"] for e in e4] == [1, 2, 3])
verifier("reprises épuisées : validation humaine, le point signalé est cité", code == 2 and len(att) == 1 and "pare-feu applicatif" in att[0]["humaine"]["pourquoi"])
verifier("l'étape suivante est tout de même exécutée (la chaîne continue)", any(a == "e21-traitement" for a, _m in s4.messages_etapes))

# --- 5. relecture finale non conforme ----------------------------------------------------------------------------------------
s5 = Scenario(finale=["RESULTAT-CONTROLE: NON CONFORME" + NL + "1. la synthèse cite un DPO absent des intrants"])
code, d = derouler(s5)
att = controles.a_valider(d)
verifier("relecture finale non conforme : code 2 et validation humaine « finale »", code == 2 and any(str(a["etape"]) == "finale" for a in att))

print("DEROULER:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
