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
# Un identifiant de modèle opencode : « big-pickle », « ollama/qwen2.5:7b »,
# « anthropic/claude-sonnet-4-5 », « llama3.1:8b » (tag Ollama « nom:tag »),
# éventuellement préfixé d'un fournisseur par un unique « / ».
RE_MODELE = re.compile(r"^[a-zA-Z0-9._:-]{1,64}(/[a-zA-Z0-9._:-]{1,96})?$")

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

NOM_PROFIL_MAX = 32
RE_PROFIL = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
PROFIL_OPENCODE = "opencode"      # config opencode déjà présente dans le conteneur
PROFIL_OLLAMA = "ollama"          # serveur Ollama (distant ou local)
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
    "PROFIL_OPENCODE",
    "PROFIL_OLLAMA",
    "nom_profil_valide",
    "appliquer_profil",
    "creer_profil",
    "activer_profil",
    "supprimer_profil",
    "nom_profils",
    "libelle_profil",
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
    """Réglages par défaut : deux profils prêts à l'emploi, aucun secret.

    - `opencode` : endpoint **vide** = on n'écrit aucune configuration d'exécution,
      opencode lit donc sa propre configuration (celle du conteneur Docker) ;
    - `ollama` : serveur Ollama, sans clé (valeur conventionnelle pour un
      fournisseur local).

    Les champs plats (`endpoint`, `cle`, `modele_chaine`) sont le **miroir du
    profil actif** : lire/écrire ces champs agit sur le profil sélectionné, ce qui
    garde l'existant (application, lancement) inchangé.
    """
    profils = {
        PROFIL_OPENCODE: {"endpoint": "", "cle": "", "modele_chaine": ""},
        PROFIL_OLLAMA: {
            "endpoint": "http://localhost:11434",
            "cle": "",
            "modele_chaine": "",
        },
    }
    return {
        "profil_actif": PROFIL_OPENCODE,
        "profils": profils,
        # miroir du profil actif (voir `appliquer_profil`)
        "endpoint": "",
        "cle": "",
        "modele_chaine": "",
        "modeles_agents": {},
    }


def nom_profil_valide(nom: str) -> bool:
    """Vrai si `nom` est un nom de profil sûr (minuscules, chiffres, `-`, `_`)."""
    return bool(isinstance(nom, str) and RE_PROFIL.match(nom))


def appliquer_profil(valeurs: dict, profil: str | None = None) -> dict:
    """Recopie le profil demandé dans les champs plats (endpoint/cle/modele_chaine).

    `profil` vaut par défaut le profil actif. Un profil inconnu est ignoré (les
    champs plats restent inchangés) : un nom forgé ne doit jamais faire le travail
    d'un profil existant.
    """
    profil = profil or valeurs.get("profil_actif") or PROFIL_OPENCODE
    contenu = (valeurs.get("profils") or {}).get(profil)
    if isinstance(contenu, dict):
        for champ in ("endpoint", "cle", "modele_chaine"):
            if champ in contenu:
                valeurs[champ] = contenu[champ]
    return valeurs


def modele_valide(nom: str) -> bool:
    """Vrai si `nom` ressemble à un identifiant de modèle (sinon `False`)."""
    return bool(isinstance(nom, str) and RE_MODELE.match(nom))


