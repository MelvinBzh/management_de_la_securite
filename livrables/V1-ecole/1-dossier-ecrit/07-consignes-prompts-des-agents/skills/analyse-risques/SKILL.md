---
name: analyse-risques
description: Use when performing or reviewing an IT risk analysis. Encodes the 6-step method (identifier les actifs, choisir une méthode, identifier les menaces, évaluer les risques, traiter les risques, valider et suivre), the probability×impact matrix and the four risk treatments (réduire, transférer, éviter, accepter). Core skill for every e21 risk-analysis agent.
---

# Analyse de risques — méthode 6 étapes

Référence : projet E21 « Des agents IA pour analyser les risques », M2 Cybersécurité. L'humain reste responsable de la décision finale.

## Les 6 étapes (→ un agent/une étape)

1. **Identifier les actifs** — lister ce qui a de la valeur, estimer cette valeur (tangibles : coût de remplacement ; intangibles : perte de revenus, valeur pour un concurrent, réputation).
2. **Choisir une méthode** — décider quelle grille de menaces utiliser et **justifier** le choix (cf. skills des frameworks : STRIDE, LINDDUN, PASTA, MITRE ATT&CK, EBIOS RM, DREAD, CVSS…).
3. **Identifier les menaces** — chercher ce qui peut mal tourner pour chaque actif et à chaque **frontière de confiance**.
4. **Évaluer les risques** — noter probabilité et impact, en déduire le niveau via la matrice.
5. **Traiter les risques** — choisir une réponse et des contre-mesures.
6. **Valider et suivre** — faire relire, décider (direction), accepter le risque résiduel, revoir régulièrement.

## Matrice probabilité × impact (niveau de risque)

| Probabilité \ Impact | Faible | Moyen | Élevé |
|---|---|---|---|
| **Élevée** | Moyen | Élevé | Critique |
| **Moyenne** | Faible | Moyen | Élevé |
| **Faible** | Faible | Faible | Moyen |

Autres grilles possibles : **DREAD** (5 critères notés 1–10), **CVSS** (note 0–10 pour une vulnérabilité connue). On en choisit **une** et on la justifie.

## Les 4 traitements du risque

- **Réduire** — contre-mesures qui baissent la probabilité ou l'impact (MFA, correctifs).
- **Transférer** — faire porter le risque par un tiers (cyber-assurance).
- **Éviter** — arrêter l'activité qui crée le risque (fermer un service exposé).
- **Accepter** — garder le risque par décision écrite de la direction (risque faible, coûteux à traiter).

⚠️ **Ignorer un risque sans décision n'est jamais une réponse acceptable.**

## Registre des risques (le livrable)

Tableau listant chaque risque : identifiant, description, actif concerné, catégorie de menace, probabilité/impact/niveau, traitement + contre-mesures, justification + sources, risque résiduel + validation. Voir le skill `registre-risques`.