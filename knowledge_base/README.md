# Base de connaissances — index des sources

Chaque menace / contre-mesure / niveau cité dans une analyse DOIT référencer un **ID stable** de cette base. Les ID sont vérifiés par `e21-controle` (rejet si inconnu).

## Grilles de menaces
| ID | Source | Usage |
|---|---|---|
| `STRIDE-S` | Spoofing — Microsoft, *Uncovering Security Design Flaws* | Usurpation d'identité |
| `STRIDE-T` | Tampering — id. | Altération |
| `STRIDE-R` | Repudiation — id. | Répudiation |
| `STRIDE-I` | Information Disclosure — id. | Fuite |
| `STRIDE-D` | Denial of Service — id. | Indisponibilité |
| `STRIDE-E` | Elevation of Privilege — id. | Élévation de privilège |
| `LINDDUN-L` | Linkability | Vie privée (KU Leuven) |
| `LINDDUN-I` | Identifiability | id. |
| `LINDDUN-N` | Non-repudiation (absence de déni) | id. |
| `LINDDUN-D` | Detectability | id. |
| `LINDDUN-DI` | Disclosure of Information | id. |
| `LINDDUN-UA` | Unawareness | id. |
| `LINDDUN-NC` | Non-compliance | id. |
| `ATT&CK-T1190` | MITRE ATT&CK, Exploit Public-Facing Application | Techniques d'attaque |
| `PASTA-*` | Process for Attack Simulation & Threat Analysis | Centré métier/attaquant |
| `DREAD-D`… | Damage potential / Reproducibility / Exploitability / Affected users / Discoverability | Priorisation |
| `CVSS-*` | Common Vulnerability Scoring System v4.0 (FIRST) | Note 0–10 d'une CVE |

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

## Contre-mesures (baseline)
| ID | Mesure |
|---|---|
| `ISO27002-A5.3` | Séparation des tâches |
| `ISO27002-A5.4` | Responsabilités de gestion |
| `ISO27002-A6.2` | Contrôle d'accès (principes généraux) |
| `ISO27002-A6.2.3` | Gestion des privilèges d'accès |
| `ISO27002-A6.3` | Responsabilité des équipements utilisateur |
| `ISO27002-A7.2` | Sensibilisation, formation, compétences |
| `ISO27002-A7.7` | Travail à distance |
| `ISO27002-A7.9` | Règles d'usage des équipements |
| `ISO27002-A8.1.1` | Gestion des logiciels (anti-malware une ligne) |
| `ISO27002-A8.2.3` | Correctifs logiciens (patch management) |
| `ISO27002-A8.3.2` | Analyse des vulnérabilités techniques |
| `ISO27002-A8.4` | Journalisation et surveillance |
| `ISO27002-A8.5.2` | Authentification sécurisée (MFA) |
| `ISO27002-A8.8` | Gestion des vulnérabilités techniques |
| `ISO27002-A8.9` | Gestion de config |
| `ISO27002-A8.11` | Masquage de données |
| `ISO27002-A8.15` | Journalisation |
| `ISO27002-A8.16` | Opérations de journalisation |
| `ISO27002-A8.25` | Cycle de vie du développement sécurisé |
| `ISO27002-A8.26` | Exigences de sécurité des applications |
| `ISO27002-A8.28` | Codage sécurisé |
| `ISO27002-A8.29` | Sécurité des tests de sécurité |
| `ISO27002-A8.34` | Protection des informations système pendant les tests |
| `ISO27002-A8.4.2` | Chiffrement des données au repos / en transit |
| `ISO27002-A8.24` | Clés cryptographiques |
| `ISO27002-A5.36` | Continuité de l'activité |
| `ISO27002-A8.14` | Redondance / haute disponibilité |
| `ANSSI-*` | Guides ANSSI (recommandations de sécurité) — cf. section « Référentiels ANSSI officiels » |

## Documents de référence (sujet)
- Sujet E21 : `documentation/E21_Management_de_la_sécurité_—_Projet_Agents_IA_pour_l'analyse_de_risques.pdf` (dossier, p. 28 checklist, méthode 6 étapes).
- Support CISSP Partie 1 : `documentation/E21_Management_de_la_sécurité_—_Support_CISSP_Partie_1_compressed.pdf` (threat modeling, chap. 10).

## Règles pour les agents
- Une **source** = un ID de cet index (ou une référence exacte CVE / document fourni).
- Toute source inconnue est rejetée par `e21-controle` (anti-hallucination).
- Chiffrer plutôt que masquer selon la sensibilité (chiffrement ≠ seul remède).