def normaliser_profils(valeurs: dict) -> dict:
    """Complète et Migre la table des profils, sans jamais l'élargir.

    Trois cas traités :
    - fichier déjà profilé : `profils` + `profil_actif` sont conservés ;
    - **fichier plat** (version précédente) : les champs plats sont rangés dans un
      profil `ollama` si un endpoint est présent, sinon dans le profil `opencode`
      — l'analyste ne perd rien ;
    - nom de profil invalide ou profil actif inconnu : refus explicite plutôt
      qu'un repli silencieux sur un autre profil (mauvaise surprise à l'usage).
    """
    valeurs = dict(valeurs)
    noms = valeurs.get("profils")
    if noms is None:
        plats = {
            champ: valeurs.get(champ)
            for champ in ("endpoint", "cle", "modele_chaine")
            if valeurs.get(champ) is not None
        }
        nom_migra = PROFIL_OLLAMA if str(plats.get("endpoint") or "").strip() else PROFIL_OPENCODE
        noms = {nom_migra: {c: v for c, v in plats.items() if v is not None}}
        # le fichier était plat : le profil actif n'est pas décidé par le fichier,
        # il est déduit du contenu (endpoint présent -> profil « ollama »).
        valeurs.pop("profil_actif", None)
    if not isinstance(noms, dict) or not noms:
        raise ValueError("Réglages refusés : « profils » doit être un dictionnaire non vide.")
    propres: dict[str, dict] = {}
    for nom, contenu in noms.items():
        nom = str(nom)
        if not nom_profil_valide(nom):
            raise ValueError(
                f"Réglages refusés : nom de profil « {nom} » invalide — minuscules, "
                "chiffres, tiret et souligné uniquement, 32 caractères maximum."
            )
        if not isinstance(contenu, dict):
            raise ValueError(
                f"Réglages refusés : le profil « {nom} » doit être un dictionnaire."
            )
        propres[nom] = {c: contenu.get(c, "") for c in ("endpoint", "cle", "modele_chaine")}
    actif = valeurs.get("profil_actif")
    if actif is None:
        actif = PROFIL_OLLAMA if any(
            (p.get("endpoint") or "").strip() for p in propres.values()
        ) else PROFIL_OPENCODE
    actif = str(actif)
    if not nom_profil_valide(actif):
        raise ValueError(f"Réglages refusés : nom de profil actif « {actif} » invalide.")
    if actif not in propres:
        raise ValueError(
            f"Réglages refusés : le profil actif « {actif} » n'existe pas "
            f"(profils présents : {', '.join(sorted(propres))})."
        )
    valeurs["profils"] = propres
    valeurs["profil_actif"] = actif
    return appliquer_profil(valeurs, actif)


def _valider_endpoint(endpoint: str, profil_actif: str) -> str:
    """Valide un endpoint non vide et renvoie sa forme normalisée (sans `/` final).

    Un endpoint **vide** est accepté uniquement pour un profil autre que « ollama » :
    cela signifie « n'écrire aucune configuration, opencode lit la sienne ».
    """
    if not isinstance(endpoint, str):
        raise ValueError("Réglages refusés : le champ « endpoint » doit être une chaîne.")
    if endpoint and not endpoint:
        raise ValueError(  # pragma: no cover - garde-fou de lecture
            "Réglages refusés : le champ « endpoint » est illisible."
        )
    original = endpoint
    endpoint = endpoint.strip()
    if not endpoint:
        if original and profil_actif != PROFIL_OLLAMA:
            raise ValueError(
                "Réglages refusés : le champ « endpoint » ne contient que des espaces. "
                "Laissez-le **vide** pour utiliser la configuration opencode du "
                "conteneur, ou saisissez une adresse."
            )
        if profil_actif == PROFIL_OLLAMA:
            raise ValueError(
                "Réglages refusés : le profil « ollama » exige un endpoint "
                "(ex. « http://192.168.2.144:11434 »). Pour utiliser la configuration "
                "opencode du conteneur, choisissez le profil « opencode »."
            )
        return ""
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
            "(ex. « http://192.168.2.144:11434 »)."
        )
    if not urlsplit(endpoint).hostname:
        raise ValueError(
            f"Réglages refusés : « endpoint » = « {endpoint} » ne contient aucun hôte."
        )
    return endpoint.rstrip("/")


def _valider_modele(modele: str, champ: str = "modele_chaine") -> str:
    """Valide un identifiant de modèle (vide accepté) et renvoie sa forme nue."""
    if not isinstance(modele, str):
        raise ValueError(f"Réglages refusés : le champ « {champ} » doit être une chaîne.")
    modele = modele.strip()
    if modele and not modele_valide(modele):
        raise ValueError(
            f"Réglages refusés : « {champ} » = « {modele} » n'est pas un identifiant "
            "de modèle. Formats acceptés : « big-pickle », « opencode/big-pickle », "
            "« ollama/qwen2.5:7b », « anthropic/claude-sonnet-4-5 » (lettres, chiffres, "
            "point, tiret, deux-points ; un seul « / » possible)."
        )
    return modele


