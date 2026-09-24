# Base de connaissances — index des sources

Chaque menace / contre-mesure / niveau cité dans une analyse DOIT référencer un **ID stable** de cette base. Les ID sont vérifiés par `e21-controle` (rejet si inconnu).

> **Correction (2026-09-24, issue #15)** : l'ancien index mélangeait des identifiants ISO 27002:2013 et des références non standard (format « code A »). L'index est désormais **ISO/IEC 27002:2022 canonique** (codes à deux chiffres) ; une table de correspondance 2013→2022 est fournie en bas de page, à titre de documentation. Les registres ont été ré-indexés en conséquence.

## Grilles de menaces

| ID | Source | Usage |
|---|---|---|
| `STRIDE-S` | Spoofing — Microsoft (A. Shostack) | Usurpation d'identité |
| `STRIDE-T` | Tampering — id. | Altération |
| `STRIDE-R` | Repudiation — id. | Répudiation |
| `STRIDE-I` | Information Disclosure — id. | Fuite |
| `STRIDE-D` | Denial of Service — id. | Indisponibilité |
| `STRIDE-E` | Elevation of Privilege — id. | Élévation de privilège |
| `LINDDUN-L` | Linkability — KU Leuven | Vie privée : corrélation |
| `LINDDUN-I` | Identifiability — id. | Vie privée : identification |
| `LINDDUN-N` | Non-repudiation (absence de déni) — id. | Vie privée : non-répudiation |
| `LINDDUN-D` | Detectability — id. | Vie privée : détectabilité |
| `LINDDUN-Disclosure` | Disclosure of Information — id. | Vie privée : divulgation |
| `LINDDUN-Unawareness` | Unawareness — id. | Vie privée : méconnaissance |
| `LINDDUN-NC` | Non-compliance — id. | Vie privée : non-conformité |
| `EBIOS-RM-2018` | EBIOS Risques Manager (ANSSI) | Analyse organisationnelle, 5 ateliers |
| `EBIOS-RM-A3` | EBIOS RM — atelier 3, scénarios stratégiques & cartographie de la menace | Chemins d'attaque (source → objectif → frontières) |
| `EBIOS-RM-A4` | EBIOS RM — atelier 4, appréciation des risques | Gravité × vraisemblance, seuils d'acceptation |
| `ATT&CK-T1190` | MITRE ATT&CK, *Exploit Public-Facing Application* | Techniques d'attaque réelles |
| `PASTA-*` | Process for Attack Simulation & Threat Analysis | Centré métier/attaquant |
| `DREAD-D`… | Damage / Reproducibility / Exploitability / Affected users / Discoverability (Microsoft) | Priorisation |
| `CVSS-*` | Common Vulnerability Scoring System v4.0 (FIRST) | Note 0–10 d'une CVE |

## Contre-mesures — ISO/IEC 27002:2022 (canonique)

| ID | Mesure (libellé officiel — EN / FR) |
|---|---|
| `ISO27002-5.3` | Segregation of duties — Séparation des tâches |
| `ISO27002-5.4` | Management responsibilities — Responsabilités de la direction |
| `ISO27002-5.15` | Access control — Contrôle d'accès |
| `ISO27002-5.19` | Information security in supplier relationships — Sécurité de l'information dans les relations avec les fournisseurs |
| `ISO27002-5.30` | ICT readiness for business continuity — Préparation TIC pour la continuité d'activité (transfert de risque : assurance) |
| `ISO27002-6.3` | Information security awareness, education and training — Sensibilisation, éducation et formation |
| `ISO27002-8.2` | Privileged access rights — Droits d'accès privilégiés |
| `ISO27002-8.5` | Secure authentication — Authentification sécurisée |
| `ISO27002-8.8` | Management of technical vulnerabilities — Gestion des vulnérabilités techniques |
| `ISO27002-8.11` | Data masking — Masquage des données |
| `ISO27002-8.13` | Information backup — Sauvegarde de l'information |
| `ISO27002-8.14` | Redundancy of information processing facilities — Redondance des moyens de traitement |
| `ISO27002-8.15` | Logging — Journalisation |
| `ISO27002-8.16` | Monitoring activities — Activités de surveillance |
| `ISO27002-8.22` | Separation of networks — Séparation des réseaux (segmentation) |
| `ISO27002-8.24` | Use of cryptography — Utilisation de la cryptographie |
| `ISO27002-8.25` | Secure development life cycle — Cycle de vie de développement sécurisé |
| `ISO27002-8.26` | Application security requirements — Exigences de sécurité des applications |
| `ISO27002-8.28` | Secure coding — Codage sécurisé |
| `ISO27002-8.29` | Security testing in development and acceptance — Tests de sécurité en développement et acceptation |
| `ISO27002-8.34` | Protection of information systems during audit testing — Protection des SI pendant les tests d'audit |
| `ANSSI-*` | Guides ANSSI (recommandations de sécurité) |

## Correspondance ISO 27002:2013 → 2022 (documentation — ne pas citer les codes 2013 dans les registres)

Correspondances principales (annexe officielle de l'ISO/IEC 27002:2022) :

| 2013 | 2022 | Contrôle |
|---|---|---|
| A9.1.2 | 5.3 | Séparation des tâches |
| A9.1.2, A9.4.4 | 5.15 | Contrôle d'accès |
| A15.1.1, A15.2.1 | 5.19 | Relations fournisseurs |
| A17.1.1, A17.2.1 | 5.30 | Préparation TIC / continuité |
| A7.2.2 | 6.3 | Formation et sensibilisation |
| A9.2.3 | 8.2 | Droits d'accès privilégiés |
| A9.4.2 | 8.5 | Authentification sécurisée |
| A12.6.1 | 8.8 | Gestion des vulnérabilités |
| A12.4.1, A12.4.3 | 8.15 / 8.16 | Journalisation et surveillance |
| A12.3.1 | 8.13 | Sauvegarde de l'information |
| A8.2.3, A8.8 | 8.8 | Correctifs / vulnérabilités |
| A10.1.1 | 8.24 | Utilisation de la cryptographie |
| A13.1.3 | 8.22 | Séparation des réseaux |

> L'ancien index contenait aussi des identifiants non standard (ex. codes `A5.36`, `A8.1.1`, `A8.4.2`, `A8.5.2` de l'ancien format). Ils ont été ré-indexés vers les codes 2022 ci-dessus — seul le format canonique `ISO27002-<code 2022>` fait foi, tout `ISO27002-A*` est refusé par le contrôleur.

## Référentiels ANSSI officiels (par étape de la chaîne e21)
Chaque agent de la chaîne ancre sa réflexion sur un référentiel ANSSI précis (documents publiés sur cyber.gouv.fr / messervices.cyber.gouv.fr). Citer l'ID dans les sorties.

| ID | Source (ANSSI) | Agent e21 ciblé | Usage |
|---|---|---|---|
| `ANSSI-CARTO-SI` | *Cartographie du système d'information — Guide d'élaboration en 5 étapes* (ANSSI, 2018) | e21-analyse-existant | Vues (métier/applicative/architecture), objets + attributs, granularité, sensibilité |
| `EBIOS-RM-2018` | *EBIOS Risk Manager* (ANSSI, 2018) | e21-choix-methode | Méthode française de référence (5 ateliers), option OIV/administration |
| `EBIOS-RM-A3` | EBIOS RM — **atelier 3**, scénarios stratégiques & cartographie de la menace | e21-menaces | Raisonner en chemins d'attaque : source de risque → objectif visé → frontières |
| `EBIOS-RM-A4` | EBIOS RM — **atelier 4**, appréciation des risques | e21-evaluation | Gravité × vraisemblance → niveau, seuils d'acceptation |
| `ANSSI-HYGIENE` | *Guide d'hygiène informatique* (ANSSI) | e21-traitement | Mesures de base numérotées (MFA, correctifs, sauvegardes…) |
| `ANSSI-RECYF` | *Référentiel Cyber France (ReCyF)* (ANSSI, 2026) — NIS2 | e21-traitement | Objectifs de sécurité + moyens acceptables de conformité |
| `ANSSI-HOMOLOGATION` | *Guide de l'homologation de sécurité* (ANSSI, 2025) | e21-validation-suivi | Acceptation formelle des risques résiduels par l'autorité, revue |
| `ANSSI-IA-GEN` | *Recommandations de sécurité pour un système d'IA générative* (ANSSI, 2024) | e21-controle | Manipulation, infection des données, exfiltration, contrôle humain |
| `ANSSI-PSSI` | *Guide pour l'élaboration d'une PSSI* (ANSSI) | e21-synthese | Notes de synthèse, plan d'action, orientation décision |

## Documents de référence (sujet)

- Sujet E21 : `documentation/E21_Management_de_la_sécurité_—_Projet_Agents_IA_pour_l'analyse_de_risques.pdf` (dossier, p. 28 checklist, méthode 6 étapes).
- Support CISSP Partie 1 : `documentation/E21_Management_de_la_sécurité_—_Support_CISSP_Partie_1_compressed.pdf` (threat modeling, chap. 10).

## Règles pour les agents

- Une **source** = un ID de cet index (ou une référence exacte CVE / document fourni).
- Toute source inconnue est rejetée par `e21-controle` (anti-hallucination) — en particulier tout code `ISO27002-A*` (2013) est **refusé**.
- Chiffrer plutôt que masquer selon la sensibilité (chiffrement ≠ seul remède).