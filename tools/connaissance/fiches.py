"""Fiche d'un document : ses faits atomiques, chacun avec l'extrait exact qui le prouve.

Un modèle propose les faits ; le CODE décide lesquels sont retenus (extrait retrouvé mot pour mot dans
le document). Un fait dont l'extrait n'existe pas est conservé mais marqué `verifie=False` : il ne doit
jamais alimenter une analyse, et le taux de faits non vérifiés mesure la fiabilité du modèle.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import ollama, texte

MODELE_EXTRACTION = "qwen3.5:9b"
MAX_FAITS = 12

SCHEMA_FAITS = {
    "type": "object",
    "properties": {"faits": {"type": "array", "items": {"type": "object", "properties": {
        "fait": {"type": "string"}, "extrait": {"type": "string"}}, "required": ["fait", "extrait"]}}},
    "required": ["faits"],
}

CONSIGNE = (
    "Voici un document. Extrais jusqu'à {maximum} FAITS ATOMIQUES (une idée par fait, formulée en une "
    "phrase autonome). Pour chaque fait, donne l'EXTRAIT EXACT du document qui le prouve : copie-le MOT "
    "POUR MOT (20 mots maximum), sans rien reformuler ni inventer. N'écris aucun fait que le document "
    "ne dit pas.\n\nDOCUMENT :\n{document}"
)


@dataclass(frozen=True)
class Fait:
    """Un fait d'un document, avec la preuve (extrait) et le verdict de la vérification par le code."""

    doc: str
    texte: str
    extrait: str
    verifie: bool


def extraire_faits(doc: str, contenu: str, *, modele: str = MODELE_EXTRACTION, maximum: int = MAX_FAITS) -> list[Fait]:
    """Faits d'un document. Le contenu est une DONNÉE : il ne sert qu'à être lu, jamais exécuté."""
    reponse = ollama.discuter_json(modele, CONSIGNE.format(maximum=maximum, document=contenu), SCHEMA_FAITS, contexte=16384)
    normalise = texte.normaliser(contenu)
    faits = []
    for brut in reponse.get("faits", [])[:maximum]:
        phrase, extrait = str(brut.get("fait", "")).strip(), str(brut.get("extrait", "")).strip()
        if len(phrase) > 15 and extrait:
            faits.append(Fait(doc, phrase, extrait, texte.contient(extrait, normalise)))
    return faits
