"""Entités et relations typées d'un document, chacune avec son extrait exact.

Contrairement à un graphe générique (« references », « shares_data_with »), les types sont ceux de
l'analyse de risques : qui héberge, administre, dépend de, a accès à… Chaque relation doit citer
l'extrait qui la prouve ; le code vérifie l'extrait ET la présence des deux entités dans le document.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import ollama, texte

MODELE_EXTRACTION = "qwen3.5:9b"

TYPES_ENTITE = ("systeme", "prestataire", "personne", "role", "site", "contrat", "materiel",
                "donnee", "norme", "processus", "autre")
TYPES_RELATION = ("heberge", "administre", "depend_de", "acces_a", "sauvegarde", "fournit",
                  "responsable_de", "situe_a", "contractualise_avec", "utilise", "applique_norme",
                  "incident_sur", "autre")

SCHEMA_RELATIONS = {
    "type": "object",
    "properties": {
        "entites": {"type": "array", "items": {"type": "object", "properties": {
            "nom": {"type": "string"}, "type": {"type": "string", "enum": list(TYPES_ENTITE)}},
            "required": ["nom", "type"]}},
        "relations": {"type": "array", "items": {"type": "object", "properties": {
            "sujet": {"type": "string"}, "relation": {"type": "string", "enum": list(TYPES_RELATION)},
            "objet": {"type": "string"}, "extrait": {"type": "string"}},
            "required": ["sujet", "relation", "objet", "extrait"]}},
    },
    "required": ["entites", "relations"],
}

CONSIGNE = (
    "Voici un document d'une entreprise. Relève (1) ses ENTITÉS importantes (systèmes, prestataires, "
    "personnes, rôles, sites, contrats, matériels, données, normes, processus) avec leur type, puis (2) "
    "jusqu'à {maximum} RELATIONS entre ces entités (types autorisés : {types}). Pour chaque relation, "
    "donne l'EXTRAIT EXACT du document qui la prouve, copié MOT POUR MOT (25 mots maximum). N'invente "
    "aucune entité ni relation absente du document.\n\nDOCUMENT :\n{document}"
)


@dataclass(frozen=True)
class Entite:
    doc: str
    nom: str
    type: str


@dataclass(frozen=True)
class Relation:
    doc: str
    sujet: str
    relation: str
    objet: str
    extrait: str
    verifiee: bool


def verifier(relation: Relation, contenu_normalise: str) -> bool:
    """Extrait retrouvé mot pour mot ET sujet et objet présents dans le document."""
    return (texte.contient(relation.extrait, contenu_normalise)
            and texte.nom_present(relation.sujet, contenu_normalise)
            and texte.nom_present(relation.objet, contenu_normalise))


def extraire(doc: str, contenu: str, *, modele: str = MODELE_EXTRACTION, maximum: int = 15) -> tuple[list[Entite], list[Relation]]:
    """Entités et relations d'un document ; `Relation.verifiee` dit si le code a retrouvé la preuve."""
    reponse = ollama.discuter_json(
        modele, CONSIGNE.format(maximum=maximum, types=", ".join(TYPES_RELATION), document=contenu),
        SCHEMA_RELATIONS, contexte=16384)
    normalise = texte.normaliser(contenu)
    entites = [Entite(doc, str(e.get("nom", "")).strip(), str(e.get("type", "autre")))
               for e in reponse.get("entites", []) if str(e.get("nom", "")).strip()]
    relations = []
    for brut in reponse.get("relations", [])[:maximum]:
        rel = Relation(doc, str(brut.get("sujet", "")).strip(), str(brut.get("relation", "autre")),
                       str(brut.get("objet", "")).strip(), str(brut.get("extrait", "")).strip(), False)
        if rel.sujet and rel.objet and rel.extrait:
            relations.append(Relation(rel.doc, rel.sujet, rel.relation, rel.objet, rel.extrait, verifier(rel, normalise)))
    return entites, relations
