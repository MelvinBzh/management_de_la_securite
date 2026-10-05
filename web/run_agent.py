# -*- coding: utf-8 -*-
r"""Lancement réel de la chaîne d'agents opencode depuis l'interface web E21.

Ce module est autonome : il n'importe **pas** Streamlit afin de rester
testable (`web/tests/test_web.py`) et réutilisable hors interface.

Garde-fous appliqués :
- **Commande fixe** : le texte passé à opencode vient de
  `lib.prompt_orchestrateur` et ne dépend que du nom de cas assaini ; aucun
  contenu d'intrant n'entre sur la ligne de commande.
- **Pas de shell** : `subprocess.Popen` reçoit une **liste d'arguments**
  (`shell=False`, défaut), donc aucun caractère d'un intrant n'est interprété
  par un interpréteur de commandes.
- **Écriture bornée** : le journal d'exécution est écrit dans
  `analyses/<cas>/intrants/` (dossier gitignoré), jamais ailleurs.
- **Maîtrise du processus** : la chaîne tourne dans une session détachée
  (`start_new_session`) et reste arrêtable à la demande (`terminer`).

Paramètres ajoutés pour la page « Réglages modèles » (`web/reglages.py`) :
- `lancer(..., modele=…)` ajoute `--model <modele>` **uniquement** si un modèle est
  fourni : `argv` reste donc à 5 éléments par défaut (WEB-09). Le modèle est validé
  par `reglages.valider` — le validateur est **importé**, jamais dupliqué — afin
  qu'aucune chaîne de commande ne puisse être injectée par ce champ.
- `lancer(..., env=…)` transmet un dictionnaire d'environnement au sous-processus
  (utilisé par l'appelant pour `OPENCODE_CONFIG`). Rien n'est imposé par défaut :
  le processus hérite de l'environnement courant.
- `fichier_config_opencode(reglages)` écrit un fragment de configuration opencode
  (`stockage_local/opencode-runtime.json`, gitignoré). **Vérifié inutile** : sur
  opencode 1.18.32, `OPENCODE_CONFIG` n'est pas lu et, même lu, ne_prime pas sur la
  configuration du projet — un fournisseur absent de `opencode.jsonc` provoque au
  mieux une erreur « Unexpected server error », au pire une connexion vers
  l'endpoint par défaut. La fonction est conservée (elle reste inoffensive et testée)
  mais plus rien n'en dépend : voir `ecrire_baseurl_ollama`.
- `ecrire_baseurl_ollama(endpoint)` / `restaurer_baseurl_ollama()` : le seul
  mécanisme qui fonctionne est le fichier `opencode.jsonc` du projet. Ces deux
  fonctions y règlent — puis restaurent — `provider.ollama.options.baseURL`, en ne
  touchant **qu'à cette valeur** : commentaires, indentation et tout le reste sont
  préservés caractère par caractère (le fichier est du JSONC, illisible par `json`).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:  # import possible depuis n'importe où (web/, tests/)
    sys.path.insert(0, str(RACINE))

from web import lib  # noqa: E402  (chemin du dépôt garanti ci-dessus)
from web import reglages  # noqa: E402  (validateur de modèle — source unique)

# Attente maximale donnée au processus lors d'un arrêt demandé (secondes).
DELAI_ARRET = 5
# Nombre de lignes de journal renvoyées par défaut à l'interface.
LIGNES_JOURNAL = 40
# Nom du fichier de configuration opencode dérivé des réglages (stockage local).
NOM_CONFIG_RUNTIME = "opencode-runtime.json"


class ChaineError(Exception):
    """Erreur métier de lancement de la chaîne (message affichable tel quel)."""


def opencode_cli() -> str | None:
    """Chemin de l'exécutable `opencode` dans le PATH, ou `None` si absent."""
    return shutil.which("opencode")


def _fichier_journal(dossier: Path, instant: datetime) -> Path:
    """Chemin du journal `analyses/<cas>/intrants/chaine-<horodatage>.log`."""
    horodatage = instant.strftime("%Y-%m-%d-%H-%M-%S")
    return dossier / lib.DOSSIER_INTRANTS / f"chaine-{horodatage}.log"


