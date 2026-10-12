---
name: mitre-attack
description: Use to ground threat scenarios in real attacker behavior. MITRE ATT&CK is a public knowledge base describing what real adversaries do (tactics → techniques → procedures). Complements STRIDE/PASTA with realistic scenarios for detection and red team exercises.
---

# MITRE ATT&CK

Base de connaissances publique (MITRE) des **comportements réels des attaquants**. On l'utilise pour **étayer les scénarios de menace** et comparer aux attaques réelles.

## Organisation

- **Tactique** : le « pourquoi » (objectif de l'attaquant). 14 tactiques de la Reconnaissance à l'Impact (ex. Initial Access, Execution, Persistence, Exfiltration).
- **Technique** : le « comment » (méthode précise, ex. T1566 Phishing, T1190 Exploit Public-Facing Application).
- **Procédure** : la mise en œuvre concrète par un groupe réel (GTAG).

## Usage dans le projet

- Enrichir une menace identifiée avec les **techniques ATT&CK** réalistes pour y parvenir.
- Citer `ATT&CK-T####` dans `sources` (ex. `ATT&CK-T1190`).
- Exemple : menace « intrusion via serveur web exposé » → `ATT&CK-T1190`, `T1505.003`.
- Idéal pour : SOC/détection, exercices Red/Purple Team, mesure de couverture des défenses.

ATT&CK **complète** un modèle de menaces (STRIDE/PASTA) : il apporte des scénarios réalistes.