#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de la mise à jour incrémentale (`ingestion`, `travail`) — aucun réseau, aucun modèle.

    python3 tools/connaissance/tests/test_ingestion.py

Les « moteurs » (extraction, vecteurs, croisement, couverture) sont remplacés par de faux moteurs qui comptent
leurs appels : on vérifie CE QUI EST RETRAITÉ, pas la qualité des modèles (mesurée ailleurs).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import contradictions, couverture, fiches, ingestion, relations, travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402

RESULTATS: list[tuple[str, bool, str]] = []


def verifier(nom: str, condition: bool, detail: str = "") -> None:
    RESULTATS.append((nom, bool(condition), detail))


def document(sujet: str, *lignes: str) -> str:
    """Document d'au moins 300 caractères (sous ce seuil, l'ingestion l'ignore comme du bruit)."""
    corps = "\n".join(lignes) + "\n" + ("Texte de remplissage sans importance pour le test. " * 8)
    return f"# {sujet}\n\n{corps}\n"


class Faux:
    """Faux moteurs qui comptent leurs appels."""

    def __init__(self, echec: set[str] | None = None, conflit: bool = False):
        self.faits, self.rels, self.vecs, self.croisements, self.evaluations = [], [], 0, [], 0
        self.echec, self.conflit = echec or set(), conflit

    def extraire_faits(self, nom: str, contenu: str):
        self.faits.append(nom)
        if nom in self.echec:
            raise RuntimeError("modèle indisponible")
        lignes = [l for l in contenu.splitlines() if l.startswith("Fait")]
        return [fiches.Fait(nom, "Le document dit : " + l, l, True) for l in lignes] + [fiches.Fait(nom, "Un fait inventé sans preuve", "absent du texte", False)]

    def extraire_relations(self, nom: str, contenu: str):
        self.rels.append(nom)
        ligne = next((l for l in contenu.splitlines() if l.startswith("Fait")), "Fait x")
        return ([relations.Entite(nom, "K. Benali", "personne")],
                [relations.Relation(nom, "K. Benali", "administre", "ERP", ligne, True)])

    def vecteurs(self, textes, prefixe: str = "search_document: "):
        self.vecs += len(textes)
        return [[float(len(t) % 7), float(len(t) % 5), 1.0] for t in textes]

    def croiser(self, index, *, seulement_docs=None, progression=None, **_):
        self.croisements.append(None if seulement_docs is None else set(seulement_docs))
        if progression:
            progression(1, 1)
        if not self.conflit:
            return []
        return [contradictions.Signal("a.md", "Fait A", "b.md", "Fait B", "Les deux sont incompatibles.", 1)]

    def evaluer(self, index, besoin, vecteur=None, **_):
        self.evaluations += 1
        return couverture.Reponse(besoin, couverture.INCONNU, "", (), "à demander", "sans_objet", True, "Aucune preuve.")

    def moteurs(self) -> ingestion.Moteurs:
        return ingestion.Moteurs(self.extraire_faits, self.extraire_relations, self.vecteurs, self.croiser, self.evaluer)


def projet(documents: dict[str, str]) -> Path:
    racine = Path(tempfile.mkdtemp(prefix="e21-conn-"))
    (racine / "intrants").mkdir()
    for nom, contenu in documents.items():
        (racine / "intrants" / nom).write_text(contenu, encoding="utf-8")
    return racine


A = document("Rapport A", "Fait : le RSSI est M. Benali.", "Fait : sauvegardes chaque nuit.")
B = document("Rapport B", "Fait : le PRA n'a jamais été testé.")
C = document("Rapport C", "Fait : la PSSI date de 2019.")

# --- 1. premier passage : tout est traité --------------------------------------------------------
dossier = projet({"a.md": A, "b.md": B, "c.md": C})
faux = Faux()
index = Index(":memory:")
suivi: list[tuple[str, int, int]] = []
bilan = ingestion.mettre_a_jour(str(dossier / "intrants"), index, moteurs=faux.moteurs(),
                                progression=lambda p, f, t, m: suivi.append((p, f, t)))
verifier("3 documents traités au premier passage", len(bilan["traites"]) == 3 and faux.faits == ["a.md", "b.md", "c.md"])
docs = index.documents()
verifier("chaque document est enregistré avec son empreinte", set(docs) == {"a.md", "b.md", "c.md"} and all(d["empreinte"] for d in docs.values()))
verifier("seuls les faits à preuve vérifiée entrent dans l'index", index.base.execute("SELECT COUNT(*) FROM elements WHERE genre='fait'").fetchone()[0] == 4
         and not index.base.execute("SELECT 1 FROM elements WHERE libelle LIKE '%inventé%'").fetchone())