def valider(reglages: dict) -> dict:
    """Valide des réglages et renvoie une copie normalisée (miroir du profil actif).

    Contrôles (tout échec lève une `ValueError` en français nommant le champ) :
    - `profils` / `profil_actif` : noms sûrs, profil actif existant (voir
      `normaliser_profils`, qui migre aussi un ancien fichier plat) ;
    - pour **chaque** profil : `endpoint` (vide autorisé hors profil « ollama »),
      `cle` (chaîne, 200 caractères maximum), `modele_chaine` (vide ou identifiant) ;
    - `modeles_agents` : table `{agent: modèle}`, chaque modèle valide.

    Les champs plats fournis (`endpoint`, `cle`, `modele_chaine`) sont repliqués dans
    le profil actif avant validation : écrire « l'endpoint du profil courant » est
    donc la formulation la plus naturelle.
    """
    if not isinstance(reglages, dict):
        raise ValueError(
            f"Réglages refusés : un dictionnaire était attendu, reçu {type(reglages).__name__}."
        )
    # --- fichier PLAT (version précédente) : les champs plats sont rangés dans un
    # profil, sinon ils seraient écrasés par les valeurs par défaut (le profil
    # « ollama » masquerait l'endpoint saisi par l'analyste).
    if "profils" not in reglages:
        flats = {
            champ: reglages[champ]
            for champ in ("endpoint", "cle", "modele_chaine")
            if reglages.get(champ) is not None
        }
        if flats:
            nom_migra = (
                PROFIL_OLLAMA if str(flats.get("endpoint") or "").strip() else PROFIL_OPENCODE
            )
            demande = reglages.get("profil_actif")
            if str(demande or "") == PROFIL_OLLAMA and not str(flats.get("endpoint") or "").strip():
                # le profil « ollama » a été demandé SANS adresse : on nomme le champ
                # fautif plutôt que de parler d'un profil inexistant.
                raise ValueError(
                    "Réglages refusés : le champ « endpoint » est vide alors que le "
                    "profil « ollama » est demandé. Saisissez l'adresse du serveur "
                    "Ollama (ex. « http://192.168.2.144:11434 »), ou choisissez le "
                    "profil « opencode » pour utiliser la configuration du conteneur."
                )
            if demande is not None and str(demande) != nom_migra:
                raise ValueError(
                    f"Réglages refusés : le profil actif « {demande} » n'existe pas "
                    f"dans ce fichier (données plates : seul « {nom_migra} » a pu être "
                    "reconstitué). Créez d'abord ce profil avec « Nouveau profil »."
                )
            valeurs = defauts()
            valeurs["profils"] = {nom_migra: flats}
            valeurs["profil_actif"] = nom_migra
            valeurs["modeles_agents"] = reglages.get("modeles_agents") or {}
            # le miroir plat est une VUE de lecture : on le retire, sinon il
            # écraserait le profil migré avec ses propres valeurs vides.
            for champ in ("endpoint", "cle", "modele_chaine"):
                valeurs.pop(champ, None)
            return valider(valeurs)

    valeurs = defauts()
    valeurs.update({cle: val for cle, val in reglages.items() if val is not None})
    # sans profil demandé explicitement, on active celui qui porte un endpoint
    if not any(c in reglages for c in ("profils", "profil_actif")):
        tables = valeurs.get("profils")
        if isinstance(tables, dict):
            derive = next(
                (
                    nom
                    for nom in (PROFIL_OLLAMA, PROFIL_OPENCODE)
                    if str((tables.get(nom) or {}).get("endpoint") or "").strip()
                ),
                None,
            )
            if derive:
                valeurs["profil_actif"] = derive
    # replique des champs plats dans le profil actif avant toute validation
    if "profils" in valeurs:
        actif = valeurs.get("profil_actif") or PROFIL_OPENCODE
        if not nom_profil_valide(str(actif)):
            raise ValueError(
                f"Réglages refusés : nom de profil actif « {actif} » invalide — "
                "minuscules, chiffres, tiret et souligné uniquement, 32 caractères maximum."
            )
        table = dict(valeurs["profils"]) if isinstance(valeurs["profils"], dict) else {}
        for nom in table:  # un nom piégé est nommé avant toute autre consideration
            if not nom_profil_valide(str(nom)):
                raise ValueError(
                    f"Réglages refusés : nom de profil « {nom} » invalide — minuscules, "
                    "chiffres, tiret et souligné uniquement, 32 caractères maximum."
                )
        if actif not in table:
            raise ValueError(
                f"Réglages refusés : le profil actif « {actif} » n'existe pas "
                f"(profils présents : {', '.join(sorted(table))}). Créez-le d'abord "
                "avec « Nouveau profil »."
            )
        courant = dict(table.get(actif) or {})
        # on ne recopie que les champs EFFECTIVEMENT fournis : sinon le miroir
        # vide des valeurs par défaut écraserait le profil (endpoint perdu).
        for champ in ("endpoint", "cle", "modele_chaine"):
            if champ in reglages and reglages[champ] is not None:
                courant[champ] = reglages[champ]
        table[actif] = courant
        valeurs["profils"] = table
        valeurs["profil_actif"] = actif
    valeurs = normaliser_profils(valeurs)

    for nom, contenu in sorted(valeurs["profils"].items()):
        valeurs["profils"][nom] = {
            "endpoint": _valider_endpoint(contenu.get("endpoint", ""), nom),
            "cle": _valider_cle(contenu.get("cle", "")),
            "modele_chaine": _valider_modele(contenu.get("modele_chaine", "")),
        }
    valeurs = appliquer_profil(valeurs)

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
        modele = _valider_modele(str(nom), champ=f"modeles_agents[{agent}]")
        if modele:
            normalises[agent] = modele
    valeurs["modeles_agents"] = normalises
    return valeurs


