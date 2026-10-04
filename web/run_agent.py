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
"""
from __future__ import annotations

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

# Attente maximale donnée au processus lors d'un arrêt demandé (secondes).
DELAI_ARRET = 5
# Nombre de lignes de journal renvoyées par défaut à l'interface.
LIGNES_JOURNAL = 40


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


def lancer(cas: str, dossier: Path | None = None) -> dict:
    """Lance la chaîne d'agents sur un cas et renvoie les infos de pilotage.

    `dossier` : dossier d'analyse à utiliser (par défaut `lib.dossier_cas(cas)`).
    Le processus démarre en arrière-plan (session détachée) et sa sortie est
    copiée dans un journal horodaté sous `intrants/`.

    Renvoie `{"pid", "fichier_log", "dossier", "proc", "commande"}`.

    Lève `ChaineError` si le dossier d'analyse manque ou si opencode est absent ;
    un nom de cas refusé par `lib.nom_cas_sur` remonte une `ValueError` (fail closed).
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
    argv = [cli, "run", "--agent", "orchestrator", prompt]
    fichier_log = _fichier_journal(dossier_reel, datetime.now())
    fichier_log.parent.mkdir(parents=True, exist_ok=True)
    fichier_log.touch()
    proc = subprocess.Popen(
        argv,
        cwd=str(lib.RACINE),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )
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
    "ChaineError",
    "opencode_cli",
    "lancer",
    "est_vivant",
    "terminer",
    "lire_log",
    "etape_terminees",
]
