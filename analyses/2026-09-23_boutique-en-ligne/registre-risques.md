# Registre des risques — Boutique en ligne « ShoPix » (2026-09-23)

> Résultat de la chaîne E21 (étapes 1–6). Méthode : STRIDE principal + LINDDUN (données personnelles), priorisation DREAD ; CVSS en attente de la CVE réelle du SDK PayFlow.
> **Registre validé** par l'analyste le 2026-09-23 (R-01…R-12, R-14) ; R-13 **rejeté** par décision de l'analyste (consigné en fin de document).

## Registre validé

| ID | Actif | Menace (catégorie) | Proba · Impact · Niveau | Traitement & contre-mesures | Justification & sources | Risque résiduel | Validé par |
|---|---|---|---|---|---|---|---|
| R-01 | Back-office `/admin`, compte admin | Brute force `/admin` (STRIDE-S) | Élevée · Élevé · **Critique** | **Réduire** : MFA, lockout, sessions courtes, sensibilisation | Incident 2024 (~1 000 tent/24 h), pas de lockout ni MFA — `STRIDE-S`, `ISO27002-A8.5.2`, `A6.2`, `A7.2` | Moyen | Analyste · 2026-09-23 |
| R-02 | Données clients | Credential stuffing (hash SHA-1) (STRIDE-S) | Moyenne · Moyen · Moyen | **Réduire** : bcrypt/argon2, 2FA clients, détection connexions anormales | Hash SHA-1 obsolète, réutilisation de mots de passe — `STRIDE-S`, `ISO27002-A8.28`, `A8.5.2` | Faible | Analyste · 2026-09-23 |
| R-03 | Identité ShoPix, domaine | Usurpation identité e-mail + phishing domaine (STRIDE-S) | Moyenne · Élevé · **Élevé** | **Réduire** : secret manager, SPF/DKIM/DMARC, surveillance domaine | Incident 2023 (clé MailJet), avis phishing — `STRIDE-S`, `ISO27002-A8.24`, ANSSI | Moyen | Analyste · 2026-09-23 |
| R-04 | Site web + MySQL | SQLi / exploitation PHP EOL (STRIDE-T) | Moyenne · Élevé · **Élevé** | **Réduire** : requêtes paramétrées, patchs, moindre privilège MySQL | PHP 8.0 EOL, pas de WAF, un compte `shopix` — `STRIDE-T`, `ATT&CK-T1190`, `ISO27002-A8.28`, `A8.2.3` | Moyen | Analyste · 2026-09-23 |
| R-05 | Checkout / PayFlow | SDK PayFlow non patché / webhooks falsifiés (STRIDE-T) | Moyenne · Élevé · **Élevé** | **Réduire + Transférer** : `composer audit`, patch SDK, signature webhooks, DPA | CVE-2023-XXXX placeholder (à confirmer), `composer audit` jamais lancé — `STRIDE-T`, `ATT&CK-T1190`, `ISO27002-A8.8`, `A8.2.3` | Moyen | Analyste · 2026-09-23 |
| R-06 | Actions admin | Répudiation (pas de journalisation) (STRIDE-R) | Élevée · Moyen · **Élevé** | **Réduire** : journalisation horodatée, logs write-only, revue | Aucune journalisation centralisée — `STRIDE-R`, `ISO27002-A8.15`, `A8.16`, `A8.4` | Faible | Analyste · 2026-09-23 |
| R-07 | Clé API PayFlow (`.env`) | Clé versionnée sur GitHub (STRIDE-I) | Moyenne · Élevé · **Élevé** | **Réduire** : `.gitignore` + secret scanning, rotation, secret manager | Incident 2024 (clé sur GitHub 1 mois) — `STRIDE-I`, `ISO27002-A8.24` | Moyen | Analyste · 2026-09-23 |
| R-08 | Sauvegardes + exports | Sauvegardes FTP en clair (STRIDE-I) | Moyenne · Élevé · **Élevé** | **Réduire** : chiffrement dumps, stockage hors mutualisé, pseudonymisation | Dump SQL en clair sur même hébergeur mutualisé — `STRIDE-I`, `ISO27002-A8.4.2`, `A5.36`, `A8.11` | Moyen | Analyste · 2026-09-23 |
| R-09 | Disponibilité (décembre) | Indisponibilité période critique (STRIDE-D) | Moyenne · Élevé · **Élevé** | **Réduire + Transférer** : monitoring, rate-limiting, runbook, cyber-assurance | Pic ×3, pas de monitoring/WAF/CDN, mutualisation — `STRIDE-D`, `ISO27002-A8.14`, `A5.36`, ANSSI | Moyen | Analyste · 2026-09-23 |
| R-10 | VM complète (site + back-office + MySQL) | Élévation de privilège sans segmentation (STRIDE-E) | Élevée · Élevé · **Critique** | **Réduire** : séparation composants, comptes MySQL distincts, re-audit | Site = API = BO = MySQL sur la même VM, un compte plein droits — `STRIDE-E`, `ATT&CK-T1190`, `ISO27002-A8.9`, `A6.2.3` | Moyen | Analyste · 2026-09-23 |
| R-11 | Exports `.csv` | Corrélation / identification (LINDDUN-L/I) | Élevée · Moyen · **Élevé** | **Réduire** : pseudonymisation, minimisation, durée de conservation réduite | Exports complets 24 mois sans pseudonymisation — `LINDDUN-L`, `LINDDUN-I`, `ISO27002-A8.11` | Faible | Analyste · 2026-09-23 |
| R-12 | Données clients | Divulgation en masse (LINDDUN-DI) | Moyenne · Élevé · **Élevé** | **Réduire** : procédure 72 h, chiffrement, DPA, droit à l'oubli | Données européennes, pas de procédure de notification — `LINDDUN-DI`, `ISO27002-A8.4.2`, `A5.4` | Moyen | Analyste · 2026-09-23 |
| R-14 | Sauvegardes + base commandes | Perte de commandes (STRIDE-D) — **modifié** | Moyenne · **Élevé** · **Élevé** | **Réduire** : cron backup, tests de restauration, règle 3-2-1 | Incident 2025 (2 jours perdus), backup manuel jamais testé — `STRIDE-D`, `ISO27002-A5.36`, `A8.16`. **Modification analysée** (2026-09-23) : impact passé à Élevé (perte définitive de données clients), résiduel Moyen | Moyen | Analyste · 2026-09-23 |

## Risque rejeté par l'analyste (2026-09-23)

| ID | Actif | Menace (catégorie) | Proba · Impact · Niveau proposés | Décision | Commentaire |
|---|---|---|---|---|---|
| ~~R-13~~ | Traitements RGPD | Non-conformité RGPD (LINDDUN-NC) | ~~Élevée · Moyen · Élevé~~ | ❌ **REJETÉ** par l'analyste | Non retenu au registre validé. ⚠️ Traçabilité : l'exposition légale subsiste tant que les traitements ne sont pas conformes ; ré-analyse si plainte/contrôle CNIL (suivi `06-validation.md` § 3) |

## Synthèse des niveaux (registre validé — 13 risques)

- **Critique** : R-01, R-10 (2)
- **Élevé** : R-03, R-04, R-05, R-06, R-07, R-08, R-09, R-11, R-12, R-14 (10)
- **Moyen** : R-02 (1)

→ État du registre : **validé par l'analyste le 2026-09-23** (voir `06-validation.md` pour les décisions et le plan de suivi).