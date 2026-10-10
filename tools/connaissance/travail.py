"""Tâche de fond : tenir à jour le dossier de connaissance d'un projet, avec un état lisible par le site.

    python -m tools.connaissance.travail <dossier-du-projet> [--complet]

Le site lance cette commande en arrière-plan (l'extraction prend plusieurs minutes, le croisement davantage) et
lit `connaissance/etat.json` pour afficher l'avancement. UN SEUL travail à la fois par projet. Un travail
interrompu (processus disparu) est signalé « interrompu » et reprend là où il en était : les documents déjà
traités sont conservés (empreintes), seul le reste est refait.

Fichiers (dans le dossier du projet, jamais partagés entre projets) :
  connaissance/index.sqlite                    l'index (preuves, entités, contradictions, couverture)
  connaissance/etat.json                       l'avancement du travail en cours ou du dernier travail
  recherches-contradictions-questions.md       le livrable lisible dans le site
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from . import externe as recherche_externe
from . import ingestion
from .index import Index

NOM_DOSSIER = "connaissance"
NOM_ETAT = "etat.json"
NOM_BASE = "index.sqlite"
NOM_LIVRABLE = "recherches-contradictions-questions.md"
DOSSIER_INTRANTS = "intrants"
LIBELLES_PHASES = {
    "documents": "Lecture des documents (faits et relations)",
    "alias": "Fusion des noms qui désignent la même chose",
    "croisement": "Recherche de contradictions entre documents",
    "couverture": "Ce que l'on sait, en partie, ou pas encore",
    "externe": "Recherche hors des documents (web)",
}


def chemins(dossier_projet: str | Path) -> tuple[Path, Path, Path]:
    """(dossier de la connaissance, fichier d'index, fichier d'état) d'un projet."""
    base = Path(dossier_projet) / NOM_DOSSIER
    return base, base / NOM_BASE, base / NOM_ETAT


def _vivant(pid: int) -> bool:
    """Le processus `pid` existe-t-il encore ? (Sous Windows, `os.kill(pid, 0)` TERMINE le processus : on l'interroge à part.)"""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        noyau = ctypes.windll.kernel32
        poignee = noyau.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not poignee:
            return False
        code = ctypes.c_ulong()
        noyau.GetExitCodeProcess(poignee, ctypes.byref(code))
        noyau.CloseHandle(poignee)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except (OSError, ValueError):
        return False
    return True


def lire_etat(dossier_projet: str | Path) -> dict:
    """État du travail : `statut` ∈ absent, en_cours, termine, erreur, interrompu (+ phase, fait, total, message…)."""
    _, _, fichier = chemins(dossier_projet)
    try:
        etat = json.loads(fichier.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"statut": "absent"}
    if etat.get("statut") == "en_cours" and not _vivant(int(etat.get("pid", 0) or 0)):
        etat["statut"] = "interrompu"  # le processus a disparu sans conclure : on ne ment pas
    return etat


