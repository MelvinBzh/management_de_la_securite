# Étape 4 — Évaluation des risques (cas ShoPix)

> Produit par la chaîne E21 (étape 4 · évaluer les risques).
> Entrées : `03-menaces.md` (M-01…M-14), `02-methodes.md` (priorisation DREAD + CVSS pour les CVE).
> Statut : proposition — les niveaux seront validés par l'analyste (étape 6).

## 1. Méthode d'évaluation

- **Matrice probabilité × impact** (méthode 6 étapes) → niveau de référence du registre :

| Probabilité \ Impact | Faible | Moyen | Élevé |
|---|---|---|---|
| **Élevée** | Moyen | Élevé | **Critique** |
| **Moyenne** | Faible | Moyen | Élevé |
| **Faible** | Faible | Faible | Moyen |

- **DREAD** (moyenne de 5 critères 1–10) : rang de priorisation pour chaque menace.
- **CVSS v4.0** : pour les seules vulnérabilités connues — **en attente ici** : la `CVE-2023-XXXX` de l'énoncé est un placeholder (aucune référence exacte vérifiable) → pas de note CVSS fabriquée (anti-hallucination), le risque M-05 est noté en DREAD et la note CVSS exacte sera posée dès que la CVE réelle sera identifiée (`composer audit`).

## 2. Tableau d'évaluation

