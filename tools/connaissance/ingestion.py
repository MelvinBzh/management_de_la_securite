"""Mise à jour INCRÉMENTALE du dossier de connaissance d'un projet.

Principe : on ne lit chaque document qu'une fois. Un document est retraité seulement s'il est NOUVEAU,
MODIFIÉ (empreinte différente) ou resté en ERREUR ; un document retiré emporte avec lui ses preuves.

Phases (la progression est annoncée à `progression(phase, fait, total, message)`) :

  1. documents    faits + relations + passages de chaque document nouveau ou modifié (extraits vérifiés par le code) ;
  2. alias        fusion des noms qui désignent la même chose (refaite sur l'ensemble des mentions) ;
  3. croisement   chaque fait des documents changés est confronté aux passages des AUTRES documents ;
  4. couverture   chaque besoin d'information : connu / partiel / inconnu (refait si quelque chose a changé).

Les « moteurs » (extraction, vecteurs, jugement) sont injectables : les tests n'appellent jamais de modèle.
Limite connue du croisement incrémental : un fait INCHANGÉ n'est pas reconfronté à un document ajouté ;
`complet=True` refait tout le croisement (à lancer de temps en temps, ou avant une livraison).
"""
from __future__ import annotations

import glob
import hashlib
import os
import time
from dataclasses import dataclass, field

from . import alias, contradictions, couverture, externe, fiches, ollama, passages, relations, texte
from .index import Index

TAILLE_MIN_DOC = 300  # en dessous, un « document » n'est que du bruit (page vide, en-tête seul)


@dataclass
class Moteurs:
    """Les appels aux modèles, remplaçables dans les tests."""

    extraire_faits: object = fiches.extraire_faits
    extraire_relations: object = relations.extraire
    vecteurs: object = ollama.vecteurs
    croiser: object = contradictions.croiser
    evaluer: object = couverture.evaluer
    vecteurs_questions: object = field(default=None)  # None : calculés avec `vecteurs` (préfixe « requête »)


def empreinte(contenu: str) -> str:
    """Empreinte stable du contenu d'un document (change si, et seulement si, le texte change)."""
    return hashlib.sha256(contenu.encode("utf-8")).hexdigest()[:16]


def lire_documents(dossier: str) -> dict[str, str]:
    """Documents Markdown d'un dossier d'intrants (les `.meta.json` sont ignorés, les fichiers vides aussi)."""
    docs = {}
    for chemin in sorted(glob.glob(os.path.join(dossier, "*.md"))):
        contenu = open(chemin, encoding="utf-8", errors="replace").read()
        if len(contenu) >= TAILLE_MIN_DOC:
            docs[os.path.basename(chemin)] = contenu
    return docs


def _rien(*_args) -> None:
    return None


def traiter_document(index: Index, nom: str, contenu: str, moteurs: Moteurs) -> dict:
    """Extrait et indexe UN document ; en cas d'échec le document est marqué `erreur` (réessayé au prochain passage)."""
    sceau = empreinte(contenu)
    index.supprimer_document(nom)
    try:
        faits = moteurs.extraire_faits(nom, contenu)
        entites, rels = moteurs.extraire_relations(nom, contenu)
        morceaux = passages.decouper(nom, contenu)
        sûrs = [f for f in faits if f.verifie]
        rels_ok = [r for r in rels if r.verifiee]
        elements = ([("fait", f.doc, f.texte, f.extrait) for f in sûrs]
                    + [("relation", r.doc, f"{r.sujet} {r.relation} {r.objet}", r.extrait) for r in rels_ok]
                    + [("passage", p.doc, p.contexte, p.texte) for p in morceaux])
        vecs = moteurs.vecteurs([f"{lib}. {ext}" for _g, _d, lib, ext in elements]) if elements else []
    except Exception as erreur:  # noqa: BLE001 — un document en échec n'arrête pas les autres
        index.enregistrer_document(nom, sceau, "erreur", f"{type(erreur).__name__}: {str(erreur)[:160]}")
        index.base.commit()
        return {"nom": nom, "statut": "erreur", "detail": str(erreur)[:160]}
    for (genre, doc, libelle, extrait), vec in zip(elements, vecs):
        index.ajouter_element(genre, doc, libelle, extrait, True, vec)
    for e in entites:
        index.ajouter_mention(nom, e.nom, e.type)
    for r in rels_ok:
        index.ajouter_mention(nom, r.sujet, "autre")
        index.ajouter_mention(nom, r.objet, "autre")
    index.enregistrer_document(nom, sceau, "ok", "", faits=len(faits), faits_verifies=len(sûrs), relations=len(rels),
                               relations_verifiees=len(rels_ok), passages=len(morceaux))
    index.base.commit()  # un plantage plus tard ne perd pas ce document
    return {"nom": nom, "statut": "ok", "faits": len(faits), "faits_verifies": len(sûrs),
            "relations": len(rels), "relations_verifiees": len(rels_ok), "passages": len(morceaux)}


