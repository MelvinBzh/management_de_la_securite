"""Modèles Ollama recommandés par agent E21, pour une RTX 5070 (12 Go de VRAM).

## Pourquoi ce module

Les agents E21 ont tous `model: opencode/big-pickle` dans leur en-tête : c'est la
configuration **par défaut**, celle qui fonctionne, et elle ne doit pas bouger. Ce
module ne sert donc **qu'au profil `ollama`** : quand l'analyste veut faire tourner
la chaîne sur son GPU local, chaque agent a besoin d'un modèle *adapté à son travail*
et **suffisamment léger pour tenir dans 12 Go de VRAM**.

## Règles suivies pour les choix

- **Un seul modèle chargé à la fois** : sur 12 Go, deux modèles de 8 Go en
  quantification Q4 ne tiennent pas (2 × ~6 Go de poids + contexte). Les
  recommandations supposent `OLLAMA_MAX_LOADED_MODELS=1` sur le PC GPU.
- **Q4_K_M par défaut** (le tag `:8b` d'Ollama est déjà quantifié) : un 7-8 Go
  tient dans ~6-7 Go, il reste de la place pour le cache KV (une fenêtre de
  contexte de 8k-16k tokens).
- **Pas de « gros » modèle** : 14 Go et plus sont hors budget sur cette carte, donc
  aucun modèle 12b+ n'est proposé — même « en Q4 », un 12b dépasse 12 Go de VRAM
  utile une fois le contexte et le runtime de GPU pris en compte.
- **Pas de modèle d'embeddings** (`nomic-embed-text`) comme modèle d'agent : c'est un
  encodeur, il ne génère pas de texte et ne peut pas mener une analyse.
- **Le français compte** : les livrables E21 sont rédigés en français, `llama3.1:8b`
  et `mistral:7b` s'en acquittent bien ; c'est le critère de départ entre eux.
- **Les images** : l'application fait l'OCR **localement** (Tesseract), donc aucun
  agent n'a besoin d'un modèle vision. Si l'analyste veut malgré tout faire lire
  une image par un modèle, `qwen3-vl:8b` est le seul recommandé ici.

## Ce que ce module ne fait PAS

Il ne modifie **aucun** fichier : c'est une table de conseil, lisible et testable.
Appliquer un modèle à un agent passe par son en-tête (`model:`), c'est-à-dire par
l'onglet **Studio E21** de l'interface, puis `make studio-deploy`. Écrire un modèle
Ollama depuis la page Réglages_modelses sans passer par le Studio reviendrait à créer
une seconde source de vérité pour les agents — c'est exactement ce que la suite
T-20 interdit.
"""
from __future__ import annotations

__all__ = [
    "VRAM_DISPONIBLE_GO",
    "CATALOGUE",
    "RECOMMANDATIONS",
    "JUSTIFICATION",
    "installe",
    "recommandation_pour",
    "choisir",
    "table_recommandations",
]

#: Budget VRAM de la carte visée (RTX 5070, 12 Go). Marge de sécurité pour le
#: runtime CUDA et le cache de contexte, d'où 11 Go utiles retenus comme plafond.
VRAM_DISPONIBLE_GO = 12
VRAM_UTILE_GO = 11

#: Catalogue des modèles candidats : identifiant Ollama, VRAM estimée en Go (Q4),
#: points forts, rôle principal. `vision` signale un modèle qui lit les images.
CATALOGUE: dict[str, dict] = {
    "llama3.1:8b": {
        "vram_go": 6.5,
        "points_forts": "raisonnement général, suivi des consignes longues, bon français",
        "vision": False,
        "role": "Analyse et raisonnement (le plus polyvalent)",
    },
    "mistral:7b": {
        "vram_go": 5.5,
        "points_forts": "rapide, rédaction fluide en français, bon rapport qualité/vitesse",
        "vision": False,
        "role": "Rédaction et synthèses (rapide)",
    },
    "qwen3-vl:8b": {
        "vram_go": 7.5,
        "points_forts": "lit les images ET le texte (multimodal), français correct",
        "vision": True,
        "role": "Lecture d'images (si l'OCR ne suffit pas)",
    },
    "qwen2.5:7b": {
        "vram_go": 6.0,
        "points_forts": "excellent sur les tâches structurées (JSON, tableaux, sources)",
        "vision": False,
        "role": "Sorties structurées (registre, tableaux de critères)",
    },
    "llava:7b": {
        "vram_go": 6.5,
        "points_forts": "lecteur d'images ancien, moins précis que qwen3-vl",
        "vision": True,
        "role": "Alternative vision (dépréciée : préférer qwen3-vl:8b)",
    },
    "nomic-embed-text:latest": {
        "vram_go": 1.0,
        "points_forts": "vecteurs de similarité — PAS un modèle de génération",
        "vision": False,
        "role": "Recherche sémantique uniquement (interdit comme modèle d'agent)",
    },
}

#: Un modèle d'agent par défaut : le plus polyvalent qui tient dans le budget.
RECOMMANDATION_DEFAUT = "llama3.1:8b"

