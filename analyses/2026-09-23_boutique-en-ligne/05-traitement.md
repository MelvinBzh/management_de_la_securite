# Étape 5 — Traitement des risques (cas ShoPix)

> Produit par la chaîne E21 (étape 5 · traiter les risques).
> Entrées : `04-evaluation.md` (niveaux), `02-methodes.md` (priorisation), `knowledge_base/README.md` (contre-mesures).
> Statut : **projet de registre** — aucune décision finale ; `valide_par` sera rempli par l'analyste à l'étape 6.

## 1. Priorité de traitement (ordre DREAD de l'étape 4)

1. **R-10** (M-10, Critique) — absence de segmentation → compromission totale
2. **R-01** (M-01, Critique) — brute force `/admin`
3. puis les risques Élevés (R-03, R-04, R-05, R-06, R-07, R-08, R-09, R-11, R-12, R-13), puis les Moyens (R-02, R-14).

Les **deux risques critiques** sont traités en premier (phases « quick wins » compatibles au budget de 2 500 €/an : pas d'obstacle technique).

## 2. Projet de registre des risques

| ID | Actif | Menace (catégorie) | Proba · Impact · Niveau | Traitement | Contre-mesures (sources) | Risque résiduel estimé |
|---|---|---|---|---|---|---|
| **R-01** | A-03, A-09 (back-office, compte admin) | Brute force `/admin` (STRIDE-S) | Élevée · Élevé · **Critique** | **Réduire** | MFA FIDO2/2FA sur `/admin` (`ISO27002-A8.5.2`) ; verrouillage de compte après 5 échecs + limitation de débit (`ISO27002-A6.2`) ; sessions courtes (< 8 h) ; sensibilisation admin (`ISO27002-A7.2`) | Moyen (proba↓ faible, impact inchangé) |
| **R-02** | A-05 (données clients) | Credential stuffing clients (STRIDE-S) | Moyenne · Moyen · Moyen | **Réduire** | Migration des hash SHA-1 → bcrypt/argon2 (`ISO27002-A8.28`, ANSSI) ; 2FA optionnelle clients (`ISO27002-A8.5.2`) ; détection de connexions anormales (`ISO27002-A8.15`) ; sensibilisation + suivi des listes d'identifiants divulgués (`ISO27002-A7.2`) | Faible (proba↓, impact↓) |
| **R-03** | A-08, A-14, A-12 (clé MailJet, réputation, domaine) | Usurpation identité ShoPix (STRIDE-S) | Moyenne · Élevé · **Élevé** | **Réduire** | Rotation + stockage des clés hors code (gestionnaire de secrets, `ISO27002-A8.24`) ; SPF/DKIM/DMARC sur `shopix.example` (ANSSI, recommandations e-mail) ; surveillance du domaine + analyse de l'avis de phishing reçu (`ISO27002-A8.16`) ; alerte sur les e-mails envoyés (`ISO27002-A8.15`) | Moyen (proba↓, impact inchangé) |
| **R-04** | A-01, A-04 (site, MySQL) | Falsification via site exposé / SQLi (STRIDE-T) | Moyenne · Élevé · **Élevé** | **Réduire** | Requêtes paramétrées systématiques (codage sécurisé, `ISO27002-A8.28`, `A8.26`) ; mise à jour PHP/MySQL (fin de vie, `ISO27002-A8.2.3`) ; compte MySQL dédié moindre privilège (`ISO27002-A6.2.3`) ; analyse de vulnérabilités régulière (`ISO27002-A8.3.2`) | Moyen (proba↓, impact↓ via moindre privilège) |
| **R-05** | A-01, A-16 (checkout, PayFlow) | Falsification flux paiement / SDK non patché (STRIDE-T) | Moyenne · Élevé · **Élevé** | **Réduire** + **Transférer** (responsabilité fonds PayFlow) | `composer audit` hebdomadaire + mise à jour PayFlow-SDK dès CVE confirmée (`ISO27002-A8.8`, `A8.2.3`) ; vérification signature/authenticité des webhooks `payment.ok` (`ISO27002-A8.28`) ; supervision des transactions (`ISO27002-A8.15`) ; contrat/DPA avec PayFlow (`ISO27002-A5.4`) | Moyen (proba↓) |
| **R-06** | A-06, A-09 (exports, admin) | Répudiation actions admin (STRIDE-R) | Élevée · Moyen · **Élevé** | **Réduire** | Journalisation des actions admin horodatées + rétention (`ISO27002-A8.15`, `A8.16`) ; journaux en écriture seule (anti-tampering) ; revue périodique des journaux (`ISO27002-A8.4`) | Faible (impact↓ : preuve disponible) |
| **R-07** | A-08 (clé PayFlow `.env`) | Divulgation clé API versionnée (STRIDE-I) | Moyenne · Élevé · **Élevé** | **Réduire** | Ne plus versionner `.env` (`.gitignore` + secret scanning) ; rotation immédiate de la clé exposée (`ISO27002-A8.24`) ; gestionnaire de secrets (`ISO27002-A8.24`) ; minimisation des droits de l'API (`ISO27002-A6.2.3`) | Moyen (proba↓) |
| **R-08** | A-07, A-06 (sauvegardes, exports) | Sauvegardes FTP en clair (STRIDE-I) | Moyenne · Élevé · **Élevé** | **Réduire** | Chiffrement des dumps avant transfert (`ISO27002-A8.4.2`) ; sauvegarde hors du serveur mutualisé (autre prestataire) (`ISO27002-A5.36`) ; accès FTP restreint + comptes dédiés (`ISO27002-A6.2`) ; pseudonymisation des exports `.csv` (`ISO27002-A8.11`) | Moyen (proba↓, impact↓) |
| **R-09** | A-13, A-01 (disponibilité, site) | Indisponibilité en décembre (STRIDE-D) | Moyenne · Élevé · **Élevé** | **Réduire** + **Transférer** | Monitoring + alertes de disponibilité (`ISO27002-A8.15`/`A8.16`) ; protection de base (rate-limiting, CDN si l'hébergeur le permet, `ISO27002-A8.14`) ; runbook de rétablissement dimensionné au pic (ANSSI) ; **cyber-assurance perte d'exploitation** (`ISO27002-A5.36`, transfert financier) | Moyen (proba↓) |
| **R-10** | A-01, A-03, A-04 (site, back-office, MySQL) | Élévation F3 sans segmentation (STRIDE-E) | Élevée · Élevé · **Critique** | **Réduire** | Séparation effective des composants (VPS/serveur dédié ou exigence d'isolation auprès de l'hébergeur, `ISO27002-A8.9`) ; comptes MySQL distincts par application, moindre privilège (`ISO27002-A6.2.3`) ; cloisonnement back-office/API (`ISO27002-A6.2`) ; re-audit après changement d'hébergement (`ISO27002-A8.3.2`, `A8.29`) | Moyen (risque structural fortement réduit mais mutualisation résiduelle) |
| **R-11** | A-06 (exports .csv) | Corrélation/identification via exports (LINDDUN-L/I) | Élevée · Moyen · **Élevé** | **Réduire** | Pseudonymisation/minimisation des exports (`ISO27002-A8.11`) ; limitation aux données strictement nécessaires ; réduction de la durée de conservation (24 mois → minimum) (`collecte minimale RGPD art. 5) ; accès aux exports restreints (`ISO27002-A6.2`) | Faible (proba↓, impact↓) |
| **R-12** | A-05 (données clients) | Divulgation données personnelles (LINDDUN-DI) | Moyenne · Élevé · **Élevé** | **Réduire** | Procédure de notification de violation 72 h (RGPD art. 33) ; minimisation + chiffrement (`ISO27002-A8.4.2`) ; clauses DPA avec hébergeur et prestataires (`ISO27002-A5.4`) ; droit à l'oubli automatisé (art. 17, `ISO27002-A8.11`) | Moyen (impact réglementaire↓ une fois la procédure prête) |
| **R-13** | A-11, A-05 (consentement, traitements) | Non-conformité RGPD (LINDDUN-NC) | Élevée · Moyen · **Élevé** | **Réduire** | Registre des traitements (art. 30) ; mentions légales complètes ; consentement valide (double opt-in, preuve) (`ISO27002-A8.11`) ; droit à l'oubli/portabilité automatisés (art. 17/20) ; désignation d'un référent RGPD (art. 37 si applicable) (ANSSI / CNIL) | Faible (risque de sanction↓ une fois conforme) |
| **R-14** | A-07, A-04 (sauvegardes, base) | Perte de commandes (STRIDE-D) | Moyenne · Moyen · Moyen | **Réduire** | Sauvegarde automatisée (cron) + test de restauration mensuel (`ISO27002-A5.36`) ; règle 3-2-1 (2e copie hors FTP mutualisé) (`ISO27002-A5.36`) ; monitoring du succès des sauvegardes (`ISO27002-A8.16`) ; chiffrement du dump (`ISO27002-A8.4.2`) | Faible (proba↓, impact↓) |

## 3. Équilibre budgétaire indicatif (2 500 €/an)

| Poste | Coût annuel indicatif |
|---|---|
| MFA + verrouillage `/admin` + journalisation (outillage SaaS/SMTP) | ~600 € |
| Hébergement avec isolation / VPS + monitoring | ~800 € |
| `composer audit`, patchs, secret manager, rotation clés | ~300 € |
| Mise en conformité RGPD (registre, mentions, consentement) | ~400 € (temps)
| Sensibilisation + runbook + test de restauration | ~200 € |
| **Total** | **~2 300 €** (marge 200 €) |

## 4. Annexe — JSON du projet de registre

```json
{
  "analyse": "2026-09-23_boutique-en-ligne",
  "methode": "STRIDE + LINDDUN, priorisation DREAD (CVSS en attente CVE reelle)",
  "risques": [
    {"id":"R-01","actif":"Back-office / admin","menace":"Brute force /admin","categorie":"STRIDE-S","probabilite":"elevee","impact":"eleve","niveau":"critique","traitement":"reduire","mesures":["MFA","lockout","sessions courtes"],"sources":["STRIDE-S","ISO27002-A8.5.2","ISO27002-A6.2"],"risque_residuel":"moyen","valide_par":null},
    {"id":"R-02","actif":"Donnees clients","menace":"Credential stuffing (hash SHA-1)","categorie":"STRIDE-S","probabilite":"moyenne","impact":"moyen","niveau":"moyen","traitement":"reduire","mesures":["bcrypt/argon2","2FA clients","detection connexions anormales"],"sources":["STRIDE-S","ISO27002-A8.28","ISO27002-A8.5.2"],"risque_residuel":"faible","valide_par":null},
    {"id":"R-03","actif":"Identite ShoPix / domaine","menace":"Usurpation identite e-mail + phishing domaine","categorie":"STRIDE-S","probabilite":"moyenne","impact":"eleve","niveau":"eleve","traitement":"reduire","mesures":["secrets manager","SPF/DKIM/DMARC","surveillance domaine"],"sources":["STRIDE-S","ISO27002-A8.24","ANSSI-*"],"risque_residuel":"moyen","valide_par":null},
    {"id":"R-04","actif":"Site web + MySQL","menace":"SQLi / exploitation PHP EOL","categorie":"STRIDE-T","probabilite":"moyenne","impact":"eleve","niveau":"eleve","traitement":"reduire","mesures":["requetes preparees","patchs","moindre privilege MySQL"],"sources":["STRIDE-T","ATT&CK-T1190","ISO27002-A8.28","ISO27002-A8.2.3"],"risque_residuel":"moyen","valide_par":null},
    {"id":"R-05","actif":"Checkout / PayFlow","menace":"SDK PayFlow non patche / webhooks falsifies","categorie":"STRIDE-T","probabilite":"moyenne","impact":"eleve","niveau":"eleve","traitement":"reduire+transferer","mesures":["composer audit","patch SDK","signature webhooks"],"sources":["STRIDE-T","ATT&CK-T1190","ISO27002-A8.8","ISO27002-A8.2.3"],"risque_residuel":"moyen","valide_par":null},
    {"id":"R-06","actif":"Actions admin","menace":"Repudiation actions admin (pas de logs)","categorie":"STRIDE-R","probabilite":"elevee","impact":"moyen","niveau":"eleve","traitement":"reduire","mesures":["journalisation","logs write-only","revue"],"sources":["STRIDE-R","ISO27002-A8.15","ISO27002-A8.16"],"risque_residuel":"faible","valide_par":null},
    {"id":"R-07","actif":"Cle API PayFlow (.env)","menace":"Cle versionnee sur GitHub","categorie":"STRIDE-I","probabilite":"moyenne","impact":"eleve","niveau":"eleve","traitement":"reduire","mesures":[".gitignore","secret scanning","rotation","secrets manager"],"sources":["STRIDE-I","ISO27002-A8.24"],"risque_residuel":"moyen","valide_par":null},
    {"id":"R-08","actif":"Sauvegardes + exports","menace":"Sauvegardes FTP en clair (mutualisation)","categorie":"STRIDE-I","probabilite":"moyenne","impact":"eleve","niveau":"eleve","traitement":"reduire","mesures":["chiffrement dumps","stockage externe","pseudonymisation exports"],"sources":["STRIDE-I","ISO27002-A8.4.2","ISO27002-A5.36","ISO27002-A8.11"],"risque_residuel":"moyen","valide_par":null},
    {"id":"R-09","actif":"Disponibilite site (dec.)","menace":"Indisponibilite periode critique","categorie":"STRIDE-D","probabilite":"moyenne","impact":"eleve","niveau":"eleve","traitement":"reduire+transferer","mesures":["monitoring","rate-limiting/CDN","runbook","cyber-assurance"],"sources":["STRIDE-D","ISO27002-A8.14","ISO27002-A5.36","ANSSI-*"],"risque_residuel":"moyen","valide_par":null},
    {"id":"R-10","actif":"Toute la VM (site+BO+MySQL)","menace":"Elevation de privilege sans segmentation","categorie":"STRIDE-E","probabilite":"elevee","impact":"eleve","niveau":"critique","traitement":"reduire","mesures":["separation composants","comptes MySQL distincts","re-audit"],"sources":["STRIDE-E","ATT&CK-T1190","ISO27002-A8.9","ISO27002-A6.2.3"],"risque_residuel":"moyen","valide_par":null},
    {"id":"R-11","actif":"Exports .csv","menace":"Correlation/identification via exports non pseudo","categorie":"LINDDUN-L/I","probabilite":"elevee","impact":"moyen","niveau":"eleve","traitement":"reduire","mesures":["pseudonymisation","minimisation","duree conservation reduite"],"sources":["LINDDUN-L","LINDDUN-I","ISO27002-A8.11"],"risque_residuel":"faible","valide_par":null},
    {"id":"R-12","actif":"Donnees clients","menace":"Divulgation en masse donnees personnelles","categorie":"LINDDUN-DI","probabilite":"moyenne","impact":"eleve","niveau":"eleve","traitement":"reduire","mesures":["procedure 72h","chiffrement","DPA","droit a l'oubli"],"sources":["LINDDUN-DI","ISO27002-A8.4.2","ISO27002-A5.4"],"risque_residuel":"moyen","valide_par":null},
    {"id":"R-13","actif":"Traitements RGPD (consentement, registre)","menace":"Non-conformite RGPD courante","categorie":"LINDDUN-NC","probabilite":"elevee","impact":"moyen","niveau":"eleve","traitement":"reduire","mesures":["registre art.30","mentions legales","double opt-in","referente RGPD"],"sources":["LINDDUN-NC","ISO27002-A8.11","ANSSI-*"],"risque_residuel":"faible","valide_par":null},
    {"id":"R-14","actif":"Sauvegardes + base commandes","menace":"Perte de commandes (sauvegarde manuelle)","categorie":"STRIDE-D","probabilite":"moyenne","impact":"moyen","niveau":"moyen","traitement":"reduire","mesures":["cron backup","tests restauration","regle 3-2-1"],"sources":["STRIDE-D","ISO27002-A5.36","ISO27002-A8.16"],"risque_residuel":"faible","valide_par":null}
  ]
}
```

> ⚠️ Décision de traitement explicitement **proposée**, jamais définitive : l'analyste valide ou corrige à l'étape 6.