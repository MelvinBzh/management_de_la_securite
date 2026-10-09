"""Détection des contradictions entre documents : le garde-fou contre le « oui c'est bon » isolé.

MÉTHODE RETENUE : `croiser` (recherche croisée, voir plus bas). Les fonctions `candidats` / `juger`
(paires d'extraits proches) sont conservées pour comparaison : elles n'ont trouvé AUCUNE contradiction
sur Nordval, car deux phrases contradictoires ne sont pas forcément proches par le sens.

Méthode des paires, en deux temps : (1) le code propose des PAIRES d'extraits qui parlent de la même entité dans des documents
différents ; (2) un modèle juge chaque paire (contradiction / cohérent / complémentaire) en citant les deux
extraits. Le modèle ne voit que les deux extraits, jamais le corpus : il ne peut pas inventer un troisième fait.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from . import ollama, texte
from .relations import Relation

MODELE_JUGE = "gemma4:12b"

SCHEMA_JUGEMENT = {
    "type": "object",
    "properties": {"verdict": {"type": "string", "enum": ["contradiction", "coherent", "complementaire"]},
                   "explication": {"type": "string"}},
    "required": ["verdict", "explication"],
}

CONSIGNE = (
    "Deux extraits de documents d'une même entreprise concernent « {entite} ».\n"
    "EXTRAIT A (document {doc_a}) : {extrait_a}\n"
    "EXTRAIT B (document {doc_b}) : {extrait_b}\n\n"
    "Dis si A et B se CONTREDISENT (affirment des choses incompatibles sur le même sujet), sont COHÉRENTS "
    "(disent la même chose) ou COMPLÉMENTAIRES (apportent des informations différentes sans conflit). "
    "Appuie-toi uniquement sur ces deux extraits. Explique en une phrase."
)


@dataclass(frozen=True)
class Paire:
    entite: str
    a: Relation
    b: Relation
    similarite: float


def candidats(relations: list[Relation], canonique: dict[str, str], vecteurs_extraits: list[list[float]],
              maximum: int = 60, seuil_min: float = 0.55, seuil_max: float = 0.985) -> list[Paire]:
    """Paires d'extraits vérifiés sur la même entité, de documents différents, classées par proximité.

    On écarte les quasi-doublons (≥ `seuil_max` : même phrase répétée) et les paires sans rapport
    (< `seuil_min`). `vecteurs_extraits[i]` est le vecteur de `relations[i].extrait`.
    """
    par_entite: dict[str, list[int]] = {}
    for i, rel in enumerate(relations):
        if rel.verifiee:
            sujet = canonique.get(texte.normaliser(rel.sujet), rel.sujet)
            par_entite.setdefault(sujet, []).append(i)
    paires: list[Paire] = []
    for entite, indices in par_entite.items():
        for p, i in enumerate(indices):
            for j in indices[p + 1:]:
                if relations[i].doc == relations[j].doc:
                    continue
                sim = ollama.cosinus(vecteurs_extraits[i], vecteurs_extraits[j])
                if seuil_min <= sim < seuil_max:
                    paires.append(Paire(entite, relations[i], relations[j], sim))
    paires.sort(key=lambda p: -p.similarite)
    return paires[:maximum]


def juger(paire: Paire, *, modele: str = MODELE_JUGE) -> dict:
    """Verdict du modèle pour une paire : `{"verdict": ..., "explication": ...}` (`{}` si illisible)."""
    return ollama.discuter_json(
        modele, CONSIGNE.format(entite=paire.entite, doc_a=paire.a.doc, extrait_a=paire.a.extrait,
                                doc_b=paire.b.doc, extrait_b=paire.b.extrait),
        SCHEMA_JUGEMENT, contexte=4096, max_sortie=200)


# --- Méthode retenue : recherche croisée (mesurée sur Nordval : 71 signalements, dont la plupart des
# incohérences majeures ; la méthode « paires proches » ci-dessus en trouvait 0). Chaque fait est confronté
# aux passages les plus proches des AUTRES documents, retrouvés par l'index.

SCHEMA_CROISE = {
    "type": "object",
    "properties": {"contradiction": {"type": "boolean"}, "passage": {"type": "integer"}, "explication": {"type": "string"}},
    "required": ["contradiction", "passage", "explication"],
}

CONSIGNE_CROISE = (
    "FAIT (document {doc}) : {extrait}\n\nPASSAGES D'AUTRES DOCUMENTS :\n{passages}\n\n"
    "Un de ces passages CONTREDIT-il le fait, c'est-à-dire affirme-t-il quelque chose d'INCOMPATIBLE sur le "
    "même sujet (valeur, date, statut, responsable différents) ? Deux informations différentes mais "
    "compatibles ne sont PAS une contradiction. Réponds contradiction=true seulement si l'incompatibilité est "
    "explicite ; indique le numéro du passage (0 sinon)."
)

# Quand le juge se contredit lui-même (son explication conclut à la cohérence), le signalement est écarté.
# Attention aux mots qui en CONTIENNENT d'autres : « incompatible » contient « compatible », « incohérent »
# contient « cohérent » — d'où le test « lettre précédente » et les marqueurs de conflit explicites.
RE_COHERENT = re.compile(r"(?<![a-zé])(cohérent|compatible|complémentaire)")
RE_NEGATION = re.compile(r"ne contredit pas|pas de contradiction|aucune contradiction")
RE_CONFLIT = re.compile(r"incompatib|incohér|contradict|contredit")


@dataclass(frozen=True)
class Signal:
    """Contradiction présumée entre deux extraits de documents différents (à valider par un humain)."""

    doc_a: str
    extrait_a: str
    doc_b: str
    extrait_b: str
    explication: str


def est_faux_positif(explication: str) -> bool:
    """Le juge a signalé une contradiction mais son explication conclut à la cohérence (sans nommer de conflit).

    >>> est_faux_positif("Les deux informations sont cohérentes.")
    True
    >>> est_faux_positif("Les extraits sont incompatibles.")
    False
    """
    bas = explication.lower()
    conclut_coherent = bool(RE_COHERENT.search(bas) or RE_NEGATION.search(bas))
    conflit = bool(RE_CONFLIT.search(RE_NEGATION.sub("", bas)))
    return conclut_coherent and not conflit


def _juger_croise(fait: dict, autres: list[dict], modele: str) -> dict:
    passages = "\n".join(f"[{i + 1}] (document {c['doc'][:40]}) {c['extrait']}" for i, c in enumerate(autres))
    return ollama.discuter_json(
        modele, CONSIGNE_CROISE.format(doc=fait["doc"][:40], extrait=fait["extrait"], passages=passages),
        SCHEMA_CROISE, contexte=4096, max_sortie=160)


def croiser(index, *, modele: str = MODELE_JUGE, passages: int = 4, limite: int | None = None, juge=None) -> list[Signal]:
    """Signalements de contradictions entre documents, dédoublonnés, faux positifs évidents écartés.

    `index` : un `Index` rempli (éléments vérifiés avec vecteurs). `juge(fait, autres, modele)` est
    injectable pour tester sans modèle ; par défaut, le modèle `modele` juge chaque fait.
    """
    juge = juge or _juger_croise
    lignes = index.base.execute("SELECT id, doc, libelle, extrait, vecteur FROM elements WHERE verifie = 1").fetchall()
    signaux: list[Signal] = []
    vus: set[frozenset] = set()
    for ident, doc, libelle, extrait, vecteur in lignes[:limite] if limite else lignes:
        candidats = index.rechercher(f"{libelle} {extrait}", json.loads(vecteur) if vecteur else None, k=passages * 3)
        autres = [c for c in candidats if c["doc"] != doc and c["extrait"] != extrait][:passages]
        if not autres:
            continue
        verdict = juge({"doc": doc, "extrait": extrait}, autres, modele)
        position = verdict.get("passage", 0)
        if not verdict.get("contradiction") or not 1 <= position <= len(autres):
            continue
        explication = str(verdict.get("explication", ""))
        if est_faux_positif(explication):
            continue
        cible = autres[position - 1]
        cle = frozenset((extrait, cible["extrait"]))
        if cle not in vus:
            vus.add(cle)
            signaux.append(Signal(doc, extrait, cible["doc"], cible["extrait"], explication))
    return signaux
