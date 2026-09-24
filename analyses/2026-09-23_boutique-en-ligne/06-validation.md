# Étape 6 — Validation et suivi (cas ShoPix)

> Produit par la chaîne E21 (étape 6 · valider et suivre).
> **Humain dans la boucle** : ce fichier consigne les décisions de l'analyste/direction. Aucun risque n'est « Done » sans `valide_par` renseigné.
> État : **dossier validé par l'analyste le 2026-09-24** (R-01…R-14) — le seul point resté ouvert est l'**arbitrage budgétaire cyber-assurance** (note § 3 de `05-traitement.md`, suivi en issue #20).

## 1. Validation des risques

Décision de l'analyste le **2026-09-24** : R-01…R-12 **validés tels quels**, R-13 **retenu** (le rejet initial décidé le 23/09 — un essai du circuit de validation — **est reconsidéré** le 24/09 : la non-conformité étant un état de fait, le risque est retenu au registre, cf. § 2), R-14 **modifié** (impact/Niveau/Résiduel).

| ID | Niveau proposé | Traitement proposé | Risque résiduel proposé | Décision analyste | Valide par + date |
|---|---|---|---|---|---|
| R-01 | Critique | Réduire (MFA, lockout) | Moyen | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-02 | Moyen | Réduire (bcrypt/argon2) | Faible | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-03 | Élevé | Réduire (SPF/DKIM/DMARC) | Moyen | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-04 | Élevé | Réduire (requêtes paramétrées, patchs) | Moyen | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-05 | Élevé | Réduire + Transférer | Moyen | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-06 | Élevé | Réduire (journalisation) | Faible | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-07 | Élevé | Réduire (rotation, secret manager) | Moyen | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-08 | Élevé | Réduire (chiffrement, stockage externe) | Moyen | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-09 | Élevé | Réduire + Transférer (cyber-assurance) | Moyen | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-10 | Critique | Réduire (séparation composants) | Moyen | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-11 | Élevé | Réduire (pseudonymisation) | Faible | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-12 | Élevé | Réduire (procédure 72 h) | Moyen | **Validé** | Melvin RAIMBAULT · 2026-09-24 |
| R-13 | Élevé | Réduire (programme de mise en conformité RGPD) | Faible | **Validé** (rejet initial du 23/09 **reconsidéré**) | Melvin RAIMBAULT · 2026-09-24 |
| R-14 | Moyen → **Élevé** | Réduire (automatisation backups) | Faible → **Moyen** | **Modifié** (impact Élevé : perte définitive de commandes + données clients ; résiduel Moyen conservateur) | Melvin RAIMBAULT · 2026-09-24 |

## 2. Décisions de la direction (consignées le 2026-09-24)

- **Risques résiduels acceptés** : les résiduels des R-01…R-14 (tableau ci-dessus) sont **acceptés** par l'analyste — responsable : admin « Mélanie » (accompagnement prestataire au besoin).
- **R-13 retenu (rejet du 23/09 reconsidéré le 2026-09-24)** : le rejet initial avait été réalisé **pour tester le circuit de validation** et ne constitue pas une décision de gestion fondée. Reconsidéré : la non-conformité RGPD est un **état de fait** (registre des traitements absent, consentement non prouvé, droit à l'oubli non automatisé) ; le risque est **retenu avec traitement Réduire** (programme de mise en conformité : registre art. 30, mentions légales, consentement double opt-in avec preuve, droit à l'oubli/portabilité art. 17/20, référent RGPD art. 37 si applicable) — **résiduel Faible accepté jusqu'à l'échéance de déc. 2026**, ré-examen à chaque évolution réglementaire.
- **R-14 modifié** : modification actée (probabilité inchangée Moyenne, impact passé Moyen → **Élevé**, niveau Moyen → **Élevé**, résiduel Faible → **Moyen**) — motivée par l'incident 2025 (perte définitive de commandes et de données clients lors d'une défaillance de sauvegarde) et par la nature irrécupérable de la perte. La modification reste opposable par l'analyste à la prochaine revue.
- **Aucun risque « accepter »** : tous les risques retenus sont traités en **réduire** (et/ou **transférer** pour R-05, R-09).

## 3. Plan de suivi (validé avec l'analyste)

- **Fréquence de revue** : semestrielle (2 revues/an) + revue rapide avant chaque période de fêtes (novembre).
- **Déclencheurs de ré-analyse** :
  - Changement de périmètre (nouveau fournisseur, nouveau prestataire de paiement, changement d'hébergeur) ;
  - Incident de sécurité (réel ou avis de phishing) ;
  - Découverte de la CVE réelle du SDK PayFlow (`composer audit`) → poser la note CVSS (R-05) ;
  - Évolution réglementaire RGPD / réclamation d'une personne concernée / contrôle CNIL → **ré-ouvre l'échéance de mise en conformité R-13** (traitement antérieur au plan prévu sinon revue d'exposition).
- **Responsable** : admin « Mélanie » (seule personne) — accompagnement prestataire au besoin ; **référent RGPD à désigner** dans le cadre du programme R-13 (échéance déc. 2026).
- **Prochaine revue** : mars 2027 (ou avant si incident).