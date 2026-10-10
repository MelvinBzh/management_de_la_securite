#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de la recherche hors documents (`externe`) — aucun réseau, aucun modèle."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import couverture, externe, ingestion, travail  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402

RESULTATS: list[tuple[str, bool, str]] = []


def verifier(nom: str, condition: bool, detail: str = "") -> None:
    RESULTATS.append((nom, bool(condition), detail))


PAGE = "Le CERT-FR recommande de tester les restaurations de sauvegarde au moins une fois par an. Autre phrase sans rapport."
BESOIN = couverture.Besoin("cont-restau", "Continuité", "Quand a eu lieu la dernière restauration de sauvegarde réussie ?")
accord = (lambda d, a: True, lambda d, a: True)
desaccord = (lambda d, a: True, lambda d, a: False)
vecs = lambda textes, **_: [[1.0, 0.0, 1.0] for _ in textes]  # noqa: E731


def extraire_bon(question, url, page):
    return {"reponse": "Les restaurations doivent être testées chaque année.",
            "extrait": "recommande de tester les restaurations de sauvegarde au moins une fois par an"}


def extraire_invente(question, url, page):
    return {"reponse": "Le test est fait chaque mois.", "extrait": "il est obligatoire de tester chaque mois"}


# --- adresses : jamais de réseau interne ---------------------------------------------------------------------
for url in ("http://127.0.0.1/x", "http://localhost/x", "http://192.168.2.195:8501/", "http://10.0.0.5/", "file:///etc/passwd",
            "ftp://exemple.org/x", "http://169.254.169.254/latest/meta-data", "http://[::1]/"):
    verifier(f"adresse refusée : {url}", not externe.url_autorisee(url))
verifier("adresse sans hôte refusée", not externe.url_autorisee("http:///x"))
try:
    externe.lire_page("http://127.0.0.1/secret")
    refuse = False
except ValueError:
    refuse = True
verifier("lire_page refuse une adresse interne", refuse)

# --- texte de page --------------------------------------------------------------------------------------------
html_page = "<html><script>alert(1)</script><style>.a{}</style><body><p>Bonjour&nbsp;&amp; bienvenue</p></body></html>"
verifier("texte de page : scripts retirés, entités décodées", externe.texte_de_page(html_page) == "Bonjour & bienvenue")

# --- retenir : extrait exact + deux vérificateurs ---------------------------------------------------------------
verifier("retenu : extrait exact et vérificateurs d'accord", externe.retenir(BESOIN.question, "u", PAGE, extraire=extraire_bon, verificateurs=accord) is not None)
verifier("jeté : extrait inventé (absent de la page)", externe.retenir(BESOIN.question, "u", PAGE, extraire=extraire_invente, verificateurs=accord) is None)
verifier("jeté : les vérificateurs divergent (sans preuve = inconnu)", externe.retenir(BESOIN.question, "u", PAGE, extraire=extraire_bon, verificateurs=desaccord) is None)
verifier("jeté : page qui ne répond pas", externe.retenir(BESOIN.question, "u", PAGE, extraire=lambda *_: {"reponse": "", "extrait": ""}, verificateurs=accord) is None)

# --- enrichir : rangé avec origine et url, jamais mêlé aux documents -------------------------------------------------
index = Index(":memory:")
index.ajouter_element("fait", "audit.md", "Aucune restauration testée", "Aucune restauration n'a été testée depuis 2024", True, [1.0, 0.0, 1.0])
adresses_ok = {"https://cert.example.org/guide": "Guide"}
externe.url_autorisee_reel = externe.url_autorisee
externe.url_autorisee = lambda u: u in adresses_ok  # pas de DNS dans les tests
trouvees = externe.enrichir(index, BESOIN, recherche=lambda q: [("https://cert.example.org/guide", "Guide"), ("http://127.0.0.1/x", "Piège")],
                            lire=lambda u: PAGE, vecteurs=vecs, extraire=extraire_bon, verificateurs=accord)
verifier("une information externe retenue, la page interne ignorée", len(trouvees) == 1 and trouvees[0]["url"] == "https://cert.example.org/guide")
ligne = index.base.execute("SELECT genre, origine, url, libelle FROM elements WHERE origine='externe'").fetchone()
verifier("rangée avec origine « externe » et son url", ligne[0] == "externe" and ligne[1] == "externe" and ligne[2].startswith("https://") and ligne[3].startswith("[cont-restau]"))
verifier("la recherche par défaut ne voit JAMAIS l'externe", all(r["origine"] == "document" for r in index.rechercher("restaurations de sauvegarde testées", [1.0, 0.0, 1.0], k=8)))
verifier("l'externe n'apparaît que si on le demande", any(r["origine"] == "externe" for r in index.rechercher("restaurations de sauvegarde testées", [1.0, 0.0, 1.0], k=8, origines=("document", "externe"))))
repete = externe.enrichir(index, BESOIN, recherche=lambda q: [("https://cert.example.org/guide", "Guide")], lire=lambda u: PAGE,
                          vecteurs=vecs, extraire=extraire_bon, verificateurs=accord)