def _ecrire_journal(fichier_log: Path, proc) -> None:
    """Copie ligne à ligne la sortie du processus dans le journal (thread dédié).

    Se termine par `=== fin (code N) ===` : l'interface distingue ainsi une
    chaîne terminée d'une chaîne encore en cours (journal sans cette ligne).
    """
    try:
        with open(fichier_log, "a", encoding="utf-8") as sortie:
            for ligne in proc.stdout:
                sortie.write(ligne if ligne.endswith("\n") else ligne + "\n")
                sortie.flush()
            sortie.write(f"=== fin (code {proc.wait()}) ===\n")
    except (OSError, ValueError) as exc:  # journal supprimé, disque plein, flux fermé
        print(f"[run_agent] journal inaccessible : {fichier_log} ({exc})")


def _modele_valide(modele: str) -> str:
    """Valide `modele` avec le validateur de `web.reglages` (source unique).

    Le modèle ne se retrouve jamais « assaini » : un identifiant qui ne ressemble
    pas à un modèle est **refusé** (`ChaineError`), car il finit sur la ligne de
    commande (fail closed — rien qui puisse être interprété par un shell).
    """
    nom = str(modele).strip()
    try:
        valide = reglages.valider({"modele_chaine": nom})["modele_chaine"]
    except ValueError as exc:
        raise ChaineError(f"Modèle refusé : {exc}") from exc
    if valide != nom:
        raise ChaineError(
            f"Modèle refusé : « {modele} » ne correspond pas exactement à un "
            "identifiant de modèle."
        )
    return nom


def fichier_config_opencode(reglages_: dict | None = None) -> Path | None:
    """Écrit `stockage_local/opencode-runtime.json` et renvoie son chemin.

    Contenu : un fragment de configuration opencode déclarant le fournisseur
    `ollama` sur l'`endpoint` réglé, avec `apiKey` = la clé enregistrée (ou
    `"ollama"` si aucune — valeur conventionnelle du fournisseur local).

    Écriture **idempotente** : si le fichier existe déjà avec le même contenu,
    il n'est pas réécrit (pas de journalisation inutile, pas de modification de
    date). Le fichier est dans `stockage_local/`, donc gitignoré : une clé
    d'API n'est jamais versionnée.

    L'appelant passe ce chemin à opencode via `OPENCODE_CONFIG` ; ce module ne
    prétend pas garantir la résolution de cette variable côté opencode.
    """
    valeurs = reglages.valider(reglages_ if reglages_ is not None else reglages.charger())
    endpoint = valeurs["endpoint"].strip()
    if not endpoint:
        # Profil « opencode » : aucune configuration d'exécution n'est écrite, donc
        # aucun `OPENCODE_CONFIG` n'est passé — opencode lit SA configuration (celle
        # du conteneur Docker). Écrire ici un fragment Ollama forcerait par erreur le
        # fournisseur `ollama` sur un profil qui ne le demande pas.
        return None
    chemin = reglages.chemin_fichier().parent / NOM_CONFIG_RUNTIME
    fragment = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            "ollama": {
                "options": {
                    "baseURL": f"{endpoint}/v1",
                    "apiKey": valeurs["cle"] or "ollama",
                },
            },
        },
    }
    contenu = json.dumps(fragment, ensure_ascii=False, indent=2) + "\n"
    if chemin.is_file() and chemin.read_text(encoding="utf-8") == contenu:
        return chemin  # inchangé : pas de réécriture
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