def _ecrire_etat(dossier_projet: str | Path, **champs) -> None:
    dossier, _, fichier = chemins(dossier_projet)
    dossier.mkdir(parents=True, exist_ok=True)
    try:
        etat = json.loads(fichier.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        etat = {}
    etat.update(champs)
    temporaire = fichier.with_suffix(".tmp")
    temporaire.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
    temporaire.replace(fichier)


def a_mettre_a_jour(dossier_projet: str | Path) -> bool:
    """Vrai si au moins un document est nouveau, modifié, retiré ou resté en erreur (ou si rien n'a jamais été fait)."""
    dossier, base, _ = chemins(dossier_projet)
    docs = ingestion.lire_documents(str(Path(dossier_projet) / DOSSIER_INTRANTS))
    if not docs and not base.is_file():
        return False
    if not base.is_file():
        return True
    index = Index(base)
    try:
        connus = index.documents()
        return (any(n not in connus or connus[n]["empreinte"] != ingestion.empreinte(c) or connus[n]["statut"] != "ok"
                    for n, c in docs.items())
                or any(n not in docs for n in connus) or not index.couvertures())
    finally:
        index.fermer()


def lancer(dossier_projet: str | Path, *, complet: bool = False, endpoint: str = "", externe: bool = False) -> int:
    """Démarre le travail en arrière-plan ; renvoie le PID. Refuse s'il y en a déjà un pour ce projet."""
    if lire_etat(dossier_projet).get("statut") == "en_cours":
        raise RuntimeError("Un travail de connaissance est déjà en cours pour ce projet.")
    argv = [sys.executable, "-m", "tools.connaissance.travail", str(dossier_projet)] + (["--complet"] if complet else []) + (["--externe"] if externe else [])
    env = dict(os.environ)
    if endpoint:
        env["OLLAMA_ENDPOINT"] = endpoint
    racine = Path(__file__).resolve().parents[2]
    proc = subprocess.Popen(argv, cwd=str(racine), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
    _ecrire_etat(dossier_projet, statut="en_cours", pid=proc.pid, phase="documents", fait=0, total=0,
                 message="démarrage", debut=time.strftime("%Y-%m-%d %H:%M:%S"), fin="", erreur="")
    return proc.pid


def executer(dossier_projet: str | Path, *, complet: bool = False, moteurs=None, options_couverture: dict | None = None,
             externe: bool = False, moteurs_externes: dict | None = None) -> int:
    """Exécute le travail dans CE processus (utilisé par la commande et par le pilote de chaîne). 0 = réussi."""
    dossier, base, _ = chemins(dossier_projet)
    dossier.mkdir(parents=True, exist_ok=True)
    _ecrire_etat(dossier_projet, statut="en_cours", pid=os.getpid(), phase="documents", fait=0, total=0,
                 message="démarrage", debut=time.strftime("%Y-%m-%d %H:%M:%S"), fin="", erreur="")

    def progression(phase: str, fait: int, total: int, message: str) -> None:
        _ecrire_etat(dossier_projet, phase=phase, fait=fait, total=total, message=message[:160],
                     libelle=LIBELLES_PHASES.get(phase, phase))

    index = Index(base)
    try:
        bilan = ingestion.mettre_a_jour(str(Path(dossier_projet) / DOSSIER_INTRANTS), index, moteurs=moteurs,
                                        progression=progression, complet=complet, options_couverture=options_couverture)
        if externe:  # recherche hors documents pour les besoins restés sans réponse ; jamais mêlée aux documents
            trouvees = recherche_externe.enrichir_inconnus(index, progression=progression, **(moteurs_externes or {}))
            bilan["externes"] = len(trouvees)
        (Path(dossier_projet) / NOM_LIVRABLE).write_text(ingestion.rapport(index), encoding="utf-8")
        _ecrire_etat(dossier_projet, statut="termine", fin=time.strftime("%Y-%m-%d %H:%M:%S"), bilan=bilan, message="à jour")
        return 0
    except Exception as erreur:  # noqa: BLE001 — l'état doit dire pourquoi, jamais rester « en cours »
        _ecrire_etat(dossier_projet, statut="erreur", fin=time.strftime("%Y-%m-%d %H:%M:%S"),
                     erreur=f"{type(erreur).__name__}: {str(erreur)[:300]}")
        return 1
    finally:
        index.fermer()


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    dossier = Path(argv[0])
    if not (dossier / DOSSIER_INTRANTS).is_dir():
        print("dossier de projet invalide (pas de sous-dossier intrants)", file=sys.stderr)
        return 2

    def _arret(_signum, _frame):
        _ecrire_etat(dossier, statut="interrompu", fin=time.strftime("%Y-%m-%d %H:%M:%S"))
        sys.exit(1)

    signal.signal(signal.SIGTERM, _arret)
    return executer(dossier, complet="--complet" in argv, externe="--externe" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
