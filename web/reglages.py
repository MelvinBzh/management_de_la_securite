# -*- coding: utf-8 -*-
r"""Réglages modèles (endpoint IA, clé, modèle de chaîne) — socle pur, sans Streamlit.

Ce module regroupe la logique de la page « Réglages modèles » de `web/app.py` :
elle est donc testable sans interface (`web/tests/test_web.py`, WEB-16/17).

Garde-fous appliqués :
- **Stockage local, hors git** : tout est écrit dans
  `stockage_local/reglages-modeles.json`, dossier gitignoré. Aucune clé d'API
  n'est jamais versionnée, et `masquer` garantit qu'elle ne réapparaît pas en
  clair dans l'interface.
- **Fail closed sur l'`endpoint`** : ni espace, ni retour à la ligne, ni
  point-virgule, ni chevron `>`/`<`, ni `&` — rien qui puisse finir sur une
  ligne de commande ou dans un interpréteur de commandes. Le format exigé est
  `http(s)://hôte[:port]`.
- **Fail closed sur les modèles** : `modele_chaine` et les valeurs de
  `modeles_agents` doivent ressembler à un identifiant de modèle
  (`ollama/qwen2.5:7b`, `anthropic/claude-sonnet-4-5`) ; `"rm -rf /"` est refusé.
- **Lecture jamais fatale** : `charger` renvoie les défauts si le fichier est
  absent ou corrompu — un réglage illisible ne casse jamais l'application.
- **Fusion, pas réinitialisation** : `enregistrer` ne remplace que les champs
  réellement fournis ; une clé absente d'un appel ne remet pas à zéro une clé
  déjà enregistrée.
- **Sonde bornée** : `sonder` interroge `<endpoint>/api/tags` avec un délai court,
  sans suivre de redirection, et n'affiche jamais de secret.
"""
from __future__ import annotations

import json
import re
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:  # import possible depuis n'importe où (web/, tests/)
    sys.path.insert(0, str(RACINE))

DOSSIER_LOCAL = RACINE / "stockage_local"
NOM_FICHIER = "reglages-modeles.json"

# Identifiant de modèle : `prefixe/segment` optionnel.
#   « qwen2.5:7b », « ollama/qwen2.5:7b », « anthropic/claude-sonnet-4-5 ».
RE_MODELE = re.compile(r"^[a-zA-Z0-9._-]{1,64}(/[a-zA-Z0-9._:-]{1,96})?$")

# `endpoint` : schéma http(s) + hôte (+ port et chemin facultatifs). Rien d'autre.
RE_ENDPOINT = re.compile(r"^https?://[a-zA-Z0-9._-]+(:[0-9]{1,5})?(/[a-zA-Z0-9._/-]*)?$")

# Caractères jamais tolérés dans un réglage : rien qui puisse finir sur une ligne
# de commande ou être interprété par un shell (séparateur, chevron, esperluette).
CARACTERES_INTERDITS = (
    " ", "\t", "\n", "\r", "\x0b", "\x0c",  # espaces et retours à la ligne
    ";", "&", "|", "`", "$", "'", '"', "\\",  # séparateurs et citations de shell
    ">", "<", ">>", "<<",  # chevrons (redirection)
    "*", "?", "!", "#", "~", "(", ")", "{", "}", "[", "]",  # jokers et groupements
)

LONGUEUR_MAX_CLE = 200
MASQUE_CLE = "••••"
DELAI_SONDE = 2.0

__all__ = [
    "RACINE",
    "DOSSIER_LOCAL",
    "NOM_FICHIER",
    "RE_MODELE",
    "RE_ENDPOINT",
    "LONGUEUR_MAX_CLE",
    "MASQUE_CLE",
    "DELAI_SONDE",
    "chemin_fichier",
    "defauts",
    "charger",
    "enregistrer",
    "valider",
    "masquer",
    "modele_valide",
    "sonder",
]


def chemin_fichier() -> Path:
    """Chemin du fichier de réglages `stockage_local/reglages-modeles.json`.

    Le dossier local est créé s'il est absent (écriture bornée à
    `stockage_local/`, jamais dans `analyses/` ni à la racine).
    """
    DOSSIER_LOCAL.mkdir(parents=True, exist_ok=True)
    return DOSSIER_LOCAL / NOM_FICHIER


