#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes des dossiers de preuves et des citations (`preuves`, `citations`) — aucun modèle contacté.

    python3 tools/connaissance/tests/test_preuves.py
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import citations, couverture, preuves, verification  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402

RESULTATS: list[tuple[str, bool, str]] = []


def verifier(nom: str, condition: bool, detail: str = "") -> None:
    RESULTATS.append((nom, bool(condition), detail))


def faux_vecteurs(textes, prefixe: str = ""):
    return [[float(len(t) % 7), float(len(t) % 5), 1.0] for t in textes]


index = Index(":memory:")
e1 = index.ajouter_element("fait", "inventaire.md", "Le site est en PHP", "Le site e-commerce est développé en PHP 7.4 sur un hébergement mutualisé", True, faux_vecteurs(["a"])[0])
e2 = index.ajouter_element("fait", "audit.md", "Les sauvegardes ne sont pas testées", "Aucune restauration de sauvegarde n'a été testée depuis 2024", True, faux_vecteurs(["b"])[0])
e3 = index.ajouter_element("passage", "pssi.md", "Comptes", "Les comptes des personnes parties sont désactivés sous 24 h", True, faux_vecteurs(["c"])[0])
index.enregistrer_couverture("cont-sauv", {"besoin": "cont-sauv", "theme": "Continuité", "question": "Comment sont réalisées les sauvegardes ?",
                                           "statut": "connu", "reponse": "Sauvegardes nocturnes non testées.", "preuves": [{"id": e2, "doc": "audit.md", "extrait": "x"}],
                                           "contestations": [], "manque": "", "a_valider": False, "pourquoi": "", "verification": "soutenu", "priorite": 0})
index.enregistrer_couverture("cont-restau", {"besoin": "cont-restau", "theme": "Continuité", "question": "Quand a eu lieu la dernière restauration ?",
                                             "statut": "inconnu", "reponse": "", "preuves": [], "contestations": [], "manque": "Journal de restauration",
                                             "a_valider": True, "pourquoi": "Aucune preuve.", "verification": "sans_objet", "priorite": 3})
index.ajouter_contradiction("", "pssi.md", "Comptes désactivés sous 24 h", "audit.md", "Des comptes de départs sont restés actifs", "contradiction", "incompatibles", 1)

# --- dossier de preuves (v2 : passages d'origine avec leur en-tête, écarts, décisions, questions) --------------------------------
import json as _json, tempfile as _tf  # noqa: E402
pb = index.ajouter_element("passage", "budget.md", "Budget_SI_2026 · | Poste | Budget (k€) | Réalisé (k€) |",
                           "| Postes de travail / terminaux radio | 95 | 40 | Renouvellement reporté |", True, faux_vecteurs(["z"])[0])
pi = index.ajouter_element("passage", "inventaire.md", "Matériel · | Type | Quantité |", "| Postes fixes | 172 |" + chr(10) + "| Ordinateurs portables | 126 |",
                           True, faux_vecteurs(["y"])[0])
dossier_projet = Path(_tf.mkdtemp(prefix="e21-prev-"))
(dossier_projet / "validations.json").write_text(_json.dumps({"decisions": {"x": {
    "type": "contradiction", "decision": "source_b", "titre": "COMEX ≠ rapport financier", "libelle_decision": "Garder la valeur de : rapport financier",
    "commentaire": "Le rapport financier est audité"}}}), encoding="utf-8")
texte = preuves.dossier_de_preuves(index, 3, vecteurs=faux_vecteurs, dossier=dossier_projet)
verifier("règles de lecture en tête : remplace les documents, en-tête de colonne, deux valeurs en cas d'écart",
         "REMPLACE la lecture" in texte and "en-tête de sa colonne" in texte and "LES DEUX valeurs" in texte and "ne tranche pas seul" in texte)
