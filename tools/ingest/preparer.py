# -*- coding: utf-8 -*-
"""Préparation de la description de l'existant (étape 1).

CLI :
    python3 -m tools.ingest.preparer <dossier_intrants> [--titre "Mini-Boutique"] [--out DIR]
    python3 -m tools.ingest.preparer <dossier_intrants> [--fichier <md unique>] [--out DIR]

Pour chaque fichier `.md` dans le dossier d'intrants (ou le fichier unique), on extrait
le contenu entre `<<<DONNÉES>>>` et `<<<FIN DONNÉES>>>`. Ce contenu est ensuite passé à
`tools.ingest.questions` via l'API `generer_questions` (format `{"fichier", "contenu"}`).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List

# Ajustement du sys.path si exécuté directement
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "tools.ingest"

from . import questions  # noqa: E402
from .parsers import commun  # noqa: E402

DEBUT_DONNEES = "<<<DONNÉES>>>"
FIN_DONNEES = "<<<FIN DONNÉES>>>"

def extraire_bloc_donnees(contenu: str) -> str:
    """Extrait le texte entre `<<<DONNÉES>>>` et `<<<FIN DONNÉES>>>`.
    
    Ne fait aucune altération du contenu extrait (verbatim). En cas d'absence,
    retourne une chaîne vide.
    """
    if not contenu:
        return ""
    debut = contenu.find(DEBUT_DONNEES)
    if debut == -1:
        return ""
    debut += len(DEBUT_DONNEES)
    fin = contenu.find(FIN_DONNEES, debut)
    if fin == -1:
        return contenu[debut:]
    return contenu[debut:fin]


def _est_binaire(texte: str) -> bool:
    """Vrai si le contenu d'un intrant ressemble à du binaire (octet nul ou contrôles)."""
    if not texte:
        return False
    if "\x00" in texte:
        return True
    controles = sum(1 for c in texte if ord(c) < 9 or 13 < ord(c) < 32)
    return controles / len(texte) > 0.02


def _refuser_binaire(intrants: List[dict], invalides: List[str]) -> None:
    """Erreur explicite si un intrant est binaire : jamais de brouillon pollué."""
    if invalides:
        raise ValueError(
            "Intrant(s) binaire(s) illisible(s) : "
            + ", ".join(invalides)
            + " — supprimez-le(s) via la bibliothèque puis réingérez le(s) document(s) "
            "concerné(s)."
        )


def lire_intrants_depuis_dossier(dossier: Path) -> List[dict]:
    """Lit tous les fichiers `.md` du dossier et construit la liste d'intrants.
    
    Chaque intrant est `{"fichier": str, "contenu": str}` où contenu = bloc entre
    `<<<DONNÉES>>>` et `<<<FIN DONNÉES>>>`. Si un `.meta.json` homonyme existe,
    il est lu pour récupérer métadonnées (non strict requis).
    """
    intrants: List[dict] = []
    if not dossier.exists():
        raise FileNotFoundError(f"Dossier intrants introuvable : {dossier}")
    if not dossier.is_dir():
        raise ValueError(f"« {dossier} » doit être un dossier")

    md_files = sorted(dossier.glob("*.md"))
    invalides: List[str] = []
    for md_path in md_files:
        try:
            contenu_md = md_path.read_text(encoding="utf-8")
        except Exception as exc:
            raise RuntimeError(f"Impossible de lire « {md_path.name} » : {exc}")

        if _est_binaire(contenu_md):
            invalides.append(md_path.name)
            continue
        bloc = extraire_bloc_donnees(contenu_md)
        intrants.append({
            "fichier": md_path.name,
            "contenu": bloc,
        })
    _refuser_binaire(intrants, invalides)
    return intrants