def reconcilier_alias(index: Index, moteurs: Moteurs) -> int:
    """Refait la table des entités à partir de TOUTES les mentions ; renvoie le nombre d'entités canoniques."""
    mentions = index.mentions()
    noms = sorted({(nom, type_) for _d, nom, type_ in mentions})
    if not noms:
        index.remplacer_entites([])
        return 0
    distincts = alias.noms_distincts(noms)
    vecs = moteurs.vecteurs([nom for _norm, nom, _type in distincts])
    canonique, _groupes = alias.fusionner(noms, vecs)  # mêmes entrées que dans la mesure (jeu de noms distincts)
    lignes = []
    for nom, type_ in noms:
        docs = [d for d, n, t in mentions if n == nom and t == type_]
        lignes.append((nom, canonique.get(texte.normaliser(nom), nom), type_, docs))
    index.remplacer_entites(lignes)
    return len(set(c for _n, c, _t, _d in lignes))


def evaluer_couverture(index: Index, moteurs: Moteurs, progression=_rien, **options) -> list:
    """Évalue chaque besoin d'information et range le résultat dans l'index. Renvoie les `Reponse`."""
    besoins = couverture.BESOINS
    if moteurs.vecteurs_questions is None:
        vecs = moteurs.vecteurs([b.question for b in besoins], prefixe="search_query: ") \
            if _accepte_prefixe(moteurs.vecteurs) else moteurs.vecteurs([b.question for b in besoins])
    else:
        vecs = moteurs.vecteurs_questions
    index.vider_couverture()
    reponses = []
    for numero, (besoin, vec) in enumerate(zip(besoins, vecs), start=1):
        progression("couverture", numero, len(besoins), besoin.question)
        reponse = moteurs.evaluer(index, besoin, vec, **options)
        index.enregistrer_couverture(besoin.id, couverture.en_dict(reponse))
        index.base.commit()
        reponses.append(reponse)
    return reponses


def _accepte_prefixe(fonction) -> bool:
    try:
        import inspect
        return "prefixe" in inspect.signature(fonction).parameters
    except (TypeError, ValueError):
        return False


def mettre_a_jour(dossier_intrants: str, index: Index, *, moteurs: Moteurs | None = None, progression=_rien,
                  complet: bool = False, options_couverture: dict | None = None) -> dict:
    """Met le dossier de connaissance à jour. Renvoie un bilan (documents traités, retirés, erreurs, durées).

    Rien à faire (aucun document nouveau, modifié ou retiré, couverture déjà calculée) : retour immédiat,
    `bilan["inchange"]` vrai — relancer ne coûte rien.
    """
    moteurs = moteurs or Moteurs()
    docs = lire_documents(dossier_intrants)
    connus = index.documents()
    retires = sorted(n for n in connus if n not in docs)
    a_traiter = sorted(n for n, contenu in docs.items()
                       if n not in connus or connus[n]["empreinte"] != empreinte(contenu) or connus[n]["statut"] != "ok")
    bilan: dict = {"documents": len(docs), "traites": [], "retires": retires, "erreurs": [], "inchange": False}
    if not retires and not a_traiter and not complet and index.couvertures() and index.lire_meta("croisement") == "a_jour":
        bilan["inchange"] = True
        return bilan
    for nom in retires:
        index.supprimer_document(nom)
    for numero, nom in enumerate(a_traiter, start=1):
        progression("documents", numero, len(a_traiter), nom)
        resultat = traiter_document(index, nom, docs[nom], moteurs)
        (bilan["erreurs"] if resultat["statut"] == "erreur" else bilan["traites"]).append(resultat)
    if a_traiter or retires:
        progression("alias", 0, 1, "fusion des noms qui désignent la même chose")
        bilan["entites"] = reconcilier_alias(index, moteurs)
        index.base.commit()
    # croisement : les documents en erreur n'ont pas de preuves, donc rien à croiser pour eux
    changes = {r["nom"] for r in bilan["traites"]}
    if complet or changes or retires or index.lire_meta("croisement") != "a_jour":
        if complet or index.lire_meta("croisement") != "a_jour":
            index.vider_contradictions(None)
            cible = None
        else:
            index.vider_contradictions(changes)
            cible = changes
        signaux = moteurs.croiser(index, seulement_docs=cible,
                                  progression=lambda i, n: progression("croisement", i, n, "faits confrontés aux autres documents"))
        for s in signaux:
            index.ajouter_contradiction("", s.doc_a, s.extrait_a, s.doc_b, s.extrait_b, "contradiction", s.explication, s.confirmations)
        bilan["contradictions"] = len(signaux)
        index.definir("croisement", "a_jour")
        index.base.commit()
    reponses = evaluer_couverture(index, moteurs, progression, **(options_couverture or {}))
    bilan["couverture"] = {s: sum(1 for r in reponses if r.statut == s) for s in (couverture.CONNU, couverture.PARTIEL, couverture.INCONNU)}
    bilan["a_valider"] = sum(1 for r in reponses if r.a_valider)
    index.definir("derniere_mise_a_jour", time.strftime("%Y-%m-%d %H:%M:%S"))
    index.base.commit()
    return bilan


def rapport(index: Index) -> str:
    """Livrable « Recherches, contradictions et questions ouvertes » (Markdown) depuis l'index."""
    reponses = [couverture.depuis_dict(d) for d in index.couvertures()]
    signaux = [contradictions.Signal(c["doc_a"], c["extrait_a"], c["doc_b"], c["extrait_b"], c["explication"], c["confirmations"])
               for c in index.contradictions()]
    return couverture.rapport_markdown(reponses, signaux) + externe.rapport_markdown(externe.externes(index))