| ID | Menace (rappel) | Probabilité | Impact | **Niveau** | Justification (une phrase) |
|---|---|---|---|---|---|
| **M-01** | Usurpation du compte admin par brute force (`/admin`) | Élevée | Élevé | **Critique** | ~1 000 tentatives/24 h déjà observées (2024), aucun lockout, mot de passe simple, pas de MFA → accès admin total quasi garanti à force |
| **M-02** | Credential stuffing des comptes clients (hash SHA-1) | Moyenne | Moyen | Moyen | Nécessite une liste d'identifiants volée ailleurs ; prise de contrôle d'un compte avec données RGPD à l'appui |
| **M-03** | Usurpation de l'identité « ShoPix » (e-mailing + domaine) | Moyenne | Élevé | **Élevé** | Déjà survenu en 2023 (clé MailJet, 2 jours de spam) ; escroquerie de clients + atteinte durable à la réputation |
| **M-04** | Falsification des données via exploitation du site (PHP EOL, SQLi) | Moyenne | Élevé | **Élevé** | Site exposé sans WAF, PHP 8.0 EOL, requêtes préparées non mentionnées ; une injection = lecture/écriture sur la base |
| **M-05** | Falsification du flux de paiement (SDK PayFlow 2.1 non patché) | Moyenne | Élevé | **Élevé** | Vulnérabilité connue non patchée sur composant de paiement ; exploitation = détournement de transactions (placeholder CVE à confirmer) |
| **M-06** | Répudiation des actions d'administration (aucune journalisation) | Élevée | Moyen | **Élevé** | Aucune trace des exports/actions admin → litiges clients et demandes RGPD impossibles à trancher ; comportement quotidien possible |
| **M-07** | Divulgation de la clé API PayFlow (`.env` versionné) | Moyenne | Élevé | **Élevé** | Déjà survenu (2024, 1 mois sur GitHub, pas de rotation) ; accès au dépôt = paiements frauduleux |
| **M-08** | Divulgation des sauvegardes FTP en clair (mutualisation) | Moyenne | Élevé | **Élevé** | Dump SQL complet déposé sur le même hébergeur mutualisé sans chiffrement ; autre locataire ou tiers = fuite totale |
| **M-09** | Indisponibilité en période critique (nov–déc) | Moyenne | Élevé | **Élevé** | Pic ×3 sans monitoring/WAF/redondance sur VM mutualisée ; CA de décembre irrattrapable |
| **M-10** | Élévation de privilèges par absence de segmentation (F3) | Élevée | Élevé | **Critique** | Site = API = back-office = MySQL sur la même VM, un compte `shopix` plein droits → toute compromission web = compromission totale |
| **M-11** | Corrélation / identification via exports `.csv` non pseudonymisés | Élevée | Moyen | **Élevé** | Exports complets conservés 24 mois sans pseudonymisation ; croisement possible → fichier clients réutilisable |
| **M-12** | Divulgation des données personnelles clients (RGPD art. 33) | Moyenne | Élevé | **Élevé** | Si M-04/M-08/M-10 se réalise, exposition en masse de données de citoyens européens sans procédure de notification préparée |
| **M-13** | Non-conformité RGPD des traitements | Élevée | Moyen | **Élevé** | Non-conformité *actuelle* (registre absent, consentement invalide, droit à l'oubli non automatisé) → contrôle CNIL = mise en demeure/amende |
| **M-14** | Perte de commandes par défaillance de sauvegarde | Moyenne | Moyen | Moyen | Sauvegarde manuelle hebdo sans cron ni test de restauration ; survenu en 2025 (2 jours perdus) |

## 3. Priorisation DREAD

Moyenne des 5 critères (Damage, Reproducibility, Exploitability, Affected users, Discoverability) — notation 1–10.

| Rang | ID | D | R | E | A | D | Moyenne | Priorité |
|---|---|---|---|---|---|---|---|---|
| 1 | **M-10** | 10 | 9 | 7 | 9 | 9 | **8,8** | 🔴 **Critique** |
| 2 | **M-01** | 8 | 8 | 7 | 5 | 10 | **7,6** | 🔴 **Critique** |
| 3 | **M-04** | 9 | 6 | 6 | 9 | 8 | **7,6** | 🟠 |
| 4 | **M-13** | 5 | 9 | 8 | 8 | 8 | **7,6** | 🟠 |
| 5 | **M-02** | 6 | 8 | 7 | 8 | 8 | **7,4** | 🟠 |
| 6 | **M-11** | 6 | 8 | 7 | 8 | 7 | **7,2** | 🟠 |
| 7 | **M-12** | 9 | 6 | 5 | 9 | 7 | **7,2** | 🟠 |
| 8 | **M-09** | 7 | 6 | 6 | 8 | 8 | **7,0** | 🟠 |
| 9 | **M-07** | 9 | 6 | 6 | 7 | 6 | **6,8** | 🟠 |
| 10 | **M-03** | 8 | 5 | 5 | 9 | 7 | **6,8** | 🟠 |
| 11 | **M-08** | 9 | 5 | 4 | 9 | 6 | **6,6** | 🟠 |
| 12 | **M-05** | 9 | 5 | 5 | 7 | 5 | **6,2** | 🟠 |
| 13 | **M-06** | 4 | 8 | 8 | 3 | 6 | **5,8** | 🟡 |
| 14 | **M-14** | 6 | 5 | 5 | 8 | 5 | **5,8** | 🟡 |

**Risques critiques pour la priorisation du traitement (étape 5)** : **M-10** (absence de segmentation → compromission totale) et **M-01** (brute force admin) — à traiter en premier.

## 4. Sources

| ID / référence | Usage |
|---|---|
| Matrice probabilité × impact | Skill `analyse-risques` (méthode 6 étapes) — niveaux de la section 2 |
| `DREAD-D…` | Grille de priorisation (5 critères) — section 3, `knowledge_base/README.md` |
| `CVSS-*` | CVSS v4.0 (FIRST) — prévue pour les CVE réelles ; non notée ici (placeholder `CVE-2023-XXXX` de l'énoncé) |
| `03-menaces.md` (M-01…M-14) | Menaces et descriptions évaluées (elles-mêmes sourcées STRIDE/LINDDUN/ATT&CK-T1190) |
| `etude-de-cas.md` (§ 6, 7, 9, 10) | Faits justifiant probabilités (incidents 2023–2025, absence de mesures) et impacts (règles affaires) |

## 5. Notes

- **CVSS** : non notée pour M-05 (CVE placeholder de l'énoncé — aucune note fabriquée). Action de fiabilisation : lancer `composer audit` pour identifier la CVE réelle du SDK PayFlow et poser la note CVSS v4.0 (avec métriques Environnement : exposition Internet, mutualisation, données RGPD) à la prochaine revue.
- Le niveau de référence utilisé pour la suite est celui de la **matrice** (§ 2) ; le rang DREAD sert d'ordre de traitement.
- Répartition : **2 critiques** (M-01, M-10), **10 élevés** (M-03…M-13 hors M-02/M-14), **2 moyens** (M-02, M-14).