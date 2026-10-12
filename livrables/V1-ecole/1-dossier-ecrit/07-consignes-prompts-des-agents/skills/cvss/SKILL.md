---
name: cvss
description: Use to score the severity of a known vulnerability (CVE). CVSS v4.0 (FIRST) gives a 0-10 score with Base/Threat/Environmental metrics. Score measures technical severity, not organizational risk — adjust with environmental metrics.
---

# CVSS — score de gravité des vulnérabilités

*Common Vulnerability Scoring System* (FIRST), version **4.0** (2023). Note **0–10** pour une **vulnérabilité connue** (CVE gérée dans le NIST NVD).

## Échelle de gravité

| Score | Niveau |
|---|---|
| 0,0 | Aucun |
| 0,1 – 3,9 | Faible |
| 4,0 – 6,9 | Moyen |
| 7,0 – 8,9 | Élevé |
| 9,0 – 10,0 | Critique |

## Groupes de métriques (v4.0)

- **Base** — caractéristiques intrinsèques de la vulnérabilité.
- **Menace (Threat)** — exploitabilité actuelle.
- **Environnement** — contexte d'utilisation dans VOTRE organisation (sécurité/vulnérabilité des actifs, exigences).
- **Supplémentaire** — contexte étendu (ex. fournisseur).

## Usage dans le projet

- Pour une menace liée à une CVE : citer `CVE-AAAA-XXXXX` + note CVSS ajustée en environnement.
- **Le score de base ≠ risque pour l'organisation** : l'ajuster avec les métriques d'environnement.
- Niveau final mappé : `faible/moyen/élevé/critique` cf. tableau ci-dessus.

Référence : FIRST, CVSS v4.0 ; NIST NVD (`knowledge_base`).