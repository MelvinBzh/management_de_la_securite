# Étape 6 — Validation et suivi (cas ShoPix)

> Produit par la chaîne E21 (étape 6 · valider et suivre).
> **Humain dans la boucle** : ce fichier consigne les décisions de l'analyste/direction. Aucun risque n'est « Done » sans `valide_par` renseigné.
> État : **en attente de la décision de l'analyste** — les questions de validation lui ont été soumises (R-01…R-14).

## 1. Validation des risques

Décision de l'analyste le **2026-09-23** : R-01…R-12 **validés tels quels**, R-13 **rejeté**, R-14 **modifié** (impact/Niveau/Résiduel).

| ID | Niveau proposé | Traitement proposé | Risque résiduel proposé | Décision analyste | Valide par + date |
|---|---|---|---|---|---|
| R-01 | Critique | Réduire (MFA, lockout) | Moyen | **Validé** | Analyste · 2026-09-23 |
| R-02 | Moyen | Réduire (bcrypt/argon2) | Faible | **Validé** | Analyste · 2026-09-23 |
| R-03 | Élevé | Réduire (SPF/DKIM/DMARC) | Moyen | **Validé** | Analyste · 2026-09-23 |
| R-04 | Élevé | Réduire (requêtes paramétrées, patchs) | Moyen | **Validé** | Analyste · 2026-09-23 |
| R-05 | Élevé | Réduire + Transférer | Moyen | **Validé** | Analyste · 2026-09-23 |
| R-06 | Élevé | Réduire (journalisation) | Faible | **Validé** | Analyste · 2026-09-23 |
| R-07 | Élevé | Réduire (rotation, secret manager) | Moyen | **Validé** | Analyste · 2026-09-23 |
| R-08 | Élevé | Réduire (chiffrement, stockage externe) | Moyen | **Validé** | Analyste · 2026-09-23 |
| R-09 | Élevé | Réduire + Transférer (cyber-assurance) | Moyen | **Validé** | Analyste · 2026-09-23 |
| R-10 | Critique | Réduire (séparation composants) | Moyen | **Validé** | Analyste · 2026-09-23 |
| R-11 | Élevé | Réduire (pseudonymisation) | Faible | **Validé** | Analyste · 2026-09-23 |
| R-12 | Élevé | Réduire (procédure 72 h) | Moyen | **Validé** | Analyste · 2026-09-23 |
| ~~R-13~~ | ~~Élevé~~ | ~~Réduire (mise en conformité)~~ | ~~Faible~~ | ❌ **REJETÉ par l'analyste** | — (non validé) |
| R-14 | Moyen → **Élevé** | Réduire (automatisation backups) | Faible → **Moyen** | **Modifié** (impact Élevé : perte définitive de commandes + données clients ; résiduel Moyen conservateur) | Analyste · 2026-09-23 |

## 2. Décisions de la direction (consignées le 2026-09-23)

- **Risques résiduels acceptés** : les résiduels des R-01…R-12 et R-14 (tableau ci-dessus) sont **acceptés** par l'analyste — responsable : admin « Mélanie » (accompagnement prestataire au besoin).
- **R-13 rejeté** : l'analyste a **rejeté** le risque R-13 (non-conformité RGPD). Ce rejet est une décision écrite : le risque n'est pas retenu au registre validé. ⚠️ *Note de traçabilité (WARN, ne remet pas en cause la décision) : la non-conformité RGPD étant un état de fait (registre absent, consentement non prouvé), le rejet du risque ne supprime pas l'exposition légale ; si la donne réglementaire évolue (plainte, contrôle CNIL), une ré-analyse sera déclenchée (cf. § 3).*
- **R-14 modifié** : modification actée (probabilité inchangée Moyenne, impact passé Moyen → **Élevé**, niveau Moyen → **Élevé**, résiduel Faible → **Moyen**) — motivée par l'incident 2025 (perte définitive de commandes et de données clients lors d'une défaillance de sauvegarde) et par la nature irrécupérable de la perte. La modification reste opposable par l'analyste à la prochaine revue.
- **Aucun risque « accepter »** : tous les risques retenus sont traités en **réduire** (et/ou **transférer** pour R-05, R-09).

## 3. Plan de suivi (validé avec l'analyste)

- **Fréquence de revue** : semestrielle (2 revues/an) + revue rapide avant chaque période de fêtes (novembre).
- **Déclencheurs de ré-analyse** :
  - Changement de périmètre (nouveau fournisseur, nouveau prestataire de paiement, changement d'hébergeur) ;
  - Incident de sécurité (réel ou avis de phishing) ;
  - Découverte de la CVE réelle du SDK PayFlow (`composer audit`) → poser la note CVSS (R-05) ;
  - Évolution réglementaire RGPD / réclamation d'une personne concernée / contrôle CNIL → **ré-ouvre l'examen de R-13 (rejeté)**.
- **Responsable** : admin « Mélanie » (seule personne) — accompagnement prestataire au besoin ; référent RGPD non désigné pour l'instant (suite au rejet de R-13).
- **Prochaine revue** : mars 2027 (ou avant si incident).