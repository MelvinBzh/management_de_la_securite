#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes du paquet `tools.connaissance` (aucun réseau, aucun modèle).

    python3 tools/connaissance/tests/test_connaissance.py

Sortie `CONNAISSANCE: N PASS, M FAIL` ; code de retour 0 si aucun FAIL.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import alias, contradictions, ollama, relations, texte  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402

RESULTATS: list[tuple[str, bool, str]] = []


def verifier(nom: str, condition: bool, detail: str = "") -> None:
    RESULTATS.append((nom, bool(condition), detail))


# --- texte : l'extrait exact, pierre angulaire -------------------------------------------------
DOC = texte.normaliser("| Compte | État |\n| adm.mdb | Actif, dernière connexion le 19/06/2026 |")
verifier("extrait exact retrouvé malgré le tableau", texte.contient("adm.mdb Actif, dernière connexion", DOC))
verifier("extrait inventé refusé", not texte.contient("adm.mdb est désactivé", DOC))
verifier("extrait vide refusé", not texte.contient("   ", DOC))
verifier("nom entier présent", texte.nom_present("adm.mdb", DOC))
verifier("nom composite toléré (75 % des mots présents)", texte.nom_present("Compte adm.mdb administrateur", DOC))
verifier("nom étranger au document refusé", not texte.nom_present("Cloudflare WAF", DOC))

# --- alias -------------------------------------------------------------------------------------
verifier("initiale + nom de famille", alias.nom_compatible("K. Benali", "Karim Benali"))
verifier("sigle entre parenthèses", alias.nom_compatible("Saint-Priest (STP)", "Saint-Priest"))
verifier("deux personnes différentes non fusionnées", not alias.nom_compatible("Julien Roussel", "Karim Benali"))
canon, groupes = alias.fusionner([("K. Benali", "personne"), ("Karim Benali", "personne"), ("Karim Benali", "personne"),
                                  ("Sage", "prestataire"), ("Sage X3", "systeme")])
verifier("variantes d'une personne fusionnées, nom le plus fréquent retenu",
         canon[texte.normaliser("K. Benali")] == "Karim Benali" and any(len(g) == 2 for g in groupes))
verifier("types différents non fusionnés (éditeur vs logiciel)",
         canon[texte.normaliser("Sage")] != canon[texte.normaliser("Sage X3")])

# --- vecteurs ----------------------------------------------------------------------------------
verifier("cosinus de vecteurs identiques", abs(ollama.cosinus([1, 2, 3], [1, 2, 3]) - 1.0) < 1e-9)
verifier("cosinus de vecteurs orthogonaux", ollama.cosinus([1, 0], [0, 1]) == 0.0)
verifier("cosinus de vecteur nul sans erreur", ollama.cosinus([0, 0], [1, 1]) == 0.0)

# --- relations : vérification par le code ---------------------------------------------------------
contenu = texte.normaliser("OPSITEL administre le firewall FortiGate du site de Lesquin depuis 2019.")
bonne = relations.Relation("d.md", "OPSITEL", "administre", "FortiGate", "OPSITEL administre le firewall FortiGate", False)
inventee = relations.Relation("d.md", "OPSITEL", "administre", "FortiGate", "OPSITEL supervise aussi le WAF Cloudflare", False)
etrangere = relations.Relation("d.md", "Cloudflare", "administre", "FortiGate", "OPSITEL administre le firewall FortiGate", False)
verifier("relation fondée acceptée", relations.verifier(bonne, contenu))
verifier("relation à extrait inventé refusée", not relations.verifier(inventee, contenu))
verifier("relation à entité étrangère refusée", not relations.verifier(etrangere, contenu))

# --- index : recherche hybride -------------------------------------------------------------------
index = Index(":memory:")
a = index.ajouter_element("fait", "d1.md", "OPSITEL administre FortiGate", "OPSITEL administre le firewall FortiGate", True, [1.0, 0.0, 0.0])
b = index.ajouter_element("fait", "d2.md", "Sauvegarde NAS", "Le NAS Veeam est la seule copie hors production", True, [0.0, 1.0, 0.0])
c = index.ajouter_element("fait", "d3.md", "Fait non vérifié", "extrait inventé sur un NAS", False, [0.0, 0.9, 0.1])
vecteur_nas = [0.0, 1.0, 0.0]
trouves = index.rechercher("quelle est la sauvegarde NAS ?", vecteur_nas, k=3)
verifier("recherche hybride : la bonne preuve en tête", trouves and trouves[0]["id"] == b)
verifier("un fait non vérifié n'est jamais renvoyé", all(t["id"] != c for t in trouves))
verifier("recherche par vecteurs seuls", index.rechercher("zzz", vecteur_nas, k=1, mots_cles=False)[0]["id"] == b)
if index.fts:
    verifier("recherche par mots-clés seuls (FTS5)", index.rechercher("firewall FortiGate", None, k=1)[0]["id"] == a)
