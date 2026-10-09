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

# --- alias : cas réels de sur-fusion observés sur Nordval (non-régression) -----------------------------
for a_, b_ in (("Restauration test échouée (sauvegarde Sage X3)", "restauration"), ("Recrutement", "Recrutement / Formation (2)"),
               ("FleetTrack", "FleetTrack/WMS"), ("NAS 12 baies", "NAS 4 baies"), ("10 ans", "5 ans"),
               ("LogiSoft", "Départ du responsable infrastructure (M. Dubreuil)"), ("Client", "CleanNet Services")):
    verifier(f"jamais fusionnés : {a_[:30]} / {b_[:25]}", not alias.nom_compatible(a_, b_))
for a_, b_ in (("M. Dubreuil", "Marc Dubreuil"), ("OPSITEL", "OPSITEL - Infogérance Réseau"), ("WMS StockPilot", "WMS StockPilot (SaaS)"),
               ("Lesquin", "Lesquin (59)"), ("Veeam", "Veeam Backup")):
    verifier(f"fusionnés : {a_} / {b_}", alias.nom_compatible(a_, b_))
mêmes_vecteurs = [[1.0, 0.0]] * 6
canon2, _g = alias.fusionner([("NAS 12 baies", "materiel"), ("NAS 4 baies", "materiel"), ("DAF", "role"), ("DPO", "role"),
                              ("STP / LHV / LSQ", "site"), ("STP / LSQ", "site")], mêmes_vecteurs)
verifier("vecteurs identiques : nombres différents, noms courts et listes ne fusionnent pas", len(set(canon2.values())) == 6)
canon3, _g = alias.fusionner([("Contrôleur de domaine principal", "systeme"), ("Serveur contrôleur de domaine", "systeme")], [[1.0, 0.0], [1.0, 0.0]])
verifier("vecteurs identiques et noms longs de même type : fusion par vecteur", len(set(canon3.values())) == 1)
canon4, _g = alias.fusionner([("Serveur principal", "systeme"), ("Serveur central", "role")], [[1.0, 0.0], [1.0, 0.0]])
verifier("deux types précis différents : jamais fusionnés, même vecteur", len(set(canon4.values())) == 2)

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


signaux = contradictions.croiser(idx, juge=faux_juge, second_avis=False)
verifier("contradiction croisée trouvée entre deux documents", len(signaux) == 1 and {signaux[0].doc_a, signaux[0].doc_b} == {"audit.md", "pssi.md"})
verifier("paire dédoublonnée (A vs B = B vs A)", len(signaux) == 1)
verifier("un fait non vérifié n'est jamais confronté", all("inventé" not in s.extrait_a + s.extrait_b for s in signaux))
idx.fermer()

# --- vérification à deux vérificateurs et couverture « connu / partiel / inconnu » ---------------------------
from tools.connaissance import couverture, verification  # noqa: E402

verifier("accord des deux vérificateurs : soutenu", verification.verifier("doc", "x", verificateurs=[lambda d, a: True, lambda d, a: True]) == "soutenu")
verifier("désaccord : doute (jamais tranché par le code)", verification.verifier("doc", "x", verificateurs=[lambda d, a: True, lambda d, a: False]) == "doute")
verifier("accord négatif : non soutenu", verification.verifier("doc", "x", verificateurs=[lambda d, a: False, lambda d, a: False]) == "non_soutenu")

def evaluer_test(*args, **kwargs):
    """Les tests ne contactent JAMAIS un modèle : sans `contre` explicite, aucune contestation."""
    kwargs.setdefault("contre", lambda index_, preuves_: [])
    return couverture.evaluer(*args, **kwargs)


base = Index(":memory:")
base.ajouter_element("fait", "audit.md", "RSSI", "Le DSI cumule les fonctions de DSI et de RSSI", True, [1.0, 0.0])
base.ajouter_element("fait", "pra.md", "PRA", "Test de bascule réalisé le 17/06/2022 (partiel)", True, [0.0, 1.0])
besoin = couverture.Besoin("t1", "Gouvernance", "Qui est le RSSI ?")
oui = [lambda d, a: True, lambda d, a: True]
non = [lambda d, a: False, lambda d, a: False]


def juge_connu(b, c, m):
    return {"statut": "connu", "passages": [1], "reponse": "Le DSI cumule DSI et RSSI.", "manque": ""}


