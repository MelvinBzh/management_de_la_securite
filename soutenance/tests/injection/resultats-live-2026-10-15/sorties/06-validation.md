# Validation et suivi (étape 6)

> Document établi par le programme à partir du registre des risques. Il ne contient AUCUNE décision : les décisions sont prises par une personne dans la page ④ du site, puis ajoutées en bas de ce document (qui, quand, pourquoi).

## 1. État de la validation

- Risques au registre : **116**.
- Décidés par un analyste : **0** (0 acceptés, 0 acceptés avec modification, 0 refusés).
- Restant à valider : **116**.

| Niveau | Risques | Dont décidés |
|---|---|---|
| Critique | 46 | 0 |
| Élevé | 29 | 0 |
| Moyen | 22 | 0 |
| Faible | 18 | 0 |

## 2. Risques à décider en priorité (niveaux Critique et Élevé)

La colonne « Décision » se remplit dans le site (page ④) ; elle est ici pour mémoire.

| ID | Actif | Niveau | Traitement proposé | Risque résiduel | Décision | Responsable |
|---|---|---|---|---|---|---|
| M004 | A02 — API interne (PHP 8) | Critique | Éviter | Critique | À décider | À désigner |
| M007 | A03 — Back-office admin (/admin) | Critique | Réduire | Critique | À décider | À désigner |
| M016 | A06 — Hébergeur mutualisé HostPlanet | Critique | Réduire | Critique | À décider | À désigner |
| M049 | A20 — PHP 8.0 EOL — Logiciel (hôte serveur) | Critique | Éviter | Critique | À décider | À désigner |
| M070 | A30 — Site web public / API interne | Critique | Réduire | Critique | À décider | À désigner |
| M079 | A27 — Comptes préparateurs | Critique | Éviter | Critique | À décider | À désigner |
| M105 | Shopix — Frontière Site Web↔Base MySQL (Écriture) RCE vulnérabilité PHP extension non auditée plugin impressions backdoor serveur exécution code [E24],[E90] | Critique | Réduire | ISO27002-8.25 | À décider | À désigner |
| M108 | Shopix — Frontière Admin↔Base MySQL (Lecture/Modif) admin滥用 droits totale exfiltration clients commandes produits exportés [E67],[E58] | Critique | Réduire | ANSSI-PSSI 3 | À décider | À désigner |
| M110 | Shopix — Frontière Sauvegarde FTP (SFTP/FTP non chiffré) SQL brut 24 mois stockage FTP hébergeur compromis exfiltration complète base de données clients [E76],[E45] | Critique | Réduire | ISO27002-5.15 | À décider | À désigner |
| M011 | A04 — Base MySQL (shopix) | Critique | Réduire | Moyen | À décider | À désigner |
| M021 | A08 — MailJet e-mails | Critique | Réduire | Élevé | À décider | À désigner |
| M022 | A08 — MailJet e-mails | Critique | Réduire | Élevé | À décider | À désigner |
| M023 | A09 — Admin cliente Mélanie | Critique | Réduire | Élevé | À décider | À désigner |
| M024 | A09 — Admin cliente Mélanie | Critique | Réduire | Élevé | À décider | À désigner |
| M025 | A10 — Utilisateurs préparateurs (×2) | Critique | Réduire | Élevé | À décider | À désigner |
| M026 | A10 — Utilisateurs préparateurs (×2) | Critique | Réduire | Élevé | À décider | À désigner |
| M027 | A11 — Données clients (données personnelles) | Critique | Réduire | Élevé | À décider | À désigner |
| M028 | A11 — Données clients (données personnelles) | Critique | Réduire | Élevé | À décider | À désigner |
| M029 | A12 — Sauvegarde hebdo (dump+zip FTP) | Critique | Réduire | Élevé | À décider | À désigner |
| M030 | A12 — Sauvegarde hebdo (dump+zip FTP) | Critique | Réduire | Élevé | À décider | À désigner |
| M031 | A13 — GitHub (repo privé .env PayFlow) | Critique | Réduire | Risque résiduel Faible | À décider | À désigner |
| M032 | A13 — GitHub (repo privé .env PayFlow) | Critique | Éviter | Risque résiduel Faible | À décider | À désigner |
| M033 | A14 — Site shopix.example + api./admin. | Critique | Réduire | Risque résiduel Faible | À décider | À désigner |
| M035 | A15 — Hébergeur "HostPlanet" mutualisé | Critique | Éviter | Risque résiduel Faible | À décider | À désigner |
| M037 | A16 — Base MySQL clients/commandes/produits | Critique | Réduire | Risque résiduel Faible | À décider | À désigner |
| M040 | A17 — Clients (nom, email, adresse, téléphone) | Critique | Réduire | Risque résiduel Faible | À décider | À désigner |
| M041 | A17 — Clients (nom, email, adresse, téléphone) | Critique | Réduire | Moyen | À décider | À désigner |
| M042 | A17 — Clients (nom, email, adresse, téléphone) | Critique | Réduire | Moyen | À décider | À désigner |
| M043 | A18 — Bancaires carte/tokenisation PayFlow | Critique | Réduire | Faible | À décider | À désigner |
| M045 | A18 — Bancaires carte/tokenisation PayFlow | Critique | Éviter | Élevé | À décider | À désigner |
| M046 | A19 — Admin (comptes, exports csv) | Critique | Réduire | Moyen | À décider | À désigner |
| M047 | A19 — Admin (comptes, exports csv) | Critique | Réduire | Moyen | À décider | À désigner |
| M051 | A20 — PHP 8.0 EOL — Logiciel (hôte serveur) | Critique | Réduire | Élevé | À décider | À désigner |
| M054 | A21 — MySQL 5.7 — Logiciel (base de données) | Critique | Réduire | Élevé | À décider | À désigner |
| M061 | A27 — Comptes préparateurs | Critique | Réduire | Élevé | À décider | À désigner |
| M063 | A27 — Comptes préparateurs | Critique | Réduire | Critique | À décider | À désigner |
| M064 | A28 — Compte client optionnel | Critique | Réduire | Critique | À décider | À désigner |
| M065 | A28 — Compte client optionnel | Critique | Réduire | Élevé | À décider | À désigner |
| M066 | A28 — Compte client optionnel | Critique | Réduire | Critique | À décider | À désigner |
| M068 | A29 — Hébergement mutualisé HostPlanet | Critique | Réduire | Critique | À décider | À désigner |
| M069 | A28 — Compte client optionnel | Critique | Réduire | Élevé | À décider | À désigner |
| M071 | A30 — Site web public / API interne | Critique | Réduire | Moyen | À décider | À désigner |
| M091 | A36 — SDK paiement PayFlow-SDK v2.1 | Critique | Réduire | Moyenne | À décider | À désigner |
| M097 | Shopix — Frontière Internet↔Site Web (HTTPS) XSS frontend malveillant exfiltration paramètres session cookies [E52] | Critique | Réduire | Critique | À décider | À désigner |
| M101 | Shopix — Frontière Site Web↔MailJet (SMTP+API) logs prestataire divulguent consentement newsletter données clients sensibles [E67],[E50] | Critique | Réduire | ISO27002-8.34 | À décider | À désigner |
| M104 | Shopix — Frontière Site Web↔Base MySQL (Écriture) SQL injection admin /admin exfiltration client commandes internes [E38],[E49] | Critique | Réduire | ISO27002-5.3 | À décider | À désigner |
| M005 | A02 — API internes (PHP 8) | Élevé | Réduire | Élevé | À décider | À désigner |
| M010 | A04 — Base MySQL (shopix) | Élevé | Réduire | Élevé | À décider | À désigner |
| M002 | A01 — Site web public (PHP 8, HTML/CSS/JS) | Élevé | Réduire | Moyen | À décider | À désigner |
| M003 | A01 — Site web public (PHP 8, HTML/CSS/JS) | Élevé | Réduire | Élevé | À décider | À désigner |
| M008 | A03 — Back-office admin (/admin) | Élevé | Réduire | Élevé | À décider | À désigner |
| M017 | A06 — Hébergeur mutualisé HostPlanet | Élevé | Réduire | Élevé | À décider | À désigner |
| M018 | A06 — Hébergeur mutualisé HostPlanet | Élevé | Éviter | Élevé | À décider | À désigner |
| M052 | A21 — MySQL 5.7 — Logiciel (base de données) | Élevé | Réduire | Élevé | À décider | À désigner |
| M053 | A21 — MySQL 5.7 — Logiciel (base de données) | Élevé | Réduire | Critique | À décider | À désigner |
| M076 | A29 — Hébergement mutualisé HostPlanet | Élevé | Transférer | Élevé | À décider | À désigner |
| M080 | A29 — Hébergement mutualisé HostPlanet | Élevé | Réduire | Élevé | À décider | À désigner |
| M084 | A32 — Clients boutique | Élevé | Transférer | Faible | À décider | À désigner |
| M087 | A34 — Sauvegardes FTP manuelles | Élevé | Réduire | Moyen | À décider | À désigner |
| M095 | Shopix — Frontière Internet↔Site Web (HTTPS) attaquant externe usurpation site légitime clients trompés furtif exfiltration données [E48],[E23] | Élevé | Réduire | Élevé | À décider | À désigner |
| M098 | Shopix — Frontière Site Web↔PayFlow (REST+Webhook) attaquant modifie webhook PaymentOK→PaymentFailed déni paiement client [E98] | Élevé | Réduire | Élevé | À décider | À désigner |
| M102 | Shopix — Frontière Site Web↔Base MySQL (Écriture) injection SQL commande/stock base modifiée fraudé [E34],[E67],[E12] | Élevé | Réduire | ISO27002-8.15 | À décider | À désigner |
| M103 | Shopix — Frontière Site Web↔Base MySQL (Écriture) admin hash SHA1 obsolète brute force mots de passe clients volés [E65],[E67] | Élevé | Réduire | — | À décider | À désigner |
| M106 | Shopix — Frontière Site Web↔Espace Fichier uploads scripts PHP malveillants dossiers images exécution arbitraire [E68],[E12] | Élevé | Réduire | ISO27002-8.14 | À décider | À désigner |
| M107 | Shopix — Frontière Site Web↔Espace Fichier uploads ZIP archives uploads FTP non chiffré fuite données personnelles clients sensibles [E68],[E12] | Élevé | Réduire | ISO27002-8.29 | À décider | À désigner |
| M111 | Shopix — Frontière Sauvegarde FTP (SFTP/FTP non chiffré) ZIP uploads sensibles stockage FTP hébergeur voisine compromission cross-tenant fuite données personnelles [E68],[E22] | Élevé | Réduire | Moyen | À décider | À désigner |
| M113 | Shopix — Périmètre Hébergeur Mutualisé HostPlanet isolation non vérifiable voisine compromise cross-tenant fuite clients commande stock partagé [E49],[E22],[E31] | Élevé | Réduire | Faible | À décider | À désigner |
| M001 | A01 — Site web public (PHP 8, HTML/CSS/JS) | Élevé | Réduire | Élevé | À décider | À désigner |
| M013 | A05 — Espace fichier (uploads) | Élevé | Réduire | Élevé | À décider | À désigner |
| M048 | A19 — Admin (comptes, exports csv) | Élevé | Réduire | Faible | À décider | À désigner |
| M062 | A27 — Comptes préparateurs | Élevé | Réduire | Moyen | À décider | À désigner |
| M067 | A29 — Hébergement mutualisé HostPlanet | Élevé | Réduire | Élevé | À décider | À désigner |
| M082 | A32 — Clients boutique | Élevé | Réduire | Moyen | À décider | À désigner |
| M092 | A37 — MailJet e-mailing — Prestataire | Élevé | Éviter | Faible | À décider | À désigner |
| M100 | Shopix — Frontière Site Web↔MailJet (SMTP+API) clé API exposée code injecte spam phishing noms clients [E50],[E80] | Élevé | Réduire | Élevé | À décider | À désigner |

