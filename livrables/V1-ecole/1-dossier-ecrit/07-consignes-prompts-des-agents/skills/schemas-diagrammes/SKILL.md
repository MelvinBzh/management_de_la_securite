---
name: schemas-diagrammes
description: Use when producing architecture or structure diagrams in markdown documents. Provides the Mermaid patterns and styling conventions for the risk-analysis system: global architecture, agent chain, DFD with trust boundaries, sequence of agent exchanges, pipeline of the 6 steps.
---

# Schémas & diagrammes (Mermaid)

Toute documentation contient des schémas **rendus en Mermaid** (compatibles GitHub/markdown). Convention de style : **cohérent, lisible, français**, couleurs douces par rôle.

## 1. Architecture globale (flowchart)

```mermaid
flowchart TB
    ENTREE["Entrée : description du système<br/>architecture ✓ flux ✓ contexte métier"]
    ORCH["🧭 Orchestrateur<br/>collecte, planifie, lance la chaîne, journalise"]
    KNOW["📚 Base de connaissances<br/>STRIDE · LINDDUN · ATT&CK<br/>ISO 27002 · EBIOS RM · ANSSI"]
    OUT["👤 Humain dans la boucle<br/>relit · corrige · décide"]
    SORTIE["📄 Sortie : registre des risques validé<br/>+ rapport + dossier d'analyse"]

    ENTREE --> ORCH
    ORCH --> KNOW
    ORCH --> OUT
    OUT --> SORTIE
```

## 2. Chaîne d'agents (6 étapes)

```mermaid
flowchart LR
    A1["1 · Existant<br/>actifs + valeur"] --> A2["2 · Méthode<br/>choix + justification"]
    A2 --> A3["3 · Menaces<br/>par actif/frontière"]
    A3 --> A4["4 · Évaluation<br/>proba × impact"]
    A4 --> A5["5 · Traitement<br/>réponses + mesures"]
    A5 --> A6["6 · Validation<br/>risque résiduel"]
    A6 --> SYN["✍️ Synthèse finale"]
    CONTROLE["🛡️ Garde-fous : sources ✓ injection ✓ anonymisation ✓"] -.vérifie chaque sortie.-> A1
    CONTROLE -.-> A2
    CONTROLE -.-> A3
    CONTROLE -.-> A4
    CONTROLE -.-> A5
    CONTROLE -.-> A6
```

## 3. DFD + frontières de confiance

```mermaid
flowchart LR
    subgraph INTERNET["Frontière : Internet"]
        CLIENT["Utilisateur"]
    end
    subgraph DMZ["Frontière : DMZ"]
        WEB["Serveur web"]
    end
    subgraph INT["Frontière : Réseau interne"]
        BDD["Base de données clients"]
        ADMIN["Back-office admin"]
    end
    CLIENT -->|HTTPS| WEB
    WEB -->|SQL interne| BDD
    ADMIN --> BDD
```

## 4. Échanges entre agents (sequenceDiagram)

```mermaid
sequenceDiagram
    participant O as Orchestrateur
    participant A as Agent (existant)
    participant B as Agent (méthodes)
    O->>A: description du système
    A-->>O: 01-actifs.md (JSON)
    O->>B: actifs + contexte
    B-->>O: 02-methodes.md (choix justifié)
```

## Règles

- Un schéma doit illustrer UNE idée ; les diagrammes riches référencent les composants (agents, base de connaissances, garde-fous).
- Mentionner systématiquement les **garde-fous** et la **validation humaine** dans les schémas.