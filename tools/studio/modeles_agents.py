#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Choix du modèle d'agent pour toute la chaîne, en une commande.

    make agents-modele                     # profil « opencode » (défaut, gratuit)
    make agents-modele PROFIL=ollama      # un modèle Ollama par agent, calibré 12 Go
    make agents-modele PROFIL=ollama DRY=1   # affiche sans écrire

Le profil `ollama` choisit, pour chaque agent, le **premier modèle recommandé déjà
présent** sur le serveur. La liste se donne explicitement, parce que l'outil ne peut
pas interroger le PC GPU depuis le serveur Docker :

    make agents-modele PROFIL=ollama MODELES=llama3.1:8b,mistral:7b,qwen3-vl:8b

Sans cette liste, c'est le premier recommandé qui est retenu — donc un agent peut
pointer un modèle absent du serveur (Ollama le tirera au premier appel, ce qui est
long, voire impossible hors ligne). Les modèles retenus sont affichés avant toute
écriture : `DRY=1` permet de vérifier.

Pourquoi un outil plutôt qu'une édition manuelle : le modèle d'un agent vit dans
son **en-tête `model:`**, et ce même contenu existe à **deux endroits** — la base
du Studio (`stockage_local/e21.sqlite3`, source de vérité) et les fichiers
`.opencode/agents/*.md` (copie déployée). Modifier un seul des deux serait
annulé par l'autre : `make studio-deploy` réécrit les fichiers depuis la base.
Cet outil met donc **les deux à jour dans la même passe**, et il est idempotent :
une deuxième exécution n'écrit rien.

Il ne touche qu'à la ligne `model:` du frontmatter. Le reste de l'agent (consignes,
garde-fous, sources) est conservé caractère par caractère.

Profils :

- `opencode` — `model: opencode/big-pickle` pour tous les agents. C'est le mode par
  défaut : gratuit, et c'est la configuration qui fonctionne sans machine
  supplémentaire. Un agent laissé sans modèle hérite du modèle global d'opencode,
  ce qui est aussi acceptable (`big-pickle` en dur reste plus explicite) ;
- `ollama` — un modèle par agent, d'après `web/modeles_ollama.py` (sélection faite
  pour une carte 12 Go). Les agents sans recommandation recommandée conservent
  leur modèle : on ne remplace jamais un choix existant par « rien ».

Aucune donnée d'analyse n'est touchée, aucun modèle n'est téléchargé ni exécuté.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.studio import db  # noqa: E402  (import après ajustement de sys.path)
from web import modeles_ollama  # noqa: E402  (recommandations par agent)

PROFIL_OPENCODE = "opencode"
MODELE_OPENCODE = "opencode/big-pickle"
PROFILS = (PROFIL_OPENCODE, "ollama")

#: Une ligne `model:` de frontmatter. Volontairement strict : on ne réécrit que
#: ce qui ressemble à un identifiant de modèle known (pas de commentaire, pas de
#: espace, pas de guillemet), pour ne jamais casser un agent malformé.
RE_LIGNE_MODELE = re.compile(r"^model:[ \t]*(\S+)[ \t]*$", re.MULTILINE)

__all__ = ["PROFILS", "MODELE_OPENCODE", "modele_pour", "appliquer_modele",
           "appliquer_profil", "lister_agents", "main"]


def modele_pour(profil: str, agent: str, modeles_disponibles=()) -> str | None:
    """Modèle à écrire pour `agent` selon `profil`, ou `None` pour ne rien changer.

    `None` signifie « ne rien écrire » : uniquement le cas d'un **profil inconnu**
    (refus global). En profil `ollama`, un agent qui n'aurait pas encore de
    recommandation reçoit le modèle par défaut du profil — sinon un agent créé
    après coup resterait sur `big-pickle` alors que l'analyste a demandé « tout le
    monde sur Ollama », et le mélange serait incompréhensible.
    """
    if profil == PROFIL_OPENCODE:
        return MODELE_OPENCODE
    if profil == "ollama":
        modele, _present = modeles_ollama.choisir(agent, modeles_disponibles)
        if modele is None:
            # agent absent de la table : on part du modèle par défaut du profil,
            # et — si l'analyste a déclaré ses modèles installés mais que le
            # défaut n'en fait pas partie — du premier modèle connu réellement
            # installé qui tient dans le budget. On ne pointerait jamais un
            # modèle absent du serveur.
            modele = modeles_ollama.RECOMMANDATION_DEFAUT
            if modeles_disponibles and modele not in set(modeles_disponibles):
                installes = [
                    nom
                    for nom in modeles_disponibles
                    if nom in modeles_ollama.CATALOGUE
                    and modeles_ollama.CATALOGUE[nom]["vram_go"]
                    <= modeles_ollama.VRAM_UTILE_GO
                ]
                if installes:
                    modele = installes[0]
        # opencode résout un modèle via son fournisseur : `ollama/llama3.1:8b`.
        return f"ollama/{modele}"
    return None