def defauts() -> dict:
    """Réglages par défaut : Ollama local, aucune clé, aucun modèle imposé."""
    return {
        "endpoint": "http://localhost:11434",
        "cle": "",
        "modele_chaine": "",
        "modeles_agents": {},
    }


def modele_valide(nom: str) -> bool:
    """Vrai si `nom` ressemble à un identifiant de modèle (sinon `False`)."""
    return bool(isinstance(nom, str) and RE_MODELE.match(nom))


def valider(reglages: dict) -> dict:
    """Valide un dictionnaire de réglages et renvoie une copie normalisée.

    Contrôles (tout échec lève une `ValueError` en français nommant le champ) :
    - `endpoint` : format `http(s)://hôte[:port][/chemin]` et **aucun** caractère
      interdit (espace, retour à la ligne, `;`, `&`, `>`, `<`…) ;
    - `cle` : chaîne, 200 caractères maximum ;
    - `modele_chaine` : vide ou identifiant de modèle ;
    - `modeles_agents` : table `{agent: modèle}`, chaque modèle valide.

    Les champs absents gardent leur valeur par défaut ; les champs `None` sont
    traités comme « non fournis ».
    """
    if not isinstance(reglages, dict):
        raise ValueError(
            f"Réglages refusés : un dictionnaire était attendu, reçu {type(reglages).__name__}."
        )
    valeurs = defauts()
    valeurs.update({cle: val for cle, val in reglages.items() if val is not None})

    endpoint = valeurs["endpoint"]
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ValueError("Réglages refusés : le champ « endpoint » est vide.")
    endpoint = endpoint.strip()
    interdits = [c for c in CARACTERES_INTERDITS if c in endpoint]
    if interdits:
        raise ValueError(
            "Réglages refusés : le champ « endpoint » contient un caractère interdit "
            f"({', '.join(repr(c) for c in interdits)}). Format attendu : "
            "« http://192.168.1.50:11434 » — ni espace, ni « ; », ni « & », "
            "ni « > »/« < »."
        )
    if not RE_ENDPOINT.match(endpoint):
        raise ValueError(
            f"Réglages refusés : « endpoint » = « {endpoint} » n'est pas une adresse "
            "valide. Format attendu : « http://hôte:port » ou « https://hôte » "
            "(ex. « http://192.168.1.50:11434 »)."
        )
    if not urlsplit(endpoint).hostname:
        raise ValueError(
            f"Réglages refusés : « endpoint » = « {endpoint} » ne contient aucun hôte."
        )
    valeurs["endpoint"] = endpoint.rstrip("/")

    cle = valeurs["cle"]
    if not isinstance(cle, str):
        raise ValueError("Réglages refusés : le champ « cle » doit être une chaîne.")
    if len(cle) > LONGUEUR_MAX_CLE:
        raise ValueError(
            f"Réglages refusés : le champ « cle » dépasse {LONGUEUR_MAX_CLE} caractères "
            f"({len(cle)})."
        )
    valeurs["cle"] = cle.strip()

    modele = valeurs["modele_chaine"]
    if not isinstance(modele, str):
        raise ValueError(
            "Réglages refusés : le champ « modele_chaine » doit être une chaîne."
        )
    modele = modele.strip()
    if modele and not modele_valide(modele):
        raise ValueError(
            "Réglages refusés : « modele_chaine » = "
            f"« {modele} » n'est pas un identifiant de modèle. Formats acceptés : "
            "« ollama/qwen2.5:7b », « anthropic/claude-sonnet-4-5 » (lettres, chiffres, "
            "point, tiret, deux-points ; un seul « / » possible)."
        )
    valeurs["modele_chaine"] = modele

    agents = valeurs["modeles_agents"]
    if agents is None:
        agents = {}
    if not isinstance(agents, dict):
        raise ValueError(
            "Réglages refusés : « modeles_agents » doit être un dictionnaire "
            "{agent : modèle}."
        )
    normalises: dict[str, str] = {}
    for agent, nom in agents.items():
        agent = str(agent).strip()
        nom = str(nom).strip()
        if nom and not modele_valide(nom):
            raise ValueError(
                f"Réglages refusés : « modeles_agents[{agent}] » = « {nom} » n'est pas "
                "un identifiant de modèle (ex. « ollama/qwen2.5:7b »)."
            )
        if nom:
            normalises[agent] = nom
    valeurs["modeles_agents"] = normalises
    return valeurs