verifier("un passage porte son identifiant citable", f"`[E{pi}]`" in texte and f"`[E{pb}]`" in texte)
verifier("la ligne de tableau arrive AVEC son en-tête de colonnes (95 = budget en k€)", "Budget (k€)" in texte and "| Postes de travail / terminaux radio | 95 |" in texte)
verifier("les lignes d'inventaire (172, 126) sont reproduites", "172" in texte and "126" in texte)
verifier("aucune « réponse » de couverture n'est présentée comme un fait", "Sauvegardes nocturnes non testées." not in texte)
verifier("les questions sans réponse sont des QUESTIONS (jamais comblées)", "sans réponse dans les documents" in texte and "dernière restauration" in texte)
verifier("les écarts confirmés sont rappelés avec les deux extraits", "Écarts entre documents" in texte and "24 h" in texte and "Des comptes de départs sont restés actifs" in texte)
verifier("les contradictions non confirmées ne sont pas rappelées", "faible aussi" not in texte)
verifier("la décision de l'analyste sur un écart passe en tête, à appliquer", "À APPLIQUER" in texte and "Garder la valeur de : rapport financier" in texte
         and texte.index("À APPLIQUER") < texte.index("## Document"))
verifier("documents présentés par nom, dans l'ordre", texte.index("budget.md") < texte.index("inventaire.md") < texte.index("pssi.md"))
verifier("les étapes ont des questions différentes", preuves.REQUETES[1] != preuves.REQUETES[3] and set(preuves.REQUETES) == set(range(1, 8)))
# budget : beaucoup de passages, seuls les plus pertinents entrent, et on le dit
for i in range(80):
    index.ajouter_element("passage", f"gros-{i % 4}.md", f"Section {i}", ("Texte de passage " + str(i) + ". ") * 45, True, [float(i % 7), float(i % 5), 1.0])
petit = preuves.dossier_de_preuves(index, 1, vecteurs=faux_vecteurs, budget=9000)
verifier("le budget borne la taille", len(petit) <= 9000 + 3000 and "REMPLACE la lecture" in petit)
verifier("les passages non reproduits sont signalés (rien n'est perdu)", "ne sont pas reproduits" in petit)
verifier("étape inconnue : questions de la synthèse", "Dossier de preuves" in preuves.dossier_de_preuves(index, 99, vecteurs=faux_vecteurs))

# écarts chiffrés d'abord, jusqu'à MAX_ECARTS
idx3 = Index(":memory:")
idx3.ajouter_contradiction("", "a.md", "Texte sans chiffre", "b.md", "Autre texte sans chiffre", "c", "x", 2)
idx3.ajouter_contradiction("", "comex.md", "CA 2025 : 46,8 M€", "readme.md", "CA 2025 : 47,2 M€", "c", "x", 1)
for i in range(30):
    idx3.ajouter_contradiction("", f"d{i}.md", f"valeur {i}", f"e{i}.md", f"valeur {i + 1}", "c", "x", 1)
t3 = preuves.dossier_de_preuves(idx3, 1, vecteurs=faux_vecteurs)
verifier("écarts : le chiffré (CA 46,8 / 47,2) passe avant le textuel même plus confirmé", t3.index("46,8") < t3.index("Texte sans chiffre") if "Texte sans chiffre" in t3 else "46,8" in t3)
verifier("écarts : au plus 20 rappelés", t3.count("**≠**") <= preuves.MAX_ECARTS)
verifier("étape 1 : budget plus large que les autres, sous la limite des pièces jointes", preuves.BUDGET_ETAPE_1 > preuves.BUDGET_OCTETS and preuves.BUDGET_ETAPE_1 < 40000)

# --- citations ----------------------------------------------------------------------------------------------
doc = ("# Actifs\n\n| Actif | Description |\n|---|---|\n"
       f"| Site | Développé en PHP 7.4 [E{e1}] |\n"
       f"| Sauvegardes | Restaurées chaque semaine [E{e2}] |\n"
       "| ERP | Hébergé chez un prestataire |\n"
       "| CRM | Cloud [E9999] |\n")
verifier("identifiants cités lus dans l'ordre", citations.ids_cites(doc) == [e1, e2, 9999])
verifier("la forme `[E12]` (code Markdown) est aussi reconnue", citations.ids_cites("x `[E5]` y") == [5])
accord = (lambda d, a: True, lambda d, a: True)
desaccord = (lambda d, a: True, lambda d, a: False)
rejet = (lambda d, a: False, lambda d, a: False)
mot_commun = (lambda d, a: "PHP" in d or "php" in d.lower(), lambda d, a: "PHP" in d or "php" in d.lower())
r = citations.analyser(doc, index, exiger=True, verificateurs=mot_commun)
verifier("citation inexistante détectée par le code", r["inexistantes"] == [9999])
verifier("ligne sans citation comptée", len(r["non_cite"]) == 1 and "ERP" in r["non_cite"][0])
verifier("ligne non soutenue par sa preuve : rejetée par les deux vérificateurs", len(r["non_soutenues"]) == 1 and "Sauvegardes" in r["non_soutenues"][0])
verifier("ligne soutenue : acceptée", r["verifiees"] == 2 and not any("PHP" in l for l in r["non_soutenues"] + r["doutes"]))
rd = citations.analyser(doc, index, verificateurs=desaccord)
verifier("désaccord des deux vérificateurs = doute (validation humaine), pas rejet", len(rd["doutes"]) == 2 and not rd["non_soutenues"])
c = citations.corrections("01-actifs.md", r, exiger=True)
verifier("corrections : citation inexistante (code), PAS de reprise pour une ligne non soutenue", "[E9999]" in c and "ne soutient PAS" not in c)
cb = citations.corrections("01-actifs.md", r, exiger=True, bloquer_non_soutenues=True)
verifier("corrections : reprise sur ligne non soutenue possible si demandée", "ne soutient PAS" in cb)
verifier("lignes non soutenues et en doute : à relire par un humain", any(l.startswith("[non soutenue]") and "Sauvegardes" in l for l in citations.a_relire(r)))
pauvre = doc + "| A | sans preuve |" + chr(10) + "| B | sans preuve |" + chr(10)
rp = citations.analyser(pauvre, index, exiger=True, verificateurs=mot_commun)
verifier("corrections : trop de lignes sans preuve citée", "sans preuve citée" in citations.corrections("01-actifs.md", rp, exiger=True))
propre = "| Actif | D |" + chr(10) + "|---|---|" + chr(10) + f"| Site | PHP [E{e1}] |" + chr(10)
verifier("les lignes en doute ne produisent PAS de correction automatique", citations.corrections("x.md", citations.analyser(propre, index, verificateurs=desaccord)) == "")
verifier("sans exigence, une ligne non citée n'est pas reprochée", citations.analyser(doc, index, exiger=False, verificateurs=accord)["non_cite"] == [])
verifier("part citée calculée", abs(r["part_citee"] - 0.75) < 1e-9)
verifier("affirmation vérifiée : seule la cellule qui cite sa preuve (les jugements ne sont pas vérifiés)", citations.affirmation(f"| Site | PHP [E{e1}] | Élevée | Grave |") == "PHP")
verifier("affirmation : ligne sans citation de cellule = toute la ligne", citations.affirmation("| A | B |") == "A ; B")
verifier("`limite` borne le nombre de lignes vérifiées", citations.analyser(doc, index, verificateurs=accord, limite=1)["verifiees"] == 1)

# --- affichage ------------------------------------------------------------------------------------------------
details = citations.extraits(index, [e1, e2])
html = citations.pour_affichage(doc + "\n<script>alert(1)</script>\n> citation", details)
verifier("les citations deviennent des notes numérotées avec infobulle", "<sup title=" in html and "[1]" in html and "[2]" in html and "PHP 7.4" in html)
verifier("les preuves sont repliées en bas", "<details><summary>Preuves citées (2)" in html)
verifier("une citation inconnue s'affiche [?]", "[?]" in html)
verifier("aucun HTML venu du livrable n'est rendu", "<script>" not in html and "&lt;script>" in html)
verifier("les citations Markdown (>) restent utilisables", "\n> citation" in html)
verifier("sans citation, le texte est inchangé (hors échappement)", citations.pour_affichage("Bonjour", {}) == "Bonjour")

echecs = [(n, d) for n, ok, d in RESULTATS if not ok]
for nom, ok, detail in RESULTATS:
    print(("PASS " if ok else "FAIL ") + nom + (f" ({detail})" if detail and not ok else ""))
print(f"PREUVES: {len(RESULTATS) - len(echecs)} PASS, {len(echecs)} FAIL")
sys.exit(1 if echecs else 0)