## 3. Acceptation du risque résiduel

Un risque résiduel n'est accepté que **par écrit**, par une personne qui en a la responsabilité (autorité d'homologation) : qui, quand, pourquoi (référentiel `ANSSI-HOMOLOGATION`). Dans le site, la décision « accepté tel quel », « accepté avec modification » ou « refusé » et son commentaire sont consignés à la fin de ce document.

## 4. Plan de suivi (proposition par défaut, à valider par la direction)

| Niveau du risque | Revue proposée |
|---|---|
| Critique | tous les mois, jusqu'à la mise en œuvre de la mesure, puis tous les trimestres |
| Élevé | tous les trimestres |
| Moyen | tous les semestres |
| Faible | une fois par an |

Déclencheurs d'une nouvelle analyse, quel que soit le niveau :

- changement de périmètre (nouveau site, nouvelle application, nouveau service) ;
- incident de sécurité significatif, y compris chez un fournisseur ou un client ;
- arrivée d'un nouveau fournisseur ou d'un nouveau prestataire ayant accès au système ;
- évolution d'une obligation réglementaire ou contractuelle (RGPD, NIS2, exigences clients) ;
- modification d'un document d'origine de l'analyse (le site le signale : les livrables sont alors « périmés »).

## Décisions enregistrées

Les décisions prises dans le site s'ajoutent ci-dessous, dans l'ordre où elles sont enregistrées.