verifier("une même page n'est pas ajoutée deux fois", repete == [] and index.base.execute("SELECT COUNT(*) FROM elements WHERE origine='externe'").fetchone()[0] == 1)
panne = externe.enrichir(index, couverture.Besoin("autre", "x", "Autre question ?"), recherche=lambda q: [("https://cert.example.org/guide", "G")],
                         lire=lambda u: (_ for _ in ()).throw(OSError("réseau coupé")), vecteurs=vecs, extraire=extraire_bon, verificateurs=accord)
verifier("une page illisible ne bloque pas", panne == [])
verifier("section de rapport : origine et source visibles, « à valider »", all(x in externe.rapport_markdown(externe.externes(index)) for x in ("hors des documents", "à valider", "https://cert.example.org/guide", "pas des documents de l'entreprise")))
verifier("sans élément externe : aucune section", externe.rapport_markdown([]) == "")

# --- le travail de fond : option externe, même verrou ---------------------------------------------------------------
index.enregistrer_couverture("cont-restau", {"besoin": "cont-restau", "theme": "Continuité", "question": BESOIN.question, "statut": "inconnu",
                                             "reponse": "", "preuves": [], "contestations": [], "manque": "", "a_valider": True,
                                             "pourquoi": "", "verification": "sans_objet", "priorite": 3})
index.enregistrer_couverture("gouv-rssi", {"besoin": "gouv-rssi", "theme": "Gouvernance", "question": "Qui est le RSSI ?", "statut": "connu",
                                           "reponse": "M. X", "preuves": [], "contestations": [], "manque": "", "a_valider": False,
                                           "pourquoi": "", "verification": "soutenu", "priorite": 0})
questions: list[str] = []
externe.enrichir_inconnus(index, recherche=lambda q: questions.append(q) or [], lire=lambda u: "", vecteurs=vecs)
verifier("seules les questions sans réponse sont envoyées au web, sans extrait de document", questions == [BESOIN.question])
import os  # noqa: E402
os.environ.pop("E21_RECHERCHE_URL", None)
try:
    externe.chercher_searxng("q")
    message = ""
except RuntimeError as exc:
    message = str(exc)
verifier("sans E21_RECHERCHE_URL : message clair", "non configurée" in message)

d = Path(tempfile.mkdtemp(prefix="e21-ext-"))
(d / "intrants").mkdir()
(d / "intrants" / "a.md").write_text("# A\n\nFait : le PRA n'est pas testé. " + "Remplissage. " * 40, encoding="utf-8")


class Faux:
    def faits(self, nom, contenu):
        from tools.connaissance import fiches
        return [fiches.Fait(nom, "Le PRA n'est pas testé", "le PRA n'est pas testé", True)]

    def rels(self, nom, contenu):
        return [], []

    def croiser(self, index, **_):
        return []

    def evaluer(self, index, besoin, vec=None, **_):
        return couverture.Reponse(besoin, couverture.INCONNU, "", (), "à demander", "sans_objet", True, "Aucune preuve.")


f = Faux()
moteurs = ingestion.Moteurs(f.faits, f.rels, vecs, f.croiser, f.evaluer)
code = travail.executer(d, moteurs=moteurs, externe=True,
                        moteurs_externes={"recherche": lambda q: [("https://cert.example.org/guide", "G")], "lire": lambda u: PAGE,
                                          "vecteurs": vecs, "extraire": extraire_bon, "verificateurs": accord})
etat = travail.lire_etat(d)
verifier("travail avec recherche externe : terminé, trouvailles comptées", code == 0 and etat["bilan"]["externes"] >= 1)
verifier("le livrable contient la section externe", "hors des documents" in (d / travail.NOM_LIVRABLE).read_text(encoding="utf-8"))

echecs = [(n, x) for n, ok, x in RESULTATS if not ok]
for nom, ok, detail in RESULTATS:
    print(("PASS " if ok else "FAIL ") + nom + (f" ({detail})" if detail and not ok else ""))
print(f"EXTERNE: {len(RESULTATS) - len(echecs)} PASS, {len(echecs)} FAIL")
sys.exit(1 if echecs else 0)