verifier("le fait non vérifié est compté mais écarté", docs["a.md"]["faits"] == 3 and docs["a.md"]["faits_verifies"] == 2)
verifier("les passages d'origine sont gardés (filet de sécurité)", index.base.execute("SELECT COUNT(*) FROM elements WHERE genre='passage'").fetchone()[0] >= 3)
verifier("la progression annonce les 4 phases", {p for p, _f, _t in suivi} == {"documents", "alias", "croisement", "couverture"})
verifier("entités fusionnées : une seule entité canonique pour K. Benali", index.base.execute("SELECT COUNT(DISTINCT canonique) FROM entites WHERE nom='K. Benali'").fetchone()[0] == 1)
verifier("croisement complet au premier passage", faux.croisements == [None])
verifier("couverture : un résultat par besoin, stocké dans l'index", faux.evaluations == len(couverture.BESOINS) == len(index.couvertures()))
verifier("le livrable lisible se construit depuis l'index", "Ce que nous ignorons encore" in ingestion.rapport(index))

# --- 2. rien n'a changé : retour immédiat, aucun modèle appelé -------------------------------------
avant = (len(faux.faits), faux.vecs, faux.evaluations)
bilan2 = ingestion.mettre_a_jour(str(dossier / "intrants"), index, moteurs=faux.moteurs())
verifier("document inchangé : rien n'est retraité", bilan2["inchange"] and (len(faux.faits), faux.vecs, faux.evaluations) == avant)

# --- 3. un document modifié : lui seul est retraité, sans doublon -----------------------------------
(dossier / "intrants" / "b.md").write_text(document("Rapport B", "Fait : le PRA a été testé en mars."), encoding="utf-8")
nb_avant = index.base.execute("SELECT COUNT(*) FROM elements WHERE doc='b.md'").fetchone()[0]
faux.faits.clear(); faux.croisements.clear()
bilan3 = ingestion.mettre_a_jour(str(dossier / "intrants"), index, moteurs=faux.moteurs())
verifier("document modifié : seul lui est retraité", faux.faits == ["b.md"] and [r["nom"] for r in bilan3["traites"]] == ["b.md"])
verifier("ses anciennes preuves ont disparu (pas de doublon)", index.base.execute("SELECT COUNT(*) FROM elements WHERE doc='b.md'").fetchone()[0] == nb_avant
         and not index.base.execute("SELECT 1 FROM elements WHERE doc='b.md' AND extrait LIKE '%jamais%'").fetchone()
         and index.base.execute("SELECT 1 FROM elements WHERE doc='b.md' AND extrait LIKE '%mars%'").fetchone())
verifier("le croisement ne porte que sur le document modifié", faux.croisements == [{"b.md"}])
verifier("la recherche plein texte ne retrouve plus l'ancien texte", not index.rechercher("jamais testé", None, k=5, verifies_seulement=False)
         or all("jamais" not in r["extrait"] for r in index.rechercher("jamais", None, k=5, verifies_seulement=False)))

# --- 4. un document retiré : ses preuves et ses contradictions partent avec lui ----------------------
index.ajouter_contradiction("", "a.md", "Fait A", "c.md", "Fait C", "contradiction", "x", 1)
os.remove(dossier / "intrants" / "c.md")
bilan4 = ingestion.mettre_a_jour(str(dossier / "intrants"), index, moteurs=faux.moteurs())
verifier("document retiré : signalé dans le bilan", bilan4["retires"] == ["c.md"])
verifier("document retiré : plus aucune preuve", index.base.execute("SELECT COUNT(*) FROM elements WHERE doc='c.md'").fetchone()[0] == 0 and "c.md" not in index.documents())
verifier("document retiré : ses contradictions disparaissent", not index.base.execute("SELECT 1 FROM contradictions WHERE doc_a='c.md' OR doc_b='c.md'").fetchone())
verifier("document retiré : plus de mention", not index.base.execute("SELECT 1 FROM mentions WHERE doc='c.md'").fetchone())

