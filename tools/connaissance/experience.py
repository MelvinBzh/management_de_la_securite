"""Expérience : construire le dossier de connaissance d'un projet et en MESURER la qualité.

    OLLAMA_ENDPOINT=http://<pc-gpu>:11434 python3 -m tools.connaissance.experience <dossier_intrants> [--base index.sqlite]

Étapes : (1) faits et relations de chaque document, extraits vérifiés par le code ; (2) vecteurs ;
(3) index SQLite ; (4) fusion des alias ; (5) paires candidates puis jugement des contradictions ;
(6) test de recherche (rappel@k) sur des questions générées à partir de preuves connues.
Chaque mesure est écrite sur une ligne `RES ...` pour être relue ou archivée telle quelle.
"""
from __future__ import annotations

import glob
import json
import os
import random
import sys
import time

from . import alias, contradictions, fiches, ollama, relations, texte
from .index import Index

TAILLE_MIN_DOC = 300
QUESTIONS_TEST = 30


def _res(message: str) -> None:
    print("RES " + message, flush=True)


def lire_documents(dossier: str) -> dict[str, str]:
    """Documents Markdown d'un dossier d'intrants (les `.meta.json` sont ignorés)."""
    docs = {}
    for chemin in sorted(glob.glob(os.path.join(dossier, "*.md"))):
        contenu = open(chemin, encoding="utf-8").read()
        if len(contenu) >= TAILLE_MIN_DOC:
            docs[os.path.basename(chemin)] = contenu
    return docs


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    dossier = argv[0]
    chemin_base = argv[argv.index("--base") + 1] if "--base" in argv else ":memory:"
    random.seed(5)
    docs = lire_documents(dossier)
    _res(f"documents={len(docs)} caracteres={sum(len(t) for t in docs.values())}")

    # 1. faits + relations par document -------------------------------------------------------
    tous_faits: list[fiches.Fait] = []
    toutes_entites: list[relations.Entite] = []
    toutes_relations: list[relations.Relation] = []
    debut = time.time()
    for nom, contenu in docs.items():
        try:
            faits = fiches.extraire_faits(nom, contenu)
            entites, rels = relations.extraire(nom, contenu)
        except Exception as erreur:  # noqa: BLE001 — un document en échec n'arrête pas les autres
            _res(f"ERREUR extraction {nom}: {str(erreur)[:100]}")
            continue
        tous_faits += faits
        toutes_entites += entites
        toutes_relations += rels
    verifies = [f for f in tous_faits if f.verifie]
    rel_ok = [r for r in toutes_relations if r.verifiee]
    _res(f"extraction duree={time.time()-debut:.0f}s faits={len(tous_faits)} faits_verifies={len(verifies)} "
         f"({100*len(verifies)//max(len(tous_faits),1)} %) entites={len(toutes_entites)}")
    _res(f"relations={len(toutes_relations)} relations_verifiees={len(rel_ok)} ({100*len(rel_ok)//max(len(toutes_relations),1)} %)")
    types = {}
    for r in rel_ok:
        types[r.relation] = types.get(r.relation, 0) + 1
    _res("types_de_relations_verifiees=" + json.dumps(types, ensure_ascii=False))
    _res(f"documents_sans_aucune_relation_verifiee={sorted(set(docs) - {r.doc for r in rel_ok})}")

    # 2-3. vecteurs + index ----------------------------------------------------------------------
    elements = [("fait", f.doc, f.texte, f.extrait) for f in verifies] + \
               [("relation", r.doc, f"{r.sujet} {r.relation} {r.objet}", r.extrait) for r in rel_ok]
    vecs = ollama.vecteurs([f"{lib}. {ext}" for _g, _d, lib, ext in elements])
    index = Index(chemin_base)
    for (genre, doc, libelle, extrait), vec in zip(elements, vecs):
        index.ajouter_element(genre, doc, libelle, extrait, True, vec)

    # 4. alias ---------------------------------------------------------------------------------
    noms = sorted({(e.nom, e.type) for e in toutes_entites} | {(r.sujet, "autre") for r in rel_ok} | {(r.objet, "autre") for r in rel_ok})
    vec_noms = ollama.vecteurs([n for n, _t in noms])
    canonique, groupes = alias.fusionner(noms, vec_noms)
    _res(f"alias noms_distincts={len(noms)} entites_canoniques={len(set(canonique.values()))} groupes_fusionnes={len(groupes)}")
    for groupe in groupes[:25]:
        _res("GROUPE " + " | ".join(groupe))
    for nom, type_ in noms:
        index.ajouter_entite(nom, canonique.get(texte.normaliser(nom), nom), type_, [e.doc for e in toutes_entites if e.nom == nom])

    # 5. contradictions : recherche croisée (chaque fait face aux passages des AUTRES documents)
    debut = time.time()
    signaux = contradictions.croiser(index)
    _res(f"contradictions signalements={len(signaux)} duree={time.time()-debut:.0f}s")
    for s in signaux:
        index.ajouter_contradiction("", s.doc_a, s.extrait_a, s.doc_b, s.extrait_b, "contradiction", s.explication)
        _res(f"SIGNAL A[{s.doc_a[:28]}] {s.extrait_a[:150]} || B[{s.doc_b[:28]}] {s.extrait_b[:150]} || {s.explication[:160]}")

    # 6. recherche : rappel@k sur des questions dont on connaît la preuve ----------------------------
    echantillon = random.sample(range(len(elements)), min(QUESTIONS_TEST, len(elements)))
    modes = {"vecteurs seuls": (True, False), "mots-cles seuls": (False, True), "hybride": (True, True)}
    scores = {m: {1: 0, 3: 0, 5: 0} for m in modes}
    for i in echantillon:
        _g, _d, libelle, extrait = elements[i]
        question = ollama.discuter(
            "qwen3.5:9b", "Écris UNE question précise à laquelle cette phrase répond, SANS recopier ses mots exacts "
            f"(reformule). Réponds uniquement par la question.\n\nPHRASE : {extrait}", contexte=2048, max_sortie=80)
        vec_q = ollama.vecteurs([question], prefixe="search_query: ")[0]
        for mode, (avec_vec, avec_mots) in modes.items():
            trouves = index.rechercher(question, vec_q if avec_vec else None, k=5, mots_cles=avec_mots)
            rangs = [t["extrait"] for t in trouves]
            for k in (1, 3, 5):
                if extrait in rangs[:k]:
                    scores[mode][k] += 1
    for mode, par_k in scores.items():
        n = len(echantillon)
        _res(f"rappel[{mode}] @1={100*par_k[1]//n} % @3={100*par_k[3]//n} % @5={100*par_k[5]//n} % (n={n})")
    _res("index " + json.dumps(index.compter()))
    index.fermer()
    _res("FIN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
