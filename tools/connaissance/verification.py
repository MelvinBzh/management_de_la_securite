"""Vérifier qu'une affirmation est SOUTENUE par un texte : deux vérificateurs indépendants, un verdict à trois états.

Pourquoi deux : mesuré sur 115 affirmations (60 inventions) — Gemma 4 est le plus fiable, MiniCheck rate d'autres
cas et faiblit en contexte long ; leur accord est un signal fort, leur désaccord un signal de doute. Un doute n'est
jamais tranché par le code : il devient « nécessite une validation humaine », avec le pourquoi.

Règle d'emploi : vérifier contre des PASSAGES COURTS (l'extrait cité, le document source), jamais contre tout le
corpus — mesuré : 89 % des vrais faits acceptés sur le document source, 67 % sur 40 Ko collés.
"""
from __future__ import annotations

from . import ollama

MODELE_SPECIALISE = "bespoke-minicheck"
MODELE_JUGE = "gemma4:12b"

SOUTENU, NON_SOUTENU, DOUTE = "soutenu", "non_soutenu", "doute"


def minicheck(document: str, affirmation: str, *, modele: str = MODELE_SPECIALISE, contexte: int = 16384) -> bool:
    """Le modèle spécialisé répond Yes/No : le document soutient-il l'affirmation ?"""
    reponse = ollama.appeler("/api/generate", {
        "model": modele, "stream": False, "prompt": f"Document: {document}\nClaim: {affirmation}",
        "options": {"temperature": 0, "num_predict": 4, "num_ctx": contexte}})
    return reponse["response"].strip().lower().startswith("yes")


def juge(document: str, affirmation: str, *, modele: str = MODELE_JUGE, contexte: int = 16384) -> bool:
    """Un modèle généraliste, avec une consigne stricte : tous les détails doivent être dans le document."""
    consigne = (
        f"DOCUMENT(S) :\n{document}\n\nTu vérifies une affirmation par rapport aux documents ci-dessus. Réponds "
        "uniquement OUI si les documents soutiennent ENTIÈREMENT l'affirmation (tous ses détails), NON dans tous "
        f"les autres cas (détail absent, différent, contraire ou trop général).\n\nAFFIRMATION : {affirmation}\n\n"
        "Réponse (OUI ou NON) :")
    return ollama.discuter(modele, consigne, contexte=contexte, max_sortie=6).upper().startswith("OUI")


def combiner(verdicts: list[bool]) -> str:
    """Accord de tous les vérificateurs → soutenu / non soutenu ; désaccord → doute.

    >>> combiner([True, True])
    'soutenu'
    >>> combiner([False, False])
    'non_soutenu'
    >>> combiner([True, False])
    'doute'
    """
    if all(verdicts):
        return SOUTENU
    if not any(verdicts):
        return NON_SOUTENU
    return DOUTE


def verifier(document: str, affirmation: str, *, verificateurs=None) -> str:
    """Verdict combiné (`soutenu`, `non_soutenu` ou `doute`). `verificateurs` : fonctions (document, affirmation) → bool,
    injectables pour les tests ; par défaut Gemma 4 et MiniCheck."""
    verificateurs = verificateurs or (juge, minicheck)
    return combiner([bool(v(document, affirmation)) for v in verificateurs])