r = evaluer_test(base, besoin, [1.0, 0.0], juge=juge_connu, verificateurs=oui)
verifier("connu : réponse + preuve citée + vérifié, sans validation requise", r.statut == "connu" and len(r.preuves) == 1 and not r.a_valider)
r = evaluer_test(base, besoin, [1.0, 0.0], juge=lambda b, c, m: {"statut": "connu", "passages": [], "reponse": "invention", "manque": ""}, verificateurs=oui)
verifier("« connu » SANS preuve citée devient inconnu", r.statut == "inconnu" and r.a_valider and r.reponse == "")
r = evaluer_test(base, besoin, [1.0, 0.0], juge=lambda b, c, m: {"statut": "connu", "passages": [99], "reponse": "x", "manque": ""}, verificateurs=oui)
verifier("preuve citée hors liste (n°99) : inconnu", r.statut == "inconnu")
r = evaluer_test(base, besoin, [1.0, 0.0], juge=juge_connu, verificateurs=non)
verifier("réponse non soutenue par ses preuves : rétrogradée en partiel, à valider", r.statut == "partiel" and r.a_valider and "soutenue" in r.pourquoi)
r = evaluer_test(base, besoin, [1.0, 0.0], juge=juge_connu, verificateurs=[lambda d, a: True, lambda d, a: False])
verifier("vérificateurs en désaccord : à valider par un humain, avec le pourquoi", r.a_valider and "divergent" in r.pourquoi)
r = evaluer_test(base, besoin, [1.0, 0.0], juge=lambda b, c, m: {"statut": "partiel", "passages": [1], "reponse": "DSI = RSSI", "manque": "nom du RSSI"}, verificateurs=oui)
verifier("partiel : le manque est dit explicitement", r.statut == "partiel" and "nom du RSSI" in r.pourquoi)
r = evaluer_test(base, besoin, [1.0, 0.0], juge=lambda b, c, m: {"statut": "inconnu", "passages": [], "reponse": "", "manque": "Demander la PSSI"}, verificateurs=oui)
verifier("inconnu : jamais « n'existe pas », toujours « à demander »", r.statut == "inconnu" and "Ne pas en conclure" in r.pourquoi and r.manque == "Demander la PSSI")
vide = Index(":memory:")
r = evaluer_test(vide, besoin, [1.0, 0.0], juge=juge_connu, verificateurs=oui)
verifier("index vide : inconnu sans même appeler le juge", r.statut == "inconnu")
reps = [evaluer_test(base, besoin, [1.0, 0.0], juge=juge_connu, verificateurs=oui),
        evaluer_test(vide, couverture.Besoin("t2", "Sauvegardes", "Quand a eu lieu la dernière restauration ?"), [1.0, 0.0])]
questions = couverture.questions_ouvertes(reps)
verifier("questions ouvertes : seulement ce qui n'est pas établi", len(questions) == 1 and "NON DOCUMENTÉ" in questions[0])
rapport = couverture.rapport_markdown(reps, signaux)
verifier("rapport : sections savoir / ignorer / contradictions", all(s in rapport for s in ("Ce que nous savons", "Ce que nous ignorons encore", "Contradictions entre documents")))
verifier("rapport : précise que « non documenté » n'est pas « n'existe pas »", "ne prouve pas" in rapport)
signal = contradictions.Signal("pssi.md", "comptes désactivés sous 24 h", "audit.md", "9 comptes d'anciens salariés toujours actifs", "incompatibles")
r = evaluer_test(base, besoin, [1.0, 0.0], juge=juge_connu, verificateurs=oui, contre=lambda i, p: [signal])
verifier("réponse CONTESTÉE par un autre document : à valider, avec la source adverse", r.a_valider and "CONTESTÉ" in r.pourquoi and "9 comptes" in r.pourquoi and len(r.contestations) == 1)
verifier("une réponse contestée est signalée dans les questions ouvertes", "CONTESTÉ" in couverture.questions_ouvertes([r])[0])
verifier("le rapport marque la réponse contestée", "CONTESTÉ" in couverture.rapport_markdown([r]))
r = evaluer_test(base, besoin, [1.0, 0.0], juge=juge_connu, verificateurs=oui)
verifier("sans contestation, une réponse vérifiée reste sans validation requise", not r.a_valider and r.contestations == ())

verifier("besoins : identifiants uniques", len({b.id for b in couverture.BESOINS}) == len(couverture.BESOINS))

# --- passages : le texte d'origine comme filet de sécurité ----------------------------------------------------
from tools.connaissance import passages  # noqa: E402

TABLEAU = "# Budget\n| Équipement | Support |\n|---|---|\n" + "".join(f"| Commutateur {i} | hors support depuis 2023 |\n" for i in range(40))
morceaux = passages.decouper("budget.md", TABLEAU, taille=300)
verifier("passages : plusieurs blocs, aucun ne dépasse la taille (une ligne n'est jamais coupée)", len(morceaux) > 3 and all(len(m.texte) <= 330 for m in morceaux))
verifier("passages : chaque bloc est une sous-chaîne EXACTE du document", all(m.texte in TABLEAU for m in morceaux))
verifier("passages : titre et en-tête de tableau conservés comme contexte, hors du texte", all("Budget" in m.contexte and "Équipement" in m.contexte for m in morceaux[1:]))
verifier("passages : aucune ligne perdue", sum(m.texte.count("Commutateur") for m in morceaux) == 40)
verifier("passages : bruit (titre isolé) ignoré", passages.decouper("x.md", "# Titre seul") == [])

