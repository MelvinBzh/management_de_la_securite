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


# Second avis (mesuré sur 101 signalements de Nordval) : avec une consigne stricte, les deux modèles ne confirment
# JAMAIS à l'unanimité — ce n'est donc pas un filtre dur. Mais les 41 signalements confirmés par au moins un modèle
# contiennent presque toutes les vraies incohérences, et les 60 autres presque tous les faux : on s'en sert pour
# TRIER (priorité haute / basse), sans rien supprimer (le faux « compatible » de Sage X3 reste visible en priorité basse).
MODELES_CONFIRMATION = ("qwen3.5:9b", "gemma4:12b")

SCHEMA_CONFIRMATION = {
    "type": "object",
    "properties": {"incompatibles": {"type": "boolean"}, "raison": {"type": "string"}},
    "required": ["incompatibles", "raison"],
}

CONSIGNE_CONFIRMATION = (
    "EXTRAIT A (document {doc_a}) : {extrait_a}\nEXTRAIT B (document {doc_b}) : {extrait_b}\n\n"
    "A et B sont-ils INCOMPATIBLES, c'est-à-dire impossibles à vrais en même temps pour le MÊME sujet (valeurs, dates, "
    "statuts ou responsables différents) ? Réponds incompatibles=false si ce sont deux informations différentes mais "
    "compatibles, si les sujets diffèrent, ou si un extrait n'est qu'un en-tête technique. Explique en une phrase."
)


@dataclass(frozen=True)
class Signal:
    """Contradiction présumée entre deux extraits de documents différents (à valider par un humain)."""

    doc_a: str
    extrait_a: str
    doc_b: str
    extrait_b: str
    explication: str
    confirmations: int = 0  # nombre de modèles de second avis qui jugent aussi les extraits incompatibles

    @property
    def priorite(self) -> str:
        """« haute » si au moins un second avis confirme, « basse » sinon (à relire si le temps le permet)."""
        return "haute" if self.confirmations >= 1 else "basse"


def _confirmer_modele(signal: Signal, modele: str) -> bool:
    reponse = ollama.discuter_json(
        modele, CONSIGNE_CONFIRMATION.format(doc_a=signal.doc_a[:30], extrait_a=signal.extrait_a[:500],
                                             doc_b=signal.doc_b[:30], extrait_b=signal.extrait_b[:500]),
        SCHEMA_CONFIRMATION, contexte=4096, max_sortie=120)
    return bool(reponse.get("incompatibles"))


def confirmer(signal: Signal, *, modeles: tuple[str, ...] = MODELES_CONFIRMATION, confirmation=None) -> Signal:
    """Renvoie le signalement avec le nombre de modèles de second avis qui le confirment."""
    confirmation = confirmation or _confirmer_modele
    return Signal(signal.doc_a, signal.extrait_a, signal.doc_b, signal.extrait_b, signal.explication,
                  sum(1 for m in modeles if confirmation(signal, m)))


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


def _signaler(index, doc: str, libelle: str, extrait: str, vecteur, juge, modele: str, passages: int) -> Signal | None:
    """Confronte UN fait aux passages proches des AUTRES documents ; renvoie le signalement ou None."""
    candidats = index.rechercher(f"{libelle} {extrait}", vecteur, k=passages * 3)
    autres = [c for c in candidats if c["doc"] != doc and c["extrait"] != extrait][:passages]
    if not autres:
        return None
    verdict = juge({"doc": doc, "extrait": extrait}, autres, modele)
    position = verdict.get("passage", 0)
    if not verdict.get("contradiction") or not 1 <= position <= len(autres):
        return None
    explication = str(verdict.get("explication", ""))
    if est_faux_positif(explication):
        return None
    cible = autres[position - 1]
    return Signal(doc, extrait, cible["doc"], cible["extrait"], explication)


def croiser(index, *, modele: str = MODELE_JUGE, passages: int = 4, limite: int | None = None, juge=None,
            second_avis: bool = True, confirmation=None, seulement_docs: set[str] | None = None,
            progression=None) -> list[Signal]:
    """Signalements de contradictions entre documents, dédoublonnés, faux positifs évidents écartés.

    `index` : un `Index` rempli (éléments vérifiés avec vecteurs). `juge(fait, autres, modele)` est
    injectable pour tester sans modèle ; par défaut, le modèle `modele` juge chaque fait. Avec `second_avis`, chaque
    signalement reçoit une priorité (voir `Signal.priorite`) et la liste est triée priorité haute d'abord.
    """
    juge = juge or _juger_croise
    lignes = index.base.execute("SELECT id, doc, libelle, extrait, vecteur FROM elements WHERE verifie = 1").fetchall()
    if seulement_docs is not None:  # mise à jour incrémentale : seuls les faits des documents nouveaux ou modifiés
        lignes = [l for l in lignes if l[1] in seulement_docs]
    signaux: list[Signal] = []
    vus: set[frozenset] = set()
    lignes = lignes[:limite] if limite else lignes
    for numero, (_ident, doc, libelle, extrait, vecteur) in enumerate(lignes, start=1):
        if progression:
            progression(numero, len(lignes))
        signal = _signaler(index, doc, libelle, extrait, json.loads(vecteur) if vecteur else None, juge, modele, passages)
        if signal and frozenset((signal.extrait_a, signal.extrait_b)) not in vus:
            vus.add(frozenset((signal.extrait_a, signal.extrait_b)))
            signaux.append(confirmer(signal, confirmation=confirmation) if second_avis else signal)
    return sorted(signaux, key=lambda s: -s.confirmations)


def contredit(index, preuves, *, modele: str = MODELE_JUGE, passages: int = 4, juge=None,
              second_avis: bool = True, confirmation=None) -> list[Signal]:
    """Les preuves citées (dicts `id`, `doc`, `extrait`) sont-elles CONTREDITES par un autre document ?

    Avec `second_avis`, seuls les signalements confirmés par au moins un second modèle sont retenus : une réponse
    n'est marquée « contestée » que sur un conflit crédible (sinon presque toutes le seraient).

    Sert à ne pas présenter comme acquise une réponse que le dossier lui-même conteste (ex. la règle de la PSSI
    « comptes désactivés sous 24 h » face au constat de l'audit).
    """
    juge = juge or _juger_croise
    signaux: list[Signal] = []
    for preuve in preuves:
        ligne = index.base.execute("SELECT libelle, vecteur FROM elements WHERE id = ?", (preuve["id"],)).fetchone()
        libelle, vecteur = (ligne[0], json.loads(ligne[1]) if ligne[1] else None) if ligne else ("", None)
        signal = _signaler(index, preuve["doc"], libelle, preuve["extrait"], vecteur, juge, modele, passages)
        if signal:
            signal = confirmer(signal, confirmation=confirmation) if second_avis else signal
            if not second_avis or signal.priorite == "haute":
                signaux.append(signal)
    return signaux