else:
    RESULTATS.append(("recherche par mots-clés seuls (FTS5)", True, "SKIP : FTS5 absent de cette build SQLite"))
index.ajouter_entite("K. Benali", "Karim Benali", "personne", ["d1.md", "d1.md"])
index.ajouter_contradiction("FortiGate", "d1.md", "x", "d2.md", "y", "contradiction", "test")
verifier("comptes de l'index", index.compter() == {"elements": 3, "entites": 1, "contradictions": 1})
index.fermer()

# --- contradictions : les candidats ----------------------------------------------------------------
r1 = relations.Relation("d1.md", "Compte adm.mdb", "acces_a", "AD", "adm.mdb désactivé", True)
r2 = relations.Relation("d2.md", "Compte adm.mdb", "acces_a", "AD", "adm.mdb actif dernière connexion 2026", True)
r3 = relations.Relation("d2.md", "Autre", "acces_a", "AD", "sans rapport", True)
r4 = relations.Relation("d3.md", "Compte adm.mdb", "acces_a", "AD", "adm.mdb désactivé", False)  # non vérifiée
paires = contradictions.candidats([r1, r2, r3, r4], {}, [[1.0, 0.2], [0.9, 0.5], [0.0, 1.0], [1.0, 0.2]])
verifier("paire de documents différents sur la même entité proposée", len(paires) == 1 and paires[0].entite == "Compte adm.mdb")
verifier("les relations non vérifiées n'entrent jamais", all(not (p.a is r4 or p.b is r4) for p in paires))
verifier("même document : aucune paire", contradictions.candidats([r1, r1], {}, [[1, 0], [1, 0]]) == [])

# --- contradictions : recherche croisée (juge simulé) ------------------------------------------------
verifier("faux positif évident écarté", contradictions.est_faux_positif("Les deux sont cohérents, pas de problème"))
verifier("« incompatibles » n'est PAS pris pour « compatible »", not contradictions.est_faux_positif("Les extraits sont incompatibles."))
verifier("« incohérent » n'est PAS pris pour « cohérent »", not contradictions.est_faux_positif("Le statut est incohérent entre les deux documents."))
verifier("explication mixte avec conflit nommé conservée", not contradictions.est_faux_positif("Ce point est cohérent. Cependant, la contradiction majeure porte sur la date."))
verifier("« ne contredit pas » écarté", contradictions.est_faux_positif("Le passage ne contredit pas le fait."))
verifier("vraie contradiction conservée", not contradictions.est_faux_positif("Le fait dit actif, le passage dit parti"))
idx = Index(":memory:")
idx.ajouter_element("fait", "audit.md", "DSI cumule", "Le DSI cumule les fonctions de DSI et de RSSI", True, [1.0, 0.0])
idx.ajouter_element("fait", "pssi.md", "RSSI indépendant", "Le RSSI exerce ses fonctions de manière indépendante du DSI", True, [0.9, 0.1])
idx.ajouter_element("fait", "pssi.md", "Comité", "Un comité de sécurité se réunit chaque trimestre", True, [0.0, 1.0])
idx.ajouter_element("fait", "faux.md", "Non vérifié", "extrait inventé", False, [1.0, 0.0])


def faux_juge(fait, autres, modele):
    pertinents = [i for i, c in enumerate(autres, 1)
                  if {fait["doc"], c["doc"]} == {"audit.md", "pssi.md"} and "comité" not in fait["extrait"] + c["extrait"]]
    return {"contradiction": bool(pertinents), "passage": pertinents[0] if pertinents else 0, "explication": "incompatibles"}


signaux = contradictions.croiser(idx, juge=faux_juge)
verifier("contradiction croisée trouvée entre deux documents", len(signaux) == 1 and {signaux[0].doc_a, signaux[0].doc_b} == {"audit.md", "pssi.md"})
verifier("paire dédoublonnée (A vs B = B vs A)", len(signaux) == 1)
verifier("un fait non vérifié n'est jamais confronté", all("inventé" not in s.extrait_a + s.extrait_b for s in signaux))
idx.fermer()

echecs = [(n, d) for n, ok, d in RESULTATS if not ok]
ignores = [n for n, ok, d in RESULTATS if ok and d.startswith("SKIP")]
for nom, ok, detail in RESULTATS:
    print(("PASS " if ok else "FAIL ") + nom + (f" ({detail})" if detail and not ok else ""))
print(f"CONNAISSANCE: {len(RESULTATS) - len(echecs)} PASS, {len(echecs)} FAIL, {len(ignores)} SKIP")
sys.exit(1 if echecs else 0)