# --- 5. un document en échec n'arrête pas les autres et sera réessayé ---------------------------------
d5 = projet({"x.md": A, "y.md": B})
faux5 = Faux(echec={"x.md"})
i5 = Index(":memory:")
b5 = ingestion.mettre_a_jour(str(d5 / "intrants"), i5, moteurs=faux5.moteurs())
verifier("l'échec d'un document est enregistré, l'autre est traité", [e["nom"] for e in b5["erreurs"]] == ["x.md"] and [t["nom"] for t in b5["traites"]] == ["y.md"])
verifier("le détail de l'erreur est conservé", "modèle indisponible" in i5.documents()["x.md"]["detail"] and i5.documents()["x.md"]["statut"] == "erreur")
faux5.echec.clear(); faux5.faits.clear()
b5b = ingestion.mettre_a_jour(str(d5 / "intrants"), i5, moteurs=faux5.moteurs())
verifier("au passage suivant, seul le document en erreur est refait", faux5.faits == ["x.md"] and i5.documents()["x.md"]["statut"] == "ok" and not b5b["erreurs"])

# --- 6. croisement complet à la demande -------------------------------------------------------------
faux6 = Faux()
ingestion.mettre_a_jour(str(dossier / "intrants"), index, moteurs=faux6.moteurs(), complet=True)
verifier("`complet` refait tout le croisement", faux6.croisements == [None] and not faux6.faits)

# --- 7. les contradictions trouvées sont rangées avec leur priorité ----------------------------------
d7 = projet({"a.md": A, "b.md": B})
i7 = Index(":memory:")
faux7 = Faux(conflit=True)
b7 = ingestion.mettre_a_jour(str(d7 / "intrants"), i7, moteurs=faux7.moteurs())
verifier("contradiction stockée avec le nombre de confirmations", b7["contradictions"] == 1 and i7.contradictions()[0]["confirmations"] == 1)
verifier("le livrable cite la contradiction de priorité haute", "incompatibles" in ingestion.rapport(i7))
verifier("sérialisation de la couverture : aller-retour sans perte",
         couverture.depuis_dict(couverture.en_dict(couverture.depuis_dict(i7.couvertures()[0]))).statut == couverture.INCONNU)

# --- 8. la tâche de fond : état lisible, reprise, un seul travail à la fois --------------------------
d8 = projet({"a.md": A, "b.md": B})
verifier("avant tout travail : état « absent »", travail.lire_etat(d8)["statut"] == "absent")
verifier("des documents jamais traités : mise à jour nécessaire", travail.a_mettre_a_jour(d8))
code = travail.executer(d8, moteurs=Faux().moteurs())
etat = travail.lire_etat(d8)
verifier("travail terminé : état « termine » avec bilan", code == 0 and etat["statut"] == "termine" and etat["bilan"]["documents"] == 2)
verifier("le livrable est écrit dans le projet", (d8 / travail.NOM_LIVRABLE).is_file())
verifier("le dossier de connaissance est rangé dans le projet", (d8 / "connaissance" / "index.sqlite").is_file())
verifier("rien à refaire après un travail réussi", not travail.a_mettre_a_jour(d8))
(d8 / "intrants" / "c.md").write_text(C, encoding="utf-8")
verifier("un document ajouté déclenche une mise à jour", travail.a_mettre_a_jour(d8))
fichier_etat = d8 / "connaissance" / "etat.json"
mort = json.loads(fichier_etat.read_text(encoding="utf-8"))
mort.update(statut="en_cours", pid=2 ** 22 + 12345)
fichier_etat.write_text(json.dumps(mort), encoding="utf-8")
verifier("processus disparu : état « interrompu » (jamais « en cours » à tort)", travail.lire_etat(d8)["statut"] == "interrompu")
mort.update(statut="en_cours", pid=os.getpid())
fichier_etat.write_text(json.dumps(mort), encoding="utf-8")
try:
    travail.lancer(d8)
    refuse = False
except RuntimeError:
    refuse = True
verifier("un seul travail à la fois par projet", refuse)

class Plante(Faux):
    def evaluer(self, *a, **k):
        raise RuntimeError("Ollama injoignable")

d9 = projet({"a.md": A})
code9 = travail.executer(d9, moteurs=Plante().moteurs())
verifier("erreur pendant le travail : état « erreur » avec la cause", code9 == 1 and travail.lire_etat(d9)["statut"] == "erreur" and "injoignable" in travail.lire_etat(d9)["erreur"])
code9b = travail.executer(d9, moteurs=Faux().moteurs())
verifier("après une erreur, le travail reprend sans refaire l'extraction déjà faite", code9b == 0 and travail.lire_etat(d9)["bilan"]["traites"] == [])

echecs = [(n, d) for n, ok, d in RESULTATS if not ok]
for nom, ok, detail in RESULTATS:
    print(("PASS " if ok else "FAIL ") + nom + (f" ({detail})" if detail and not ok else ""))
print(f"INGESTION: {len(RESULTATS) - len(echecs)} PASS, {len(echecs)} FAIL")
sys.exit(1 if echecs else 0)