def lancer(
    cas: str,
    dossier: Path | None = None,
    modele: str | None = None,
    env: dict | None = None,
) -> dict:
    """Lance la chaîne d'agents sur un cas et renvoie les infos de pilotage.

    `dossier` : dossier d'analyse à utiliser (par défaut `lib.dossier_cas(cas)`).
    `modele` : identifiant de modèle opencode (ex. `ollama/qwen2.5:7b`). Ajoute
    `--model <modele>` **uniquement s'il est fourni** — `argv` reste donc à
    5 éléments par défaut, 7 avec le modèle. Il est validé par
    `web.reglages.valider` (validateur importé, jamais dupliqué) ; un modèle
    invalide lève une `ChaineError` explicite en français.
    `env` : environnement du sous-processus. `None` = héritage de l'ambiance
    courante (comportement historique) ; un dictionnaire est transmis tel quel
    (utilisé par l'appelant pour `OPENCODE_CONFIG`).

    Le processus démarre en arrière-plan (session détachée) et sa sortie est
    copiée dans un journal horodaté sous `intrants/`.

    Renvoie `{"pid", "fichier_log", "dossier", "proc", "commande", "modele"}`.

    Lève `ChaineError` si le dossier d'analyse manque, si opencode est absent ou
    si le modèle est refusé ; un nom de cas refusé par `lib.nom_cas_sur` remonte
    une `ValueError` (fail closed).
    """
    nom = lib.nom_cas_sur(cas)
    dossier_reel = Path(dossier) if dossier is not None else lib.dossier_cas(nom)
    if not dossier_reel.is_dir():
        raise ChaineError(
            "Dossier d'analyse absent — préparez d'abord le cas "
            "(onglet « Préparer un cas »)."
        )
    cli = opencode_cli()
    if not cli or not Path(cli).exists():
        raise ChaineError(
            "opencode introuvable : installez opencode (voir .opencode/) puis relancez."
        )
    prompt = lib.prompt_orchestrateur(nom, dossier_reel.name)
    argv = [cli, "run", "--agent", "orchestrator"]
    modele_reel = ""
    if modele and str(modele).strip():
        modele_reel = _modele_valide(modele)
        argv += ["--model", modele_reel]
    argv.append(prompt)
    fichier_log = _fichier_journal(dossier_reel, datetime.now())
    fichier_log.parent.mkdir(parents=True, exist_ok=True)
    fichier_log.touch()
    options = {
        "cwd": str(lib.RACINE),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "text": True,
        "bufsize": 1,
        "start_new_session": True,
    }
    if env is not None:
        options["env"] = dict(env)
    proc = subprocess.Popen(argv, **options)
    redacteur = threading.Thread(
        target=_ecrire_journal,
        args=(fichier_log, proc),
        daemon=True,
        name="e21-journal",
    )
    redacteur.start()
    return {
        "pid": proc.pid,
        "fichier_log": str(fichier_log),
        "dossier": str(dossier_reel),
        "proc": proc,
        "commande": " ".join(argv),
        "modele": modele_reel,
    }


def est_vivant(proc) -> bool:
    """Vrai tant que le processus de chaîne tourne (`poll()` vaut `None`)."""
    return proc.poll() is None


def terminer(proc) -> None:
    """Arrête la chaîne : `terminate`, puis `kill` si elle résiste (> `DELAI_ARRET`)."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=DELAI_ARRET)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=DELAI_ARRET)
        except subprocess.TimeoutExpired:  # processus fantôme : on abandonne
            pass


def lire_log(fichier_log: str | Path, n: int = LIGNES_JOURNAL) -> str:
    """Dernières `n` lignes du journal d'exécution (chaîne vide si journal absent)."""
    chemin = Path(fichier_log)
    if not chemin.is_file():
        return ""
    lignes = chemin.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lignes[-n:]) if n > 0 else ""


def etape_terminees(dossier: Path) -> int:
    """Nombre d'étapes de la chaîne dont tous les livrables sont écrits."""
    return sum(1 for entree in lib.avancement_chaine(dossier) if entree["terminee"])


__all__ = [
    "RACINE",
    "DELAI_ARRET",
    "LIGNES_JOURNAL",
    "NOM_CONFIG_RUNTIME",
    "ChaineError",
    "opencode_cli",
    "lancer",
    "fichier_config_opencode",
    "est_vivant",
    "terminer",
    "lire_log",
    "etape_terminees",
]


# --------------------------------------------------------- endpoint Ollama du projet
# Valeur livrée avec le dépôt : valable quand Ollama tourne sur la machine qui
# héberge opencode. Toute autre adresse est écrite par `ecrire_baseurl_ollama`.
BASEURL_OLLAMA_LIVREE = "http://localhost:11434/v1"
CHEMIN_CONFIG_PROJET = RACINE / "opencode.jsonc"
# Une seule clé, un seul remplacement : le premier « baseURL » du bloc « ollama ».
RE_BASEURL = re.compile(r'("baseURL"\s*:\s*")([^"]*)(")')