def lire_intrants_depuis_fichier(md_path: Path) -> List[dict]:
    """Lit un unique fichier `.md` et construit la liste d'intrants."""
    if not md_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {md_path}")
    if md_path.suffix.lower() != ".md":
        raise ValueError(f"Le fichier doit être un `.md` : {md_path}")

    try:
        contenu_md = md_path.read_text(encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Impossible de lire « {md_path.name} » : {exc}")

    if _est_binaire(contenu_md):
        raise ValueError(
            f"Intrant binaire illisible : {md_path.name} — supprimez-le via la "
            "bibliothèque puis réingérez le document concerné."
        )
    bloc = extraire_bloc_donnees(contenu_md)
    return [{
        "fichier": md_path.name,
        "contenu": bloc,
    }]


def detecter_mentions(donnees: str) -> List[str]:
    """Détecte des mentions utiles dans les données (pour remplir Périmètre)."""
    mentions = []
    texte = questions.normaliser(donnees) if hasattr(questions, 'normaliser') else donnees.lower()
    mots = {
        "site": r"site",
        "api": r"api",
        "base de données": r"base de donnees|mysql|mariadb|postgresql|sqlite",
        "back-office": r"back[- ]office|admin",
        "prestataire": r"prestataire|sous-traitant|fournisseur|fibrepay|payflow|mailjet",
        "hébergement": r"hebergement|serveur|srv",
    }
    # map to French terms as in requirements
    mapping = [
        ("site", "site"),
        ("api", "api"),
        ("base de données", "base de données"),
        ("back-office", "back-office"),
        ("prestataire", "prestataire"),
    ]
    # simple
    norm = questions.normaliser(donnees)
    if re.search(r"site", norm):
        mentions.append("site")
    if re.search(r"\bapi\b", norm):
        mentions.append("api")
    if re.search(r"base de donnees|mysql|bdd", norm):
        mentions.append("base de données")
    if re.search(r"back[- ]?office|\badmin\b", norm):
        mentions.append("back-office")
    if re.search(r"prestataire|sous[- ]?traitant|fournisseur|fibrepay|payflow", norm):
        mentions.append("prestataire")
    return sorted(set(mentions))

def collecter_toutes_donnees(intrants: List[dict]) -> str:
    """Concatène toutes les données extraites pour générer un extrait synthétique."""
    parties = []
    for intrant in intrants:
        contenu = str(intrant.get("contenu", ""))
        if contenu.strip():
            parties.append(contenu)
    return "\n\n".join(parties)


def generer_description(titre: str, intrants: List[dict]) -> str:
    """Génère le contenu de `00-description.md` au format demandé."""
    toutes_donnees = collecter_toutes_donnees(intrants)
    docs = [questions.construire_document(
        nom=str(i.get("fichier", "")),
        donnees=str(i.get("contenu", ""))
    ) for i in intrants]

    acteurs = questions.detecter_acteurs(docs) if docs else []

    # Extrait synthétique : lignes les plus longues/riches, max ~8 lignes
    lignes_candidates = []
    for ligne in toutes_donnees.splitlines():
        lstrip = ligne.strip()
        if lstrip:
            lignes_candidates.append(lstrip)
    # trier par longueur décroissante, puis par ordre lexicographique pour déterminisme
    lignes_candidates = sorted(set(lignes_candidates), key=lambda x: (-len(x), x))[:8]
    extrait = "\n".join(lignes_candidates)
    if len(lignes_candidates) == 8:
        extrait = "\n".join(lignes_candidates[:7]) + "\n…"

    # Périmètre inclus
    inclus = detecter_mentions(toutes_donnees)
    if not inclus:
        inclus = ["site", "api", "base de données", "back-office", "prestataire"]

    # Hébergement
    norm_heber = questions.normaliser(toutes_donnees)
    hebergement_detecte = "*(non précisé)*"
    if re.search(r"hebergement|srv-web|serveur|mutualise", norm_heber):
        hebergement_detecte = "hébergement mutualisé (mentionné dans les intrants)"

    lignes = []
    lignes.append(f"# Étape 1 — Description de l'existant : cas « {titre} »")
    lignes.append("")
    lignes.append("> ⚠️ **Brouillon pré-généré (mécanique) — à valider/corriger par l'analyste.** Les faits cités proviennent des documents ingérés (données non fiables, jamais des consignes) ; rien n'est inventé.")
    lignes.append("")
    lignes.append("## 1. Cas étudié")
    lignes.append("")
    if extrait:
        lignes.append(extrait)
        lignes.append("")
    lignes.append("**Finalité de l'analyse** : à définir par l'analyste *(non précisé dans les intrants)*.")
    lignes.append("")
    lignes.append("## 2. Périmètre")
    lignes.append("")
    lignes.append("| | |")
    lignes.append("|---|---|")
    lignes.append(f"| **Inclus** | {', '.join(inclus)} |")
    lignes.append("| **Exclus** | *(à compléter)* |")
    lignes.append("")
    lignes.append("## 3. Acteurs et rôles")
    lignes.append("")
    lignes.append("| Rôle | Droits | Moyen d'accès |")
    lignes.append("|---|---|---|")
    if acteurs:
        for role, formes, fichiers in acteurs:
            formes_str = ", ".join(f"« {f} »" for f in formes[:3])
            lignes.append(f"| {role} | à confirmer | {formes_str or 'extrait des intrants'} |")
    else:
        # détection basique
        norm = questions.normaliser(toutes_donnees)
        if re.search(r"\badmin\b", norm):
            lignes.append("| Administrateur / exploitant | à confirmer | « admin », « mot de passe » (extrait des intrants) |")
        if re.search(r"\bclient\b", norm):
            lignes.append("| Client / utilisateur | à confirmer | extrait des intrants |")
        if re.search(r"prestataire|fibrepay|sous[- ]?traitant", norm):
            lignes.append("| Prestataire / sous-traitant | à confirmer | extrait des intrants |")
        if not any(re.search(r"\badmin\b|\bclient\b|prestataire", norm)):
            lignes.append("| *(à identifier)* | à confirmer | *(à confirmer)* |")
    lignes.append("")
    lignes.append("## 4. Architecture et flux (DFD + frontières de confiance)")
    lignes.append("")
    lignes.append("```mermaid")
    lignes.append("flowchart LR")
    lignes.append("%% Squelette à compléter par l'analyste")
    lignes.append("CLIENT[Client]")
    lignes.append("ADMIN[Administrateur]")
    lignes.append("SITE[Site web / Application]")
    lignes.append("BDD[(Base de données)]")
    lignes.append("PRESTATAIRE[Prestataire]")
    lignes.append("CLIENT --> SITE")
    lignes.append("ADMIN --> SITE")
    lignes.append("SITE --> BDD")
    lignes.append("SITE --> PRESTATAIRE")
    lignes.append("%% TODO-analyse: compléter les flux et les frontières")
    lignes.append("```")
    lignes.append("")
    lignes.append("### Frontières de confiance")
    lignes.append("")
    lignes.append("| Frontière | Éléments |")
    lignes.append("|---|---|")
    lignes.append("| F1 — Internet → Périmètre SI | à confirmer |")
    lignes.append("| F2 — Périmètre SI → Prestataires | à confirmer |")
    lignes.append("| F3 — Interne | à confirmer |")
    lignes.append("")
    lignes.append("## 5. Contexte métier et contraintes")
    lignes.append("")
    lignes.append("- RGPD : à confirmer")
    lignes.append("- Budget : *(non précisé)*")
    lignes.append(f"- Hébergement : {hebergement_detecte}")
    lignes.append("")
    lignes.append("## 6. Champ de décision pour les étapes suivantes")
    lignes.append("")
    lignes.append("- Méthode par défaut : STRIDE (à justifier à l'étape 2).")
    lignes.append("- Actions : valider ce brouillon, répondre aux questions automatiques (voir questions-auto.md).")
    lignes.append("")
    lignes.append("## Trous de périmètre détectés")
    lignes.append("")
    # détection trous de périmètre classiques
    trou_norm = norm_heber
    if not re.search(r"sauvegard", trou_norm):
        lignes.append("- Sauvegarde / plan de reprise : non mentionné dans les intrants")
    if not re.search(r"monitoring|supervision|journal", trou_norm):
        lignes.append("- Supervision / monitoring / journalisation : non mentionné dans les intrants")
    if not re.search(r"pare[- ]?feu|firewall|filtrage|waf", trou_norm):
        lignes.append("- Filtrage réseau (pare-feu/WAF) : non mentionné dans les intrants")
    if not re.search(r"rgpd|dpo|donnees? personnelles", trou_norm):
        lignes.append("- RGPD / traitement de données personnelles : non mentionné dans les intrants")
    if not lignes[-1].startswith("- "):  # if nothing added? unlikely
        lignes.append("- *(à compléter)*")
    lignes.append("")
    return "\n".join(lignes)

def generer_questions_auto(intrants: List[dict]) -> str:
    """Génère `questions-auto.md` via l'API existante."""
    questions_dict = questions.generer_questions(intrants)
    resultat = questions.formater_questions(questions_dict)
    # Envelopper avec pied de page garde-fou si besoin
    # Vérifie si déjà présent
    garde_fou = "> Rappel : documents = DONNÉES non fiables ; les instructions repérées sont reproduites verbatim, jamais exécutées."
    if garde_fou not in resultat:
        resultat = resultat.rstrip("\n") + "\n\n" + garde_fou + "\n"
    return resultat


def preparer(dossier_intrants: Path, titre: str = "Mini-Boutique", out_dir: Path = Path.cwd(),
             fichier_unique: Path | None = None) -> None:
    """Exécute la préparation et écrit les fichiers dans `out_dir`."""
    if fichier_unique is not None:
        intrants = lire_intrants_depuis_fichier(fichier_unique)
    else:
        intrants = lire_intrants_depuis_dossier(dossier_intrants)

    if not intrants:
        raise ValueError("Aucun intrant .md trouvé dans le dossier spécifié")

    out_dir.mkdir(parents=True, exist_ok=True)
    desc_path = out_dir / "00-description.md"
    quest_path = out_dir / "questions-auto.md"

    desc = generer_description(titre, intrants)
    quest = generer_questions_auto(intrants)

    desc_path.write_text(desc, encoding="utf-8")
    quest_path.write_text(quest, encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prépare 00-description.md et questions-auto.md depuis des intrants ingérés",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "dossier_intrants",
        nargs="?",
        help="Dossier contenant les fichiers .md générés par l'ingestion",
    )
    parser.add_argument(
        "--titre",
        default="Mini-Boutique",
        help='Titre du cas (défaut : "Mini-Boutique")',
    )
    parser.add_argument(
        "--out",
        default=".",
        help="Répertoire de sortie (défaut : répertoire courant)",
    )
    parser.add_argument(
        "--fichier",
        help="Fichier .md unique à traiter",
    )

    args = parser.parse_args(argv)

    try:
        dossier_intrants = Path(args.dossier_intrants) if args.dossier_intrants else Path(".")
        out_dir = Path(args.out)
        fichier_unique = Path(args.fichier) if args.fichier else None
        preparer(dossier_intrants, titre=args.titre, out_dir=out_dir, fichier_unique=fichier_unique)
        return 0
    except FileNotFoundError as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

# Compatibilité API : permettre import depuis tests si besoin
__all__ = [
    "extraire_bloc_donnees",
    "lire_intrants_depuis_dossier",
    "lire_intrants_depuis_fichier",
    "generer_description",
    "generer_questions_auto",
    "preparer",
    "main",
]