def charger() -> dict:
    """Réglages enregistrés (copie), ou les défauts si le fichier est illisible.

    **Aucune exception** ne remonte : fichier absent, JSON corrompu, contenu
    inattendu ou clé d'API non conforme — l'application doit toujours démarrer.
    """
    valeurs = defauts()
    chemin = chemin_fichier()
    try:
        brut = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return valeurs
    if not isinstance(brut, dict):
        return valeurs
    try:
        return valider(brut)
    except ValueError:
        # Enregistré invalide : on retombe champ par champ sur les valeurs par
        # défaut plutôt que de tout perdre (le fichier reste à inspecter).
        fusion = defauts()
        for cle_champ in ("endpoint", "cle", "modele_chaine"):
            valeur = brut.get(cle_champ)
            if isinstance(valeur, str):
                try:
                    fusion[cle_champ] = valider({cle_champ: valeur})[cle_champ]
                except ValueError:
                    continue
        agents = brut.get("modeles_agents")
        if isinstance(agents, dict):
            fusion["modeles_agents"] = {
                agent: nom for agent, nom in agents.items()
                if modele_valide(str(nom).strip())
            }
        return fusion


def enregistrer(reglages: dict) -> dict:
    """Valide puis **fusionne** `reglages` avec l'existant, écrit et renvoie le résultat.

    Une clé absente de `reglages` ne réinitialise pas une clé déjà enregistrée :
    seul le champ réellement fourni est remplacé. Le contenu renvoyé est donc
    toujours l'état complet stocké.
    """
    valides = valider(reglages)  # fail closed : rien n'est écrit si un champ est refusé
    chemin = chemin_fichier()
    existant = charger()
    fusion = defauts()
    for cle_champ in ("endpoint", "cle", "modele_chaine"):
        fourni = cle_champ in reglages and reglages[cle_champ] is not None
        fusion[cle_champ] = valides[cle_champ] if fourni else existant[cle_champ]
    if isinstance(reglages, dict) and reglages.get("modeles_agents") is not None:
        fusion["modeles_agents"] = valides["modeles_agents"]
    else:
        fusion["modeles_agents"] = dict(existant["modeles_agents"])
    # `valider` porte sur l'ensemble fusionné : les règles restent en un seul
    # endroit (pas de doublon), y compris sur les champs venant du fichier.
    fusion = valider(fusion)
    chemin.write_text(json.dumps(fusion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return fusion


def masquer(cle: str) -> str:
    """« •••• » si `cle` est non vide, chaîne vide sinon (jamais la clé en clair)."""
    return MASQUE_CLE if (cle or "").strip() else ""


def _raison_courte(exc: Exception) -> str:
    """Raison courte et lisible d'une exception réseau, sans secret ni trace longue."""
    if isinstance(exc, urllib.error.HTTPError):
        return f"réponse HTTP {exc.code}"
    if isinstance(exc, urllib.error.URLError):
        raison = getattr(exc, "reason", None)
        if isinstance(raison, OSError) and not isinstance(raison, (TimeoutError,)):
            raison = raison.strerror or type(raison).__name__
        return str(raison) if raison else "adresse injoignable"
    if isinstance(exc, TimeoutError):
        return "délai dépassé"
    texte = str(exc).strip()
    return texte if texte else type(exc).__name__


def _raison_hote(exc: Exception) -> str:
    """Raison d'un échec de connexion (OSError de socket, délai dépassé…)."""
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "délai dépassé"
    if isinstance(exc, ConnectionRefusedError):
        return "connexion refusée"
    if isinstance(exc, socket.gaierror):
        return "nom d'hôte introuvable"
    texte = str(exc).strip()
    return texte if texte else type(exc).__name__


class _SANS_REDIRECTION(urllib.request.HTTPRedirectHandler):
    """Gestionnaire qui refuse TOUTE redirection (aucune URL suivie)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirection refusée", headers, fp)


def sonder(endpoint: str, delai: float = DELAI_SONDE) -> dict:
    """Sonde HTTP **bornée** de l'API Ollama : `GET <endpoint>/api/tags`.

    Renvoie `{"joignable", "modeles", "message", "endpoint"}` :
    - `joignable` : l'API a répondu ;
    - `modeles` : noms de modèles annoncés (`/api/tags`) ;
    - `message` : phrase en français, sans aucun secret ;
    - `endpoint` : l'adresse sondée.

    Garde-fous : délai d'attente borné (`delai`), **aucune redirection suivie**
    (une sonde ne doit pas être détournée vers une autre URL), aucune donnée
    envoyée, aucune exception propagée. Un endpoint invalide est signalé sans
    appel réseau.
    """
    adresse = (endpoint or "").strip()
    resultat = {"joignable": False, "modeles": [], "message": "", "endpoint": adresse}
    if not adresse:
        resultat["message"] = "Aucune adresse à tester : renseignez d'abord l'endpoint."
        return resultat
    try:
        adresse = valider({"endpoint": adresse})["endpoint"]
    except ValueError as exc:
        resultat["message"] = f"Endpoint refusé — {exc}"
        resultat["endpoint"] = adresse
        return resultat
    resultat["endpoint"] = adresse
    url = f"{adresse}/api/tags"

    try:
        # `build_opener(_SANS_REDIRECTION)` : aucune redirection n'est installée,
        # donc un 3xx est retourné tel quel — la sonde ne peut pas être détournée
        # vers une autre URL par un service intermédiaire.
        with urllib.request.build_opener(_SANS_REDIRECTION).open(
            url, timeout=delai
        ) as reponse:
            code = getattr(reponse, "status", None) or reponse.getcode()
            if code != 200:
                resultat["message"] = f"Ollama ne répond pas sur {adresse} : HTTP {code}"
                return resultat
            brut = reponse.read(1_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if 300 <= int(exc.code) < 400:
            resultat["message"] = (
                f"Ollama ne répond pas sur {adresse} : redirection HTTP "
                f"{exc.code} refusée (sonde bornée, aucune URL suivie)."
            )
        elif exc.code == 404:
            resultat["message"] = (
                f"{adresse} répond mais n'expose pas /api/tags — ce service "
                "n'est peut-être pas une API Ollama."
            )
        else:
            resultat["message"] = f"Ollama ne répond pas sur {adresse} : HTTP {exc.code}"
        return resultat
    except urllib.error.URLError as exc:
        raison = _raison_courte(exc)
        hote = urlsplit(adresse).hostname or adresse
        if "Name or service not known" in raison or "not known" in raison.lower():
            resultat["message"] = f"Hôte injoignable : {raison}"
        elif isinstance(getattr(exc, "reason", None), (ConnectionRefusedError, OSError)) \
                and not isinstance(getattr(exc, "reason", None), TimeoutError):
            resultat["message"] = (
                f"Hôte injoignable : {hote} ({raison}) — Ollama est-il démarré "
                f"sur cette machine ?"
            )
        elif "timed out" in raison.lower():
            resultat["message"] = f"Hôte injoignable : {hote} (délai dépassé)"
        else:
            resultat["message"] = f"Ollama ne répond pas sur {adresse} : {raison}"
        return resultat
    except (TimeoutError, OSError) as exc:
        resultat["message"] = f"Hôte injoignable : {_raison_hote(exc)}"
        return resultat
    except Exception as exc:  # noqa: BLE001 — une sonde ne doit jamais casser la page
        resultat["message"] = f"Sonde impossible sur {adresse} : {_raison_courte(exc)}"
        return resultat

    try:
        document = json.loads(brut)
    except ValueError:
        resultat["message"] = (
            f"{adresse} a répondu, mais la réponse n'est pas du JSON exploitable."
        )
        return resultat
    entree = document.get("models") if isinstance(document, dict) else None
    if not isinstance(entree, list):
        resultat["message"] = f"{adresse} a répondu sans liste de modèles exploitable."
        return resultat
    modeles = sorted({
        str(modele.get("name", "")) for modele in entree
        if isinstance(modele, dict) and modele.get("name")
    })
    resultat["joignable"] = True
    resultat["modeles"] = modeles
    resultat["message"] = f"Joignable — {len(modeles)} modèle(s)"
    return resultat