def appliquer_modele(contenu: str, modele: str) -> tuple[str, bool]:
    """Remplace la ligne `model:` du frontmatter. Renvoie `(contenu, change)`.

    - frontmatter fermé (`---`) ou ligne `model:` absente : le contenu est renvoyé
      **inchangé** avec `change = False`. On ne fabrique jamais d'en-tête : un agent
      sans `model:` hérite du modèle global, ce qui est une configuration valide ;
    - le reste du fichier est préservé à l'identique.
    """
    if not isinstance(contenu, str) or not modele:
        return contenu, False
    tete = contenu.split("---", 2)
    if len(tete) < 3 or tete[0].strip():
        return contenu, False  # pas d'en-tête délimité par `---`
    trouve = RE_LIGNE_MODELE.search(tete[1])
    if not trouve:
        return contenu, False
    nouveau_bloc = RE_LIGNE_MODELE.sub(f"model: {modele}", tete[1], count=1)
    return "---" + nouveau_bloc + "---" + tete[2], trouve.group(1) != modele


def lister_agents(dossier_agents: Path | None = None) -> list[str]:
    """Noms des agents présents sur disque (sans l'extension)."""
    dossier = Path(dossier_agents) if dossier_agents is not None else db.DOSSIER_AGENTS
    return sorted(p.name[: -len(".md")] for p in dossier.glob("*.md"))


def appliquer_profil(
    profil: str,
    chemin_db: Path | None = None,
    dossier_agents: Path | None = None,
    dry_run: bool = False,
    modeles_disponibles=(),
) -> dict:
    """Applique `profil` à tous les agents, **base Studio et fichiers** en une fois.

    `modeles_disponibles` : tags Ollama réellement installés (voir `main` et le
    `MODELES=` du Makefile). Vide = on prend le premier modèle recommandé.

    Renvoie `{"profil", "modifies": [...], "inchangees": [...], "sans_modele": [...],
    "ecrits_base": int, "ecrits_fichiers": int, "dry_run": bool}`.

    L'ordre est important : on lit la base (source de vérité) si elle contient
    l'agent, sinon le fichier `.opencode/`. Dans les deux cas, le résultat est
    réécrit dans les deux endroits, donc `make studio-deploy` ne peut plus annuler
    le choix.
    """
    if profil not in PROFILS:
        raise ValueError(
            f"Profil inconnu : « {profil} » — attendu : {', '.join(PROFILS)}."
        )
    dossier = Path(dossier_agents) if dossier_agents is not None else db.DOSSIER_AGENTS
    bilan = {
        "profil": profil,
        "modifies": [],
        "inchangees": [],
        "sans_modele": [],
        "ecrits_base": 0,
        "ecrits_fichiers": 0,
        "dry_run": bool(dry_run),
    }
    for agent in lister_agents(dossier):
        modele = modele_pour(profil, agent, modeles_disponibles)
        if modele is None:
            bilan["inchangees"].append(agent)
            continue
        entite = db.lire("agent", agent, chemin_db)
        if entite is not None:
            contenu = entite["contenu"]
        else:
            chemin = dossier / f"{agent}.md"
            if not chemin.is_file():
                bilan["sans_modele"].append(agent)
                continue
            contenu = chemin.read_text(encoding="utf-8")
        nouveau, change = appliquer_modele(contenu, modele)
        cible = dossier / f"{agent}.md"
        fichier_actuel = cible.read_text(encoding="utf-8") if cible.is_file() else None
        if not change and fichier_actuel == contenu:
            bilan["inchangees"].append(agent)
            continue
        bilan["modifies"].append({"agent": agent, "modele": modele})
        if dry_run:
            continue
        if entite is not None:
            # `chemin_db` en MOT CLÉ : le 4e positionnel de `sauvegarder` est
            # `source`, un chemin passé là-bas finirait en base.
            db.sauvegarder("agent", agent, nouveau, source=entite.get("source") or "studio",
                           chemin_db=chemin_db)
            bilan["ecrits_base"] += 1
        if fichier_actuel != nouveau:
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_text(nouveau, encoding="utf-8")
            bilan["ecrits_fichiers"] += 1
    return bilan


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    profil = PROFIL_OPENCODE
    dry_run = False
    modeles: tuple[str, ...] = ()
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--dry-run", "-n"):
            dry_run = True
        elif arg in ("-h", "--help"):
            print(__doc__)
            return 0
        elif arg == "--modeles" and index + 1 < len(argv):
            modeles = tuple(m.strip() for m in argv[index + 1].split(",") if m.strip())
            index += 1
        else:
            profil = arg
        index += 1
    try:
        bilan = appliquer_profil(profil, dry_run=dry_run, modeles_disponibles=modeles)
    except ValueError as exc:
        print(f"Refus : {exc}", file=sys.stderr)
        return 1
    prefixe = "[simulation] " if dry_run else ""
    if modeles:
        print(f"Modèles considérés comme installés : {', '.join(modeles)}")
    print(f"{prefixe}Profil « {profil} » : {len(bilan['modifies'])} agent(s) à "
          f"basculer, {len(bilan['inchangees'])} déjà conforme(s).")
    for entree in bilan["modifies"]:
        print(f"  - {entree['agent']} → model: {entree['modele']}")
    if bilan["sans_modele"]:
        print(f"  (absents de la base et du dossier, ignorés : {bilan['sans_modele']})")
    if not dry_run:
        print(f"Base Studio : {bilan['ecrits_base']} écriture(s) · "
              f"fichiers .opencode/ : {bilan['ecrits_fichiers']} écriture(s).")
        print("Les deux magasins sont alignés : `make studio-deploy` ne ré-annulera rien.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