def _bloc_fournisseur(source: str, fournisseur: str) -> tuple[int, int] | None:
    """Bornes du bloc JSONC `{ … }` dont la clé est exactement `"fournisseur"`.

    Le fichier est du JSONC : une accolade peut se trouver dans un commentaire ou
    dans une chaîne. On repère donc la clé comme **clé de premier niveau** — chaîne
    suivie de `:` puis de `{` — et on compte les accolades en sautant chaînes et
    commentaires `//`. Renvoie `(debut, fin)` ou `None` si le fournisseur est absent.
    """
    cible = '"' + str(fournisseur) + '"'
    n = len(source)
    i = 0
    while i < n:
        caractere = source[i]
        if caractere == "/" and source[i : i + 2] == "//":
            saut = source.find("\n", i)
            i = n if saut == -1 else saut
            continue
        if caractere != '"':
            i += 1
            continue
        # chaîne courante, échappements compris
        j = i + 1
        echappe = False
        while j < n:
            if echappe:
                echappe = False
            elif source[j] == "\\":
                echappe = True
            elif source[j] == '"':
                break
            j += 1
        chaine = source[i : j + 1]
        k = j + 1
        while k < n and source[k] in " \t\r\n":
            k += 1
        if chaine == cible and k < n and source[k] == ":":
            k += 1
            while k < n and source[k] in " \t\r\n":
                k += 1
            if k < n and source[k] == "{":
                profondeur = 0
                m = k
                dans_chaine = False
                echappe = False
                while m < n:
                    c = source[m]
                    if dans_chaine:
                        if echappe:
                            echappe = False
                        elif c == "\\":
                            echappe = True
                        elif c == '"':
                            dans_chaine = False
                    elif c == '"':
                        dans_chaine = True
                    elif c == "/" and source[m : m + 2] == "//":
                        saut = source.find("\n", m)
                        m = n if saut == -1 else saut
                        continue
                    elif c == "{":
                        profondeur += 1
                    elif c == "}":
                        profondeur -= 1
                        if profondeur == 0:
                            return k, m
                    m += 1
                return None
        i = j + 1
    return None


def ecrire_baseurl_ollama(endpoint: str, chemin: Path | None = None) -> dict:
    """Règle `provider.ollama.options.baseURL` dans `opencode.jsonc`.

    Seule la valeur est réécrite : le reste du fichier — commentaires du dépôt
    compris — est conservé tel quel, car le fichier est du JSONC que `json` refuse
    de lire. Un endpoint sans `/v1` se le voit ajouter (opencode parle à Ollama par
    son API compatible OpenAI).

    Renvoie `{"ecrit", "valeur", "chemin", "raison"}`. Refus explicite, sans
    écriture, si le fichier est absent, illisible, sans bloc `ollama` ou sans
    `baseURL` : mieux vaut un lancement annoncé comme « non configuré » qu'un
    fichier ouvert du mauvais côté.
    """
    chemin = Path(chemin) if chemin is not None else CHEMIN_CONFIG_PROJET
    attendu = str(endpoint or "").strip().rstrip("/")
    if not attendu:
        return {"ecrit": False, "valeur": "", "chemin": chemin,
                "raison": "Aucun endpoint à écrire."}
    if attendu.endswith("/v1"):
        attendu = attendu[: -len("/v1")]
    valeur = f"{attendu}/v1"
    try:
        source = chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {"ecrit": False, "valeur": valeur, "chemin": chemin,
                "raison": f"{chemin.name} illisible : {exc}"}

    bloc = _bloc_fournisseur(source, "ollama")
    if bloc is None:
        return {"ecrit": False, "valeur": valeur, "chemin": chemin,
                "raison": f"Aucun bloc « ollama » dans {chemin.name}."}
    debut, fin = bloc
    segment = source[debut : fin + 1]
    motif = RE_BASEURL
    trouve = motif.search(segment)
    if trouve is None:
        return {"ecrit": False, "valeur": valeur, "chemin": chemin,
                "raison": f"Aucune clé « baseURL » dans le bloc « ollama » de {chemin.name}."}
    deja = trouve.group(2)
    if deja == valeur:
        return {"ecrit": False, "valeur": valeur, "chemin": chemin,
                "raison": "Déjà configuré — rien n'est réécrit."}
    nouveau_segment = motif.sub(lambda m: m.group(1) + valeur + m.group(3), segment, count=1)
    chemin.write_text(source[:debut] + nouveau_segment + source[fin + 1 :], encoding="utf-8")
    return {"ecrit": True, "valeur": valeur, "chemin": chemin,
            "raison": f"{chemin.name} : baseURL ollama → {valeur}"}


def restaurer_baseurl_ollama(chemin: Path | None = None) -> dict:
    """Remet l'endpoint livré avec le dépôt (Ollama sur la machine d'opencode).

    Appelé lors d'un repli sur le modèle de secours : le dépôt n'est alors plus
    modifié, et `git status` reste propre si la chaîne a basculé sur big-pickle.
    """
    return ecrire_baseurl_ollama(BASEURL_OLLAMA_LIVREE, chemin=chemin)
