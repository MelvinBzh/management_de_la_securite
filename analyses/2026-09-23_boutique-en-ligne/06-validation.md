# Étape 6 — Validation et suivi (cas ShoPix)

> Produit par la chaîne E21 (étape 6 · valider et suivre).
> **Humain dans la boucle** : ce fichier consigne les décisions de l'analyste/direction. Aucun risque n'est « Done » sans `valide_par` renseigné.
> État : **en attente de la décision de l'analyste** — les questions de validation lui ont été soumises (R-01…R-14).

## 1. Validation des risques

Chaque risque est présenté à l'analyste dans le format du registre. Réponse attendue pour chaque risque : **valider tel quel / corriger / refuser**.

| ID | Niveau proposé | Traitement proposé | Risque résiduel proposé | Décision analyste | Valide par + date |
|---|---|---|---|---|---|
| R-01 | Critique | Réduire (MFA, lockout) | Moyen | *(en attente)* | — |
| R-02 | Moyen | Réduire (bcrypt/argon2) | Faible | *(en attente)* | — |
| R-03 | Élevé | Réduire (SPF/DKIM/DMARC) | Moyen | *(en attente)* | — |
| R-04 | Élevé | Réduire (requêtes paramétrées, patchs) | Moyen | *(en attente)* | — |
| R-05 | Élevé | Réduire + Transférer | Moyen | *(en attente)* | — |
| R-06 | Élevé | Réduire (journalisation) | Faible | *(en attente)* | — |
| R-07 | Élevé | Réduire (rotation, secret manager) | Moyen | *(en attente)* | — |
| R-08 | Élevé | Réduire (chiffrement, stockage externe) | Moyen | *(en attente)* | — |
| R-09 | Élevé | Réduire + Transférer (cyber-assurance) | Moyen | *(en attente)* | — |
| R-10 | Critique | Réduire (séparation composants) | Moyen | *(en attente)* | — |
| R-11 | Élevé | Réduire (pseudonymisation) | Faible | *(en attente)* | — |
| R-12 | Élevé | Réduire (procédure 72 h) | Moyen | *(en attente)* | — |
| R-13 | Élevé | Réduire (mise en conformité) | Faible | *(en attente)* | — |
| R-14 | Moyen | Réduire (automatisation backups) | Faible | *(en attente)* | — |

## 2. Décisions de la direction (à consigner après validation)

- **Risques résiduels acceptés** : *(à remplir)* — chaque risque résiduel noté ci-dessus sera accepté explicitement par l'analyste avec responsabilité et date.
- **Risques « accepter » par décision écrite** : *(aucun proposé — tous les risques sont traités en réduire/transférer ; si l'analyste choisit « accepter » pour un risque, le documenter ici)*.

## 3. Plan de suivi (proposé — à valider avec l'analyste)

- **Fréquence de revue** : semestrielle (2 revues/an) + revue rapide avant chaque période de fêtes (novembre).
- **Déclencheurs de ré-analyse** :
  - Changement de périmètre (nouveau fournisseur, nouveau prestataire de paiement, changement d'hébergeur) ;
  - Incident de sécurité (réel ou avis de phishing) ;
  - Découverte de la CVE réelle du SDK PayFlow (`composer audit`) → poser la note CVSS (R-05) ;
  - Évolution réglementaire RGPD / réclamation d'une personne concernée.
- **Responsable** : admin « Mélanie » (seule personne) — accompagnement prestataire au besoin ; référent RGPD à désigner (R-13).
- **Prochaine revue** : mars 2027 (ou avant si incident).

## 4. Garde-fous appliqués (rappel)

- `valide_par` rempli **uniquement par l'analyste** ; le registre n'est pas final tant qu'il est vide.
- Sources de chaque risque vérifiées par `e21-controle` (ID de `knowledge_base/`).
- Données fictives, aucun chiffre inventé ; CVSS en attente de CVE réelle.