#: Recommandation par agent. Ordre = préférence ; le premier modèle **installé**
#: parmi la liste est retenu, sinon le premier de la liste (avec la commande
#: `ollama pull` affichée à l'analyste).
RECOMMANDATIONS: dict[str, list[str]] = {
    # --- chaîne E21 (ordre des 6 étapes)
    "orchestrator": ["llama3.1:8b"],
    "e21-analyse-existant": ["llama3.1:8b"],
    "e21-choix-methode": ["llama3.1:8b", "qwen2.5:7b"],
    "e21-menaces": ["llama3.1:8b"],
    "e21-evaluation": ["qwen2.5:7b", "llama3.1:8b"],
    "e21-traitement": ["mistral:7b", "llama3.1:8b"],
    "e21-validation-suivi": ["llama3.1:8b"],
    "e21-synthese": ["mistral:7b", "llama3.1:8b"],
    "e21-controle": ["llama3.1:8b"],
    # --- agents annexes
    "github-manager": ["llama3.1:8b"],
    "research": ["llama3.1:8b"],
    "security": ["llama3.1:8b"],
    # --- cas particulier : lecture d'image
    "vision (images/PDF)": ["qwen3-vl:8b", "llava:7b"],
}

#: Pourquoi ce choix, en une phrase par agent (affiché dans la page).
JUSTIFICATION: dict[str, str] = {
    "orchestrator": "Il ne doit qu'orchestrer et déléguer : le suivi des consignes "
                    "compte plus que la profondeur d'analyse.",
    "e21-analyse-existant": "Inventaire d'actifs à partir d'ingested textuel : "
                            "il faut de la rigueur et ne rien inventer.",
    "e21-choix-methode": "Arbitrage méthodique (STRIDE, EBIOS, LINDDUN…) : le raisonnement "
                         "prime, d'où llama3.1 en premier.",
    "e21-menaces": "Déduire des menaces plausibles : c'est le cœur métier, modèle le "
                   "plus capable.",
    "e21-evaluation": "Scores, moyennes et tableaux de critères : la régularité des "
                      "sorties structurées compte plus que la prose (qwen2.5 d'abord).",
    "e21-traitement": "Plan de traitement : rédaction claire et rapide, mistral suffit.",
    "e21-validation-suivi": "Contrôle avant validation humaine : il doit rester fidèle "
                            "au registre, sans initiative.",
    "e21-synthese": "Synthèse finale rédigée : vitesse et qualité de français, "
                     "mistral en premier.",
    "e21-controle": "Garde-fous (injection, sources, anonymisation) : les faux positifs "
                    "d'un modèle vif sont coûteux, on prend le plus posé.",
    "github-manager": "PR, issues, commits : syntaxe exacte avant tout.",
    "research": "Documentation et sources : même prudence sur les citations.",
    "security": "Analyse de vulnérabilités : raisonnement, d'où le modèle le plus capable.",
    "vision (images/PDF)": "Seul cas où un modèle voit une image. En pratique l'OCR "
                           "local suffit : ce modèle n'est nécessaire que si un document "
                           "scanné reste illisible.",
}


def installe(modele: str, modeles_disponibles) -> bool:
    """Vrai si `modele` figure parmi les modèles déjà installés/détectés."""
    return modele in set(modeles_disponibles or ())


def recommandation_pour(agent: str) -> list[str]:
    """Modèles recommandés pour un agent (liste vide si agent inconnu)."""
    return list(RECOMMANDATIONS.get(agent, []))


def choisir(agent: str, modeles_disponibles) -> tuple[str | None, bool]:
    """Choisit le modèle d'un agent parmi ceux déjà installés.

    Renvoie `(modele, deja_installe)` :
    - `modele` est le premier recommandé **installé**, sinon le premier recommandé
      (l'analyste devra alors le télécharger) ;
    - `deja_installe` indique si le choix est utilisable immédiatement.
    `None` en modèle quand l'agent n'a aucune recommandation.
    """
    candidats = recommandation_pour(agent)
    if not candidats:
        return None, False
    for modele in candidats:
        if installe(modele, modeles_disponibles):
            return modele, True
    return candidats[0], False


def table_recommandations(modeles_disponibles) -> list[dict]:
    """Lignes prêtes à afficher : agent, modèle retenu, VRAM, statut, pourquoi.

    `modeles_disponibles` : sortie de `reglages.sonder` (liste des tags détectés) —
    un modèle absent est signalé comme « à installer », avec la commande.
    """
    lignes: list[dict] = []
    for agent, candidats in RECOMMANDATIONS.items():
        modele, present = choisir(agent, modeles_disponibles)
        infos = CATALOGUE.get(modele or "", {})
        lignes.append({
            "Agent": agent,
            "Modèle Ollama": modele or "—",
            "VRAM (Go)": round(infos.get("vram_go", 0.0), 1),
            "Statut": "installé" if present else f"à installer : `ollama pull {modele}`",
            "Pourquoi": JUSTIFICATION.get(agent, ""),
        })
    return lignes
