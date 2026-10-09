"""Client Ollama minimal (bibliothèque standard uniquement).

Trois appels suffisent à tout le paquet : discuter (texte ou JSON contraint par un schéma), calculer
des vecteurs, mesurer une similarité. L'adresse du serveur vient de `OLLAMA_ENDPOINT`
(défaut : http://localhost:11434) : le paquet ne suppose pas où tourne le GPU.
"""
from __future__ import annotations

import json
import math
import os
import urllib.request

ENDPOINT_DEFAUT = "http://localhost:11434"
MODELE_VECTEURS = "nomic-embed-text"


def endpoint() -> str:
    """Adresse du serveur Ollama, sans « / » final."""
    return os.environ.get("OLLAMA_ENDPOINT", ENDPOINT_DEFAUT).rstrip("/")


def appeler(chemin: str, corps: dict, delai: int = 600) -> dict:
    """POST JSON vers l'API Ollama ; lève l'exception réseau telle quelle (l'appelant décide)."""
    requete = urllib.request.Request(
        endpoint() + chemin, json.dumps(corps).encode("utf-8"), {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(requete, timeout=delai) as reponse:
        return json.load(reponse)


def discuter(modele: str, consigne: str, *, schema: dict | None = None, contexte: int = 8192,
             reflechir: bool = False, max_sortie: int | None = None, delai: int = 600) -> str:
    """Une question, une réponse. `schema` contraint la sortie à du JSON valide (décodage contraint).

    Température 0 (reproductible) ; `reflechir=False` coupe le « thinking » des modèles qui en ont :
    pour extraire ou juger, il ralentit sans améliorer, et il épuise le budget de sortie.
    """
    options = {"temperature": 0, "num_ctx": contexte}
    if max_sortie:
        options["num_predict"] = max_sortie
    corps = {"model": modele, "stream": False, "think": reflechir, "options": options,
             "messages": [{"role": "user", "content": consigne}]}
    if schema:
        corps["format"] = schema
    return appeler("/api/chat", corps, delai)["message"]["content"].strip()


def discuter_json(modele: str, consigne: str, schema: dict, **options) -> dict:
    """Comme `discuter` mais renvoie le JSON décodé ; `{}` si la réponse n'est pas du JSON valide."""
    try:
        resultat = json.loads(discuter(modele, consigne, schema=schema, **options))
    except (ValueError, KeyError):
        return {}
    return resultat if isinstance(resultat, dict) else {}


def vecteurs(textes: list[str], *, modele: str = MODELE_VECTEURS, prefixe: str = "search_document: ",
             taille_lot: int = 32, delai: int = 300) -> list[list[float]]:
    """Vecteurs d'embedding (nomic-embed-text attend un préfixe : document ou requête)."""
    sorties: list[list[float]] = []
    for debut in range(0, len(textes), taille_lot):
        lot = [prefixe + t for t in textes[debut:debut + taille_lot]]
        sorties.extend(appeler("/api/embed", {"model": modele, "input": lot}, delai)["embeddings"])
    return sorties


def cosinus(a: list[float], b: list[float]) -> float:
    """Similarité cosinus de deux vecteurs (0.0 si l'un est nul ou de taille différente)."""
    if not a or len(a) != len(b):
        return 0.0
    produit = sum(x * y for x, y in zip(a, b))
    norme = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return produit / norme if norme else 0.0
