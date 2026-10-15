# Inventaire des actifs (étape 1)

| ID | Actif | Type | Description, périmètre et valeur | Sensibilité | Preuve source |
|---|---|---|---|---|---|
| A01 | Site web public (PHP 8, HTML/CSS/JS) | Site | Interface publique vente/catalogue/checkout sur shopix.example avec HTTPS Let's Encrypt, hébergeur mutualisé HostPlanet, disponibilité critique en décembre | Publique | [E49]–[E52], [E90]–[E91],[E103]–[E110],[E117] |
| A02 | API interne (PHP 8) | Service/Logiciel | REST API commandes+stock sur api.shopix.example, même VM que site, exposée internet | Publique | [E49],[E51],[E53], [E117] |
| A03 | Back-office admin (/admin) | Site | Template Bootstrap, login simple, accès 2 préparateurs + 1 admin, pas de MFA pas lockout | Sensible | [E36],[E39],[E49],[E50],[E82], [E117] |
| A04 | Base MySQL (shopix) | Donnée/Logiciel | 1 base unique clients+commandes+produits, 1 compte shopix pas root, SQL 5.7 EOL non chiffrée | Sensible/Critique | [E49],[E36],[E53], [E64]–[E68],[E107]–[E110],[E117] |
| A05 | Espace fichier (uploads) | Matériel/Logiciel | Uploads fichiers produits+images, exports .csv commandes 24 mois FTP non chiffré, zip sauvegarde hebdo | Sensible | [E38],[E49],[E65],[E75], [E103]–[E110] |
| A06 | Hébergeur mutualisé | Service/Prestataire | HostPlanet PHP auto-géré MySQL 5.7 EOL, isolation partagée WAF/CDN/logging absent | Interne | [E49],[E84],[E90], [E103]–[E107],[E110],[E117] |
| A07 | PayFlow paiement | Prestataire/Service | API REST webhooks cartes+SEPA tokenisation côté prestataire, hors périmètre mais clé .env exposée GitHub | Critique | [E43],[E51],[E58], [E80],[E84]+[E105]–[E110],[E117] |
| A08 | MailJet e-mails | Prestataire/Service | API email confirmations+s/newsletter, clé .env stockée en clair code cause spam piracy 2023 | Interne | [E44],[E60],[E80], [E105]–[E110],[E117] |
| A09 | Admin cliente Mélanie | Rôle/Organisation | Accès full produits+commandes+clients+exports, MFA absent session 30 jours, mot de passe simple | Sensible/Critique | [E56],[E58],[E59],[E117] [E57] |
| A10 | Utilisateurs préparateurs (×2) | Rôle/Organisation | Comptes dédiés voir+marquer commandes expédiées du jour, mot de passe simple pas MFA | Interne | [E39],[E40],[E58],[E60],[E117] |
| A11 | Données clients (données personnelles) | Donnée | Nom e-mail adresse livraison téléphone historique commandes hash sha1 EOL consentement newsletter défectueux | Sensible/Critique | [E64],[E65],[E87], [E117]+[ANSSI-CARTO-SI] |
| A12 | Sauvegarde hebdo (dump+zip FTP) | Matériel/Donnée | 1 .sql MySQL + 1 zip uploads FTP même hébergeur non chiffré, perte 2 jours commandes déjà vécue | Sensible/Critique | [E45],[E67],[E75],[E82], [E117] |
| A13 | GitHub (repo privé) | Service/Donnée | Versionné .env clé PayFlow exposée 1 mois oublié, risque phishing domaine signalé | Interne/Sensible | [E83],[E84],[E105]–[E110],[E117] |
| A14 | Site shopix.example + sous-domaines api., admin. | Site | site public e-commerce avec back-office ; SSL Let's Encrypt auto-renouvelé ([E48], [E49]) | Publique | [E48] |
| A15 | Hébergeur "HostPlanet" mutualisé | Service | hébergement partagé, isolation PHP par l'hébergeur, pas de root ou WAF ([E48], [E51]) | Interne | [E48] |
| A16 | Base MySQL clients/commandes/produits | Donnée | 1 seule base unique, compte unique "shopix", SQL non chiffré dans sauvegardes ([E34], [E67]) | Sensible | [E49] [E3] |
| A17 | Clients (nom, email, adresse, téléphone) | Donnée | données personnelles clients avec historique commandes et consentements newsletter ([E64], [E65]) | Interne | [E48] |
| A18 | Bancaires carte/tokenisation PayFlow | Donnée | cartes non stockées dans boutique, tokenisation côté prestataire ([E66]) | Publique | [E66] |
| A19 | Admin (comptes, exports csv) | Donnée | comptes admin, exports CSV clients+commandes en clair sans pseudonymisation ([E67], [E84]) | Critique | [E67] |
| A20 | PHP 8.0 EOL | Logiciel | version maintenue par hébergeur (EOL) mais non patchée ([E105], [E109]) | Interne | [E105] |
| A21 | MySQL 5.7 | Logiciel | base de données gérée par hébergeur, non patchée depuis longtemps ([E48], [E106]) | Sensible | [E106] |
| A22 | PayFlow-SDK v2.1 | Logiciel | SDK paiement avec CVE-2023-XXXX connu non patché ([E107], [E109]) | Critique | [E107] |
| A23 | Plugin impressions v3.2.1 | Logiciel | extension du site non audité, dépendance Composers sans audit régulier ([E48], [E109]) | Interne | [E109] |
| A24 | PayFlow (API REST + webhooks) | Prestataire | paiement cartes/SEPA, clés API dans .env versionné GitHub ([E42], [E84]) | Sensible | [E84] |
| A25 | MailJet (e-mails confirmations/newsletter) | Prestataire | service d'envoi e-mail, clé API stockée en clair ayant causé spam en 2023 ([E43], [E49], [E81]) | Sensible | [E81] |
| A26 | Compte "Mélanie" admin | Rôle | toute administration, mots de passe simples, pas MFA, sessions 30 jours ([E55]) | Critique | [E55] |
| A27 | Comptes préparateurs (×2) | Rôle | accès limité aux commandes du jour, marquer expédiée ([E56], [E57]) | Interne | [E57] |
| A28 | Compte client optionnel | Rôle | passage commande avec compte e-mail/mot de passe ou guest checkout ([E59]) | Publique | [E59] |
| A29 | Hébergement mutualisé HostPlanet | Service | Hébergeur web pour shopix.example, VM partagée, pas de root accessible, budget 2500€/an max (E49). | Publique | [E3],[E49] |
| A30 | Site web public / API interne | Site | Catalogue commandes panier checkout PHP8 HTMLCSSJS mêmes VM hébergeur HTTPS Let's Encrypt (E2),(E3) | Publique | [E48],[E51] |
| A31 | Préparateurs du jour | Rôle / Organisation | 2 comptes dédiés voir commandes jour marquer expédier accès limité préparation (E58) | Sen | [E56] |
| A32 | Clients boutique | Donnée | Nom e-mail adresse livraison téléphone historique commande mot passe hash sha1 ancien consentement newsletter (E59),(E60),[E3],[E64] | Sensible | [E3],[E60],[E68] |
| A33 | Clés API prestataires | Donnée | Ké MailJet PayFlow stockées en clair dans .env versionné GitHub privée oubliée 1 mois (E59,E60)[E17] | Sensible | [E4],[E59] |
| A34 | Sauvegardes FTP manuelles | Donnée | Scripts cron absents dump MySQL ZIP uploads upload FTP dossier hébergeur mutualisé même machine stockage non chiffree (E2),(E3),(E8) | Critique | [E34],[E50] |
| A35 | Extensions plugins PHP | Logiciel | Print plugin version 3.2.1 non auditée PHP8 hébergeur géré pas de composer audit jamais lancé (E18),(E27) | Interne | [E96] |
| A36 | SDK paiement PayFlow-SDK v2.1 | Logiciel | Librairie intégration checkout API REST webhooks CVE-XXXX connu non patché dépendance critique (E36)[E43] | Critique | [E23],[E70] |
| A37 | MailJet e-mailing | Prestataire | Confirmation newsletter envoi SMTP clé API en clair historique piratage 2023 spam au nom boutique 2 jours (E51,E70) | Publique | [E85],[E90] |
| A38 | PayFlow paiement cartes SEPA | Prestataire | Tokenisation hors périmètre boutique webhook commande validation payement.ok intégration (E49),(E63),[E5],[E66] | Interne | [E44],[E72] |