# --- en-tête technique d'ingestion, mots génériques, priorité ----------------------------------------------------
DOC_INGERE = ("# Extrait — a.docx\n\n- Source : `a.docx`\n- Taille : 3 octets\n\n<<<DONNÉES>>>\n\n## Sauvegardes\n"
              "Sauvegardes quotidiennes sur NAS local, avec réplication nocturne vers un second emplacement distant.\n\n<<<FIN DONNÉES>>>")
verifier("corps : l'en-tête technique est retiré, le texte utile intact", texte.corps(DOC_INGERE).startswith("## Sauvegardes") and "Source" not in texte.corps(DOC_INGERE))
verifier("corps : tranche contiguë du document (rien de reformulé)", texte.corps(DOC_INGERE) in DOC_INGERE)
verifier("passages : plus aucune trace de l'en-tête d'ingestion",
         all("Extrait" not in q.texte and "Source" not in q.texte for q in passages.decouper("a.md", DOC_INGERE, minimum=0)))
verifier("« Direction » ne s'aligne pas sur « Direction des Ressources Humaines »", not alias.nom_compatible("Direction", "Direction des Ressources Humaines"))
verifier("un nom précis garde son alias préfixe (« Veeam » ~ « Veeam Backup »)", alias.nom_compatible("Veeam", "Veeam Backup"))
contestee = evaluer_test(base, besoin, [1.0, 0.0], juge=juge_connu, verificateurs=oui, contre=lambda i, p: [signal])
partielle = evaluer_test(base, besoin, [1.0, 0.0], juge=lambda b, c, m: {"statut": "partiel", "passages": [1], "reponse": "x", "manque": "m"}, verificateurs=oui)
inconnue = evaluer_test(vide, besoin, [1.0, 0.0])
verifier("priorité : contesté > non documenté > partiel > rien",
         couverture.priorite(contestee) > couverture.priorite(inconnue) > couverture.priorite(partielle) > 0)
verifier("questions ouvertes : le plus important d'abord", couverture.questions_ouvertes([partielle, contestee, inconnue])[0].find("CONTESTÉ") >= 0)

# --- second avis : la priorité trie, elle ne supprime rien ---------------------------------------------------
s0 = contradictions.Signal("a.md", "Sage X3 externe", "b.md", "Sage X3 interne", "incompatibles")
verifier("signalement sans confirmation : priorité basse", s0.priorite == "basse")
s1 = contradictions.confirmer(s0, confirmation=lambda sig, modele: modele == "gemma4:12b")
verifier("un seul modèle confirme : priorité haute", s1.confirmations == 1 and s1.priorite == "haute")
s2 = contradictions.confirmer(s0, confirmation=lambda sig, modele: True)
verifier("deux modèles confirment : 2 confirmations", s2.confirmations == 2)
idx2 = Index(":memory:")
idx2.ajouter_element("fait", "audit.md", "DSI cumule", "Le DSI cumule les fonctions de DSI et de RSSI", True, [1.0, 0.0])
idx2.ajouter_element("fait", "pssi.md", "RSSI indépendant", "Le RSSI exerce ses fonctions de manière indépendante du DSI", True, [0.9, 0.1])
oui_juge = lambda fait, autres, modele: {"contradiction": True, "passage": 1, "explication": "incompatibles"}  # noqa: E731
tries = contradictions.croiser(idx2, juge=oui_juge, confirmation=lambda sig, m: m == "gemma4:12b")
verifier("croiser : tous les signalements sont conservés, les confirmés d'abord", len(tries) == 1 and tries[0].priorite == "haute")
verifier("croiser sans second avis : aucun tri ni appel de modèle", all(s.confirmations == 0 for s in contradictions.croiser(idx2, juge=oui_juge, second_avis=False)))
preuve = [{"id": 1, "doc": "audit.md", "extrait": "Le DSI cumule les fonctions de DSI et de RSSI"}]
verifier("contredit : un conflit NON confirmé ne rend pas une réponse « contestée »",
         contradictions.contredit(idx2, preuve, juge=oui_juge, confirmation=lambda sig, m: False) == [])
verifier("contredit : un conflit confirmé la rend contestée",
         len(contradictions.contredit(idx2, preuve, juge=oui_juge, confirmation=lambda sig, m: True)) == 1)
rapport2 = couverture.rapport_markdown([], [s2, s0])
verifier("rapport : priorité haute en tête, priorité basse repliée à part", "À relire si le temps le permet (1)" in rapport2 and rapport2.index("Sage X3 externe") < rapport2.index("À relire"))
idx2.fermer()

echecs = [(n, d) for n, ok, d in RESULTATS if not ok]
ignores = [n for n, ok, d in RESULTATS if ok and d.startswith("SKIP")]
for nom, ok, detail in RESULTATS:
    print(("PASS " if ok else "FAIL ") + nom + (f" ({detail})" if detail and not ok else ""))
print(f"CONNAISSANCE: {len(RESULTATS) - len(echecs)} PASS, {len(echecs)} FAIL, {len(ignores)} SKIP")
sys.exit(1 if echecs else 0)
