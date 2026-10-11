#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Intégration : la chaîne produit 01, 03, 04 et 05 PAR LOTS (faux agents, aucun modèle).

Vérifie le déroulé réel de `chaine.derouler` avec un index de connaissance : découpage, un appel d'agent par lot,
parties vérifiées, assemblage par le code, reprise ciblée sur les seuls lots concernés.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402
from web import chaine, controles, lib, lots  # noqa: E402

ECHECS: list[str] = []


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


NL = chr(10)


def table(nom: str, n: int = 8) -> str:
    return NL.join([f"# {nom}", "", "| Élément | Détail | Variante |", "|---|---|---|"] +
                   [f"| ligne {i} | description du composant {i} du système | a |" for i in range(1, n + 1)]) + NL


class Faux:
    """Faux agents : les étapes en une passe écrivent un livrable ; les lots écrivent leurs lignes."""

    def __init__(self, oublier: tuple[str, ...] = ()):
        self.appels: list[tuple[str, str]] = []   # (agent, message)
        self.oublier = oublier                      # identifiants volontairement oubliés (test de reprise)
        self.par_lot: list[str] = []

    def lancer(self, cli, agent, modele, message, pieces=None, pret=None):
        self.appels.append((agent, message))
        if agent == "e21-controle":
            return 0, "RESULTAT-CONTROLE: CONFORME"
        m_partie = re.search(r"analyses/[^ ]+/parties/([\w.-]+\.md)", message)
        if m_partie:
            nom = m_partie.group(1)
            self.par_lot.append(nom)
            entrees = next((p for p in (pieces or []) if "/lot-" in p.replace("\\", "/")), "")
            texte = Path(entrees if Path(entrees).is_absolute() else lib.RACINE / entrees).read_text(encoding="utf-8") if entrees else ""
            ids = re.findall(r"^- ([A-Z]\d{2,3})\b", texte, re.M)
            rows = []
            if nom.startswith("01-actifs"):
                noms = re.findall(r"^- (.+?) \(cité par", texte, re.M) or [f"Actif {nom} {k}" for k in range(1, 4)]
                rows = [f"| - | {n} | Logiciel / Service | desc [E1] | Interne | [E1] |" for n in noms]
            elif nom.startswith("03-menaces"):
                rows = [f"| - | {i} Actif | STRIDE-S | Menace réaliste [E1] | — | STRIDE-S |" for i in ids if i not in self.oublier] or \
                       ["| - | Frontière Internet → DMZ | STRIDE-S | Contournement [E1] | — | STRIDE-S |"]
            elif nom.startswith("04-evaluation"):
                rows = [f"| {i} | menace {i} | Moyenne | j [E1] | Élevé | j | Élevé | j |" for i in ids]
            elif nom.startswith("05-traitement"):
                rows = [f"| {i} | A01 | STRIDE-S {i} | Moyenne·Élevé·Élevé | Réduire | MFA | ISO27002-8.5 | Faible |" for i in ids]
            chemin = lib.RACINE / f"analyses/{m_partie.group(0).split('/')[1]}/parties/{nom}"
            chemin = lib.DOSSIER_ANALYSES / m_partie.group(0).split("/")[1] / "parties" / nom
            chemin.parent.mkdir(exist_ok=True)
            chemin.write_text(NL.join(rows) + NL, encoding="utf-8")
            return 0, ""
        for fichier in re.findall(r"analyses/[^ ,]+/([\w.-]+\.md)", message):
            if fichier in ("00-description.md", "02-methodes.md", "06-validation.md", "registre-risques.md", "SYNTHESE.md"):
                (self.dossier / fichier).write_text(table(fichier), encoding="utf-8")
        return 0, ""


racine = Path(tempfile.mkdtemp(prefix="e21-derlots-"))
lib.DOSSIER_ANALYSES = racine
dossier = racine / "2026-01-01_test"
(dossier / "intrants").mkdir(parents=True)
(dossier / "intrants" / "a.md.md").write_text("Site e-commerce hébergé sur un mutualisé. " * 20, encoding="utf-8")
(dossier / "connaissance").mkdir()
idx = Index(travail.chemins(dossier)[1])
idx.ajouter_element("passage", "a.md.md", "Section", "Le site e-commerce est hébergé sur un mutualisé.", True, [1.0, 0.0, 1.0])
ENTITES = [(f"Système {k}", "systeme") for k in range(1, 11)] + [("Données RH", "donnee"), ("FortiGate", "materiel"),
                                                                   ("Site Lesquin", "site"), ("OPSITEL", "prestataire")]
for nom, type_ in ENTITES:
    idx.ajouter_entite(nom, nom, type_, ["a.md.md", "b.md.md"])
idx.fermer()

