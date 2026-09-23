# 01 — Architecture

Système multi-agents IA qui assiste un analyste dans l'analyse de risques d'un système informatique. L'humain reste décideur final.

## Vue globale

```
Entrée (description du système)
   │  architecture, flux de données, contexte métier, contraintes (RGPD…)
   ▼
┌────────────── ORCHESTRATEUR ──────────────┐
│ Lance les agents dans l'ordre, fait       │
│ circuler les résultats, gère les reprises,│
│ conserve l'historique (logs JSONL)        │
└──────┬─────────┬─────────┬─────────┬──────┘
   Agent 1      AGent 2    Agent 3   Agent 4   Agent 5
   Inventaire   Modèle     Menaces   Évaluation Traitement
      │           │          │        │          │
      └───────────┴──────────┴────────┴──────────┘
                      │  JSON validé (Pydantic)
                      ▼
              Validation humaine (valide_par)
                      ▼
        Sortie : registre des risques + rapport
```

## Composants

- **Orchestrateur** : processus séquentiel déterministe (CrewAI `Process.sequential`). Reçoit la demande de l'analyste, ordonne les 5 agents, réinjecte la sortie JSON validée de chaque agent dans le suivant.
- **Agents spécialisés** : 5 rôles reproduisant les 6 étapes de l'analyse de risques.
- **Base de connaissances** (`knowledge_base/`) : STRIDE, contre-mesures ISO/ANSSI, CVE — sources à identifiant stable (ex. `STRIDE-S`, `ISO27002-A8.2.3`).
- **Outils (lecture seule)** : lecture de fichiers, recherche CVE (API NVD), calcul du niveau de risque (matrice probabilité×impact).
- **Mémoire partagée** : chaque agent ne lit que le résultat structuré de l'agent précédent.

## Modèle LLM (interface `LlmProvider`)

Trois implémentations interchangeables (une ligne de config) :

| Provider | Usage | Quand |
|---|---|---|
| `ollama` | LLM local (ex. `qwen3:8b`, `mistral-small3.1`) | Nominal — aucune donnée ne sort |
| `api` | OpenAI/Anthropic/Mistral cloud | Secours si réseau/modèle indisponible ou comparaison |
| `mock` | Réponses déterministes à base de règles | **Démo garantie** : prototype toujours fonctionnel |

La bascule se fait via config ; `temperature=0` pour le déterminisme. Les autres fournisseurs ne reçoivent que des données fictives anonymisées.

## Structure du dépôt (prévue)

```
src/
├── schemas.py            # Pydantic : Actif, Menace, Risque, Registre
├── config.py             # provider, modèle, chemins
├── engine/
│   ├── base.py           # interface LlmProvider
│   ├── ollama.py
│   ├── api.py
│   └── mock.py           # mode démo
├── agents/               # inventaire, modele, menaces, evaluation, traitement
├── tools/                # lire_fichier, cve_lookup, calcul_niveau
├── guardrails/           # filtrage_entrees, anonymisation, valider_sources
├── orchestrateur.py      # Crew séquentiel + logs
└── main.py               # CLI / API FastAPI
output/                   # registre_risques.json + rapport.md
logs/                     # échanges JSONL
tests/                    # test_injection.py, test_schemas.py
```

## Positions de sécurité

- Outils **en lecture seule** : aucun agent ne modifie de système réel (moindre privilège).
- Chaque résultat intermédiaire est **vérifiable** et **journalisé**.
- Garde-fous appliqués à **tous** les agents (cf. `04-garde-fous.md`).