def _valider_cle(cle: str) -> str:
    """Valide une clé d'API (chaîne, longueur bornée) et renvoie sa forme nue."""
    if not isinstance(cle, str):
        raise ValueError("Réglages refusés : le champ « cle » doit être une chaîne.")
    if len(cle) > LONGUEUR_MAX_CLE:
        raise ValueError(
            f"Réglages refusés : le champ « cle » dépasse {LONGUEUR_MAX_CLE} caractères "
            f"({len(cle)})."
        )
    return cle.strip()


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


def _ecrire(etat: dict) -> dict:
    """Valide puis écrit l'état complet des réglages (gitignoré) et le renvoie."""
    valide = valider({k: v for k, v in etat.items() if k in
                      ("profils", "profil_actif", "modeles_agents")})
    chemin_fichier().write_text(
        json.dumps(valide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return valide


def enregistrer(reglages: dict, profil: str | None = None) -> dict:
    """Fusionne des champs dans **un profil** (le profil actif par défaut).

    Seuls les champs réellement fournis sont remplacés : une clé absente de
    `reglages` ne réinitialise rien. `profil` désigne le profil **à modifier** —
    il ne change pas le profil actif (utiliser `activer_profil` pour cela) :
    enregistrer les valeurs d'un profil secondaire ne doit jamais détourner le
    prochain lancement. Un nom de profil inconnu ou piégé est refusé
    (fail closed : rien n'est écrit).

    Renvoie l'état complet stocké (profils + miroir du profil actif).
    """
    if not isinstance(reglages, dict):
        raise ValueError(
            f"Réglages refusés : un dictionnaire était attendu, reçu {type(reglages).__name__}."
        )
    etat = charger()
    cible = profil if profil is not None else etat["profil_actif"]
    cible = str(cible).strip()
    if not nom_profil_valide(cible):
        raise ValueError(
            f"Réglages refusés : nom de profil « {cible} » invalide — minuscules, "
            "chiffres, tiret et souligné uniquement, 32 caractères maximum."
        )
    if cible not in etat["profils"]:
        raise ValueError(
            f"Réglages refusés : le profil « {cible} » n'existe pas "
            f"(profils présents : {', '.join(sorted(etat['profils']))})."
        )
    courant = dict(etat["profils"][cible])
    for champ in ("endpoint", "cle", "modele_chaine"):
        if champ in reglages and reglages[champ] is not None:
            courant[champ] = reglages[champ]
    if "modeles_agents" in reglages and reglages["modeles_agents"] is not None:
        etat["modeles_agents"] = dict(reglages["modeles_agents"])
    etat["profils"][cible] = courant
    # le profil actif est laissé tel quel : seul `activer_profil` le change
    etat = _ecrire(etat)
    return appliquer_profil(etat)


def creer_profil(nom: str, endpoint: str = "", cle: str = "", modele_chaine: str = "") -> dict:
    """Crée un profil supplémentaire (sans l'activer) et renvoie l'état complet.

    Le nom est validé et **un profil existant n'est jamais écrasé** : pour changer
    les valeurs d'un profil, utiliser `enregistrer`. L'endpoint peut être vide
    (config opencode du conteneur) pour un profil autre que « ollama ».
    """
    nom = str(nom).strip().lower()
    if not nom_profil_valide(nom):
        raise ValueError(
            f"Nom de profil refusé : « {nom} » — minuscules, chiffres, tiret et "
            "souligné uniquement, 32 caractères maximum, il doit commencer par une "
            "lettre ou un chiffre."
        )
    etat = charger()
    if nom in etat["profils"]:
        raise ValueError(
            f"Profil « {nom} » déjà présent : modifiez-le au lieu de le recréer."
        )
    etat["profils"][nom] = {"endpoint": endpoint, "cle": cle, "modele_chaine": modele_chaine}
    # on valide l'ensemble : un profil « ollama » sans endpoint serait refusé
    return appliquer_profil(_ecrire(etat), etat["profil_actif"])


def activer_profil(nom: str) -> dict:
    """Bascule le profil actif et renvoie l'état complet (miroir recalculé)."""
    nom = str(nom).strip()
    etat = charger()
    if not nom_profil_valide(nom):
        raise ValueError(f"Nom de profil refusé : « {nom} ».")
    if nom not in etat["profils"]:
        raise ValueError(
            f"Profil « {nom} » introuvable (profils présents : "
            f"{', '.join(sorted(etat['profils']))})."
        )
    etat["profil_actif"] = nom
    return appliquer_profil(_ecrire(etat), nom)


def supprimer_profil(nom: str) -> dict:
    """Supprime un profil (jamais le dernier) et renvoie l'état complet.

    Si le profil supprimé était actif, le premier profil restant devient actif :
    l'application ne se retrouve jamais sans profil sélectionné.
    """
    nom = str(nom).strip()
    etat = charger()
    if nom not in etat["profils"]:
        raise ValueError(f"Profil « {nom} » introuvable.")
    if len(etat["profils"]) <= 1:
        raise ValueError(
            "Impossible de supprimer le dernier profil : créez-en un autre d'abord."
        )
    etat["profils"].pop(nom)
    if etat["profil_actif"] == nom:
        etat["profil_actif"] = sorted(etat["profils"])[0]
    return appliquer_profil(_ecrire(etat), etat["profil_actif"])


def nom_profils(etat: dict | None = None) -> list[str]:
    """Noms des profils connus, triés (le profil actif en premier)."""
    etat = etat if etat is not None else charger()
    noms = sorted(etat.get("profils") or {})
    actif = etat.get("profil_actif")
    if actif in noms:
        noms.remove(actif)
        noms.insert(0, actif)
    return noms


def libelle_profil(nom: str, etat: dict | None = None) -> str:
    """Libellé lisible d'un profil : ce qu'il faut savoir en une ligne.

    - profil sans endpoint → « configuration opencode du conteneur » ;
    - sinon « Ollama <endpoint> » (jamais la clé, qui n'est pas affichée).
    """
    etat = etat if etat is not None else charger()
    contenu = (etat.get("profils") or {}).get(nom) or {}
    endpoint = str(contenu.get("endpoint") or "").strip()
    if not endpoint:
        return "opencode (config du conteneur)"
    return f"Ollama · {endpoint}"


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