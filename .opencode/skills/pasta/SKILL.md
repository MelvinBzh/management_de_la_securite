---
name: pasta
description: Use when the analysis must be aligned with business objectives and driven by the attacker. PASTA is a 7-step method from business goals to attack simulation. Best when executives need to understand impact in business terms.
---

# PASTA — Process for Attack Simulation and Threat Analysis

Méthode **centrée attaquant**, alignée sur le **métier** (UcedaVélez & Morana). En 7 étapes, du métier jusqu'à la simulation d'attaques.

## Les 7 étapes

1. **Définir les objectifs** — objectifs métier + exigences de conformité.
2. **Définir le périmètre technique** — composants, technologies, dépendances.
3. **Décomposer l'application** — flux de données, rôles, frontières de confiance (DFD).
4. **Analyser les menaces** — renseignement sur les menaces réelles (threat intelligence).
5. **Analyser les vulnérabilités** — faiblesses existantes et leurs liens avec les menaces.
6. **Modéliser les attaques** — arbres d'attaque, scénarios, simulations.
7. **Analyser risques et impacts** — impact métier + contre-mesures priorisées.

## Usage dans le projet

- Etapes 4–6 produisent des **scénarios d'attaque concrets** (utile avec ATT&CK).
- Etapes 1 et 7 parlent **métier** → bon choix si la direction décide du traitement.
- Impact exprimé en termes métier (pertes, réputation, conformité).

Référence : UcedaVélez & Morana, *Risk Centric Threat Modeling* (2012-2015).