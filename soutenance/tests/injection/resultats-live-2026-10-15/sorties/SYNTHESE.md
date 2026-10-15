# Synthèse (étape 7)

> Document d'orientation pour une décision de direction (structure inspirée du guide `ANSSI-PSSI` : faits, décisions, actions). Les chiffres sont CALCULÉS par le programme à partir du registre des risques, pas écrits par un modèle ; chaque risque garde l'identifiant du registre.

## 1. Résumé exécutif

L'analyse porte sur **38 actifs** et **116 risques**. 46 risques sont évalués au niveau Critique (40 %), 29 Élevé, 22 Moyen et 18 Faible. Traitement proposé : 91 à réduire, 13 à éviter, 6 à accepter, 6 à transférer. Aucun risque n'a encore été décidé : les 116 risques sont proposés et attendent la validation d'un analyste. L'actif le plus exposé est **A28 — Compte client optionnel** (5 risques dont 4 critiques).

**Lecture** (rédigée par le modèle, dont les chiffres ont été recontrôlés par le programme) :

# Chiffres de l'analyse

## Synthèse pour la direction

La sécurité de 38 actifs a été évaluée, soit 116 risques inscrits dans le registre. Quarante pour cent (46) des risques sont classés Critique et vingt-cinq pour cent (29) Élevé. Neuf traitements privilégient la réduction immédiate contre treize éviter.

### Où se concentre le risque
Les actifs clients, paiements bancaires et administration représentent les points critiques. Quarante pourcent des risques sont Critique ou élevés sur 116 inscrits. Le traitement Éviter concerne 13 cas seulement.

### Ce qui est urgent
Réduire immédiatement 91 risques identifiés comme impactant la vie privée, la disponibilité et l'intégrité. Zéro risque n'a encore été validé par un analyste humain.

### Ce qu'il reste à décider
La direction doit prioriser entre 6 risques en attente de transfert (fournisseurs) et 6 acceptés (faible impact). Une revue humaine complète 116 risques pour valider les décisions restantes.

## 2. Chiffres clés

| Indicateur | Valeur |
|---|---|
| Actifs analysés | 38 |
| Risques au registre | 116 |
| Niveau Critique | 46 (40 %) |
| Niveau Élevé | 29 (25 %) |
| Niveau Moyen | 22 (19 %) |
| Niveau Faible | 18 (16 %) |
| Traitement : Réduire | 91 |
| Traitement : Éviter | 13 |
| Traitement : Accepter | 6 |
| Traitement : Transférer | 6 |
| Risques décidés par un analyste | 0 sur 116 |

## 3. Où se concentre le risque

| Actif | Risques | Dont Critique | Dont Élevé |
|---|---|---|---|
| A28 — Compte client optionnel | 5 | 4 | 0 |
| A27 — Comptes préparateurs | 5 | 3 | 1 |
| A17 — Clients (nom, email, adresse, téléphone) | 3 | 3 | 0 |
| A19 — Admin (comptes, exports csv) | 3 | 2 | 1 |
| A08 — MailJet e-mails | 3 | 2 | 0 |
| A18 — Bancaires carte/tokenisation PayFlow | 3 | 2 | 0 |
| A20 — PHP 8.0 EOL — Logiciel (hôte serveur) | 3 | 2 | 0 |
| A30 — Site web public / API interne | 3 | 2 | 0 |

## 4. Risques prioritaires (les 10 premiers par niveau, impact puis probabilité)

| ID | Actif | Menace | Niveau | Pourquoi (étape 4) | Traitement | Risque résiduel |
|---|---|---|---|---|---|---|
| M004 | A02 — API interne (PHP 8) | STRIDE-I — Fuite données sensibles clients/produits à travers les endpoints REST exposés internet sans authentification forte et rate limiting, permettant lecture brute de bases par scanners web automatisés [E49] | Critique | endpoints REST API internes exposés internet sans authentification forte ni rate limiting, données sensibles accessibles aux scanners automatisés [E49] | Éviter | Critique |
| M007 | A03 — Back-office admin (/admin) | STRIDE-S — Spoofing d'administration via brute force sur login sans lockout/brute rate limiting, permettant usurpation compte admin ou préparateurs [E49], [E81] | Critique | brute force détecté logs HTTP 2024 tente usurpation compte admin/preparateurs, absence lockout/auth forte [E81] | Réduire | Critique |
| M016 | A06 — Hébergeur mutualisé HostPlanet | STRIDE-S/Spoofing — Attaquant tiers (voisin locataire) usurpe l'identité du site shopix.example via DNS cache poisoning ou compromission de VM co-lodée, redirigeant utilisateurs vers faux site de phishing [E49]. | Critique | Hébergeur mutualisé HostPlanet, VM co-lodée avec autres locataires [E38], absence de WAF/logging [E48], domaine déjà reçu 1 avis phishing abandonné [E83] → usurpation identité site via DNS poisoning ou compromission voisin [E50] | Réduire | Critique |
| M049 | A20 — PHP 8.0 EOL — Logiciel (hôte serveur) | STRIDE-T — Exploitation de vulnérabilités connues sur PHP 8.0 maintenu par hébergeur ([E49], [E105]) → exécution de code malveillant dans /var/www après injection via formulaire catalogue sans validation d'entrée ([E67]) | Critique | PHP 8.0 EOL maintenu par hébergeur avec vulnérabilités [E49] | Éviter | Critique |
| M070 | A30 — Site web public / API interne | STRIDE-I — Une faille CVE-2024-3009 dans PHP 8.0 hébergé sur la VM mutualisée (E2) permet l'exfiltration de la base MySQL via injection mémoire, exposant tous les clients et commandes en clair | Critique | CVE-2024-3009 sur PHP 8.0 [E2] | Réduire | Critique |
| M079 | A27 — Comptes préparateurs | EBIOS-RM-A4 — Un fournisseur de solution de paiement tiers (E56) est compromis et l'attaquant injecte du code dans les flux vers le panel des préparateurs pour usurper leur rôle via webhooks malveillants depuis l'extérieur de l'écosystème organisationnel | Critique | Fournisseur paiement tiers compromis [E51], webhook malveillant injecté vers panel préparateurs, flux financier et données sensibles clients [E48] à risque direct en violation PCI DSS potentiel. | Éviter | Critique |
| M105 | Shopix — Frontière Site Web↔Base MySQL (Écriture) RCE vulnérabilité PHP extension non auditée plugin impressions backdoor serveur exécution code [E24],[E90] | STRIDE-I — Environment Modification → attaqu via requête GET vers route backend exploitant CVE-XXXX sur library payement ou plugin 3.2.1 → code shell malveillant injecté web root → accès système complet VM mutualisé voisine compromise [E49],[E22] | Critique | Extension non auditée exploitable côté serveur (CVE-XXXX) enchaîné RCE → exécution code système complet sur VM mutualisé compromise [E24],[E90] | Réduire | ISO27002-8.25 |
| M108 | Shopix — Frontière Admin↔Base MySQL (Lecture/Modif) admin滥用 droits totale exfiltration clients commandes produits exportés [E67],[E58] | STRIDE-T — Tampering → Mélanie admin accède /admin sans MFA sessions 30j -> télécharge .csv clients+commandes stocké FTP hébergeur -> CSV brut avec SHA1 + consentements newsletter non pseudonymisés [E64],[E66] | Critique | Compte admin « Mélanie » sans MFA avec sessions de 30 jours permet exfiltration CSV brut client+commandes+consentements RGPD hébergé sur FTP accessible par compromission serveur [E67],[E58] | Réduire | ANSSI-PSSI 3 |
| M110 | Shopix — Frontière Sauvegarde FTP (SFTP/FTP non chiffré) SQL brut 24 mois stockage FTP hébergeur compromis exfiltration complète base de données clients [E76],[E45] | STRIDE-I — Information Disclosure → attaqu connait FTP@hostplanet.net dossier /backups/shopix → SSH-KEY ou brute force accès ftp → télécharge .sql contenant tables clients/commandes/produits en clair SHA1 non chiffré → fuit RGPD CNIL [E67] | Critique | Accès FTP connu dossier /backups/shopix hébergé sur mutualisé permettant exfiltration SQL brut 24 mois de tables clients/commandes avec hash SHA1 sans chiffrement [E76],[E45] | Réduire | ISO27002-5.15 |
| M011 | A04 — Base MySQL (shopix) | STRIDE-T — Injection SQLi côté base via connexions non filtrées depuis API interne, modifiant/effaçant clients/commandes/produits [E49] | Critique | Connexions non filtrées depuis API interne vers base MySQL exposée [E49], ancienne version MySQL 5.7 (EOL) + absence de WAF/logging centralisé [E48] → SQLi facile contre clients/commandes/produits [E14] | Réduire | Moyen |

## 5. Actions recommandées

Chaque action vient du traitement de l'étape 5 pour le risque indiqué ; la revue suit le plan de `06-validation.md`.

| Priorité | Risque | Action (contre-mesures proposées) | Prochaine revue |
|---|---|---|---|
| Critique | M004 | Authentification OAuth2 (ANSSI-RECYF-8.2), rate limiting (ISO27002-8.8) | mensuelle |
| Critique | M007 | Lockout compte (ANSSI-HYGIENE-8.2), authentification forte (ISO27002-8.2) | mensuelle |
| Critique | M016 | Isolation VM via segmentation (ISO27002-8.11) | mensuelle |
| Critique | M049 | Migration à PHP 8.3+ avec notification hébergeur non supportée + audit détaillé | mensuelle |
| Critique | M070 | Mise à jour PHP vers 8.2 (ISO27002-8.26) + patch CVE-2024-3009 (ANSSI-HOMOLOGATION) | mensuelle |
| Critique | M079 | Suppression du fournisseur tiers (EBIOS-RM-A4) | mensuelle |
| Critique | M105 | Audit code plugin impressions 3.2.1 via SCA scanner dépendances (ISO27002-8.25) + Mise à jour vers version stabilisée 3.x+ (EBIOS-RM-A4) + Isolation sandbox PHP pour extensions tiers (ANSSI-HYGIENE 5) | mensuelle |
| Critique | M108 | Authentification MFA FIDO2 admin obligatoire (ANSSI-PSSI 3) + Sessions à max 8h renouvelées par token JWT avec refresh tokens rotation (ISO27002-5.4) + Chiffrage données CSV exportés via AES-256 avant stockage FTP () | mensuelle |
| Critique | M110 | Sauvegardes déplacées vers cloud chiffré GCP KMS ou AWS S3 Encryption SSE-KMS (ANSSI-CARTO-SI 2) + Cycle rétention 90jours puis destruction automatique cron (ISO27002-8.34) + Accès restaurations avec MFA secondaire et journalisation complète (ISO27002-5.15) | mensuelle |
| Critique | M011 | MFA FIDO2 (ANSSI-HYGIENE) | mensuelle |

## 6. Décisions de l'analyste

Aucune décision enregistrée : les 116 risques restent « À valider par l'analyste ».

## 7. Limites et points à vérifier

- **Niveaux à relire en priorité** : 46 risques sur 116 (40 %) sont évalués Critique. Le niveau est CALCULÉ par le programme (matrice probabilité × impact) à partir des valeurs proposées par le modèle ; quand presque tout est critique, la hiérarchie ne guide plus : relisez d'abord les probabilités et les impacts.
- **Étapes à valider par une personne** : 1, 2, 3, 4, 5 ; 181 ligne(s) dont la preuve citée n'a pas pu être établie par la machine (page ④, « Lignes à relire », par pages de dix).
- **1 risque(s) sans niveau** : l'évaluation de l'étape 4 est incomplète pour eux.

## 8. Comment lire ce dossier

- `registre-risques.md` : tous les risques, une ligne chacun, de la menace au traitement.
- `06-validation.md` : ce qui reste à décider, le plan de suivi, et les décisions prises.
- `03-menaces.md`, `04-evaluation.md`, `05-traitement.md` : le détail et les preuves `[E…]`.
- `RAPPORT-CONTROLE.md` : ce que le contrôle a relevé, étape par étape.