faux = Faux()
faux.dossier = dossier
chaine._lancer_agent = faux.lancer
chaine.modeles_declares = lambda cli: set()
chaine.preparer_connaissance = lambda d, auto: True
chaine.fichier_de_preuves = lambda d, n: None
chaine.controle_citations = lambda d, f: ("", [])
chaine.ids_connus = lambda chemin=None: set()
chaine._VECTEURS = lambda textes, prefixe="": [[1.0, 0.0, 1.0] for _ in textes]
code = chaine.derouler("test", "2026-01-01_test", "ollama/x", "opencode")

actifs = lots.lire_lignes(dossier, "01-actifs.md")
menaces = lots.lire_lignes(dossier, "03-menaces.md")
evals = lots.lire_lignes(dossier, "04-evaluation.md")
traits = lots.lire_lignes(dossier, "05-traitement.md")
verifier("la chaîne aboutit (code 0)", code == 0)
verifier("01 : trois lots → 14 actifs, identifiants A01 à A14 posés par le code", [r[0] for r in actifs] == [f"A{n:02d}" for n in range(1, 15)])
verifier("01 : chaque partie est dans parties/", sorted(p.name for p in (dossier / "parties").glob("01-actifs.*.md")) == ["01-actifs.1.md", "01-actifs.2.md", "01-actifs.3.md"])
verifier("03 : 14 actifs = 3 lots (5 + 5 + 4) + le lot des frontières ; au moins une menace par actif",
         all(any(a[0] in " ".join(m) for m in menaces) for a in actifs) and any("Frontière" in " ".join(m) for m in menaces))
verifier("03 : identifiants de menaces M01… posés par le code", [r[0] for r in menaces][:3] == ["M01", "M02", "M03"])
verifier("04 : une évaluation par menace, identifiants repris", sorted(r[0] for r in evals) == sorted(r[0] for r in menaces) and len(evals) >= 14)
verifier("05 : un traitement par risque évalué", sorted(r[0] for r in traits) == sorted(r[0] for r in evals))
parties_vues = faux.par_lot
verifier("un appel d'agent par lot (et non un appel par livrable)", len([p for p in parties_vues if p.startswith("01-actifs")]) == 3
         and len([p for p in parties_vues if p.startswith("03-menaces")]) == 4)
verifier("livrables non découpés (00, 02, 06, registre, synthèse) toujours produits en une passe",
         all((dossier / f).is_file() for f in ("00-description.md", "02-methodes.md", "06-validation.md", "registre-risques.md", "SYNTHESE.md")))
verifier("contrôles numérotés enregistrés pour les 7 étapes", len({str(e["etape"]) for e in controles.lire(dossier)}) >= 7)
verifier("le livrable assemblé porte l'en-tête du programme", (dossier / "03-menaces.md").read_text(encoding="utf-8").startswith("# Menaces (étape 3)"))

# --- reprise ciblée : un lot oublie un actif, seul ce lot est refait -------------------------------------------------------------------
faux2 = Faux(oublier=("A07",))
faux2.dossier = dossier
chaine._lancer_agent = faux2.lancer
# on repart d'un état propre pour l'étape 3 : parties de 03 supprimées
for p in (dossier / "parties").glob("03-menaces.*.md"):
    p.unlink()
liste = lots.plan_etape(dossier, 3, None)["03-menaces.md"]
n = chaine.produire_par_lots("opencode", "e21-menaces", dossier, "2026-01-01_test", 3, "03-menaces.md", liste, auto=False, installes=set(),
                             defaut="ollama/x", modele_impose="ollama/x", corrections="", index_chemin=travail.chemins(dossier)[1])
verifier("production initiale : tous les lots refaits", n == len(liste))
avant = len(faux2.par_lot)
faux2.oublier = ()
n2 = chaine.produire_par_lots("opencode", "e21-menaces", dossier, "2026-01-01_test", 3, "03-menaces.md", liste, auto=False, installes=set(),
                              defaut="ollama/x", modele_impose="ollama/x", corrections="A07 : aucune menace décrite pour cet actif",
                              index_chemin=travail.chemins(dossier)[1])
verifier("reprise ciblée : un seul lot refait (celui de A07, le deuxième)", n2 == 1 and faux2.par_lot[avant:] == ["03-menaces.2.md"])
verifier("reprise ciblée : l'actif oublié a maintenant sa menace", any("A07" in " ".join(m) for m in lots.lire_lignes(dossier, "03-menaces.md")))
n3 = chaine.produire_par_lots("opencode", "e21-menaces", dossier, "2026-01-01_test", 3, "03-menaces.md", liste, auto=False, installes=set(),
                              defaut="ollama/x", modele_impose="ollama/x", corrections="remarque générale sans identifiant",
                              index_chemin=travail.chemins(dossier)[1])
verifier("corrections sans identifiant : aucun lot refait (confié à l'analyste)", n3 == 0)

print("DEROULER-LOTS:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
