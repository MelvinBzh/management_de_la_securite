# Étape 3 — Identification des menaces (cas ShoPix)

> Produit par la chaîne E21 (étape 3 · identifier les menaces).
> Entrées : `00-description.md` (DFD + frontières F1–F4), `01-actifs.md` (A-01…A-16), `02-methodes.md` (§ 6), `knowledge_base/README.md`, `etude-de-cas.md`.
> Statut : proposition — **aucun `valide_par`** : les décisions (validation, puis évaluation étape 4) sont humaines.

## 1. Méthode appliquée

- **STRIDE** (S/T/R/I/D/E) appliqué **élément par élément du DFD**, en priorité aux **passages des frontières de confiance** F1 → F4 (c'est là que se concentrent les attaques) : F1 Internet → HostPlanet, F2 HostPlanet → prestataires, F3 absence de segmentation interne, F4 mutualisation hébergeur.
- **LINDDUN** appliqué **uniquement** sur les actifs de données personnelles : **A-05** (données clients), **A-06** (exports .csv), **A-11** (consentement newsletter) — sans dupliquer les menaces STRIDE.
- **MITRE ATT&CK** pour ancrer les scénarios : seule technique citable dans l'index = `ATT&CK-T1190` (Exploit Public-Facing Application) ; toute autre technique est signalée en § 6 (à ajouter à l'index avant citation).
- **Pas d'évaluation** probabilité/impact ici : c'est l'étape 4 (DREAD / CVSS).

## 2. Tableau des menaces

| ID | Actif concerné | Catégorie (grille) | Description (réaliste, argumentée) | CVE si connue | Source |
|---|---|---|---|---|---|
| **M-01** | A-03, A-09 (back-office `/admin`, compte admin) | STRIDE-S | **Usurpation du compte admin par brute force au passage de F1.** Incident documenté en 2024 : ~1 000 tentatives/24 h dans les logs HTTP sur `/admin`, **aucun verrouillage de compte** (pas de lockout), mot de passe simple, **pas de MFA**, sessions de 30 jours. Une attaque par dictionnaire sans limite de débit aboutit à un accès total au back-office (produits, commandes, clients, exports). | — | STRIDE-S ; etude-de-cas.md § 6 ; 00-description.md F1 |
| **M-02** | A-05 (données clients) | STRIDE-S | **Usurpation des comptes clients par credential stuffing (F1).** Comptes optionnels protégés par un hash **SHA-1** (algorithme obsolète, attaquable hors ligne, présent dans les tables arc-en-ciel) ; réutilisation de mots de passe fréquente côté client. Une liste d'identifiants volée ailleurs permet le credential stuffing sur la boutique → prise de contrôle de comptes, lecture de l'historique de commandes, des adresses et des téléphones (données RGPD). | — | STRIDE-S ; etude-de-cas.md § 4, § 9 |
| **M-03** | A-08, A-14, A-12 (clé MailJet, réputation, domaine) | STRIDE-S | **Usurpation de l'identité « ShoPix » (emailing + domaine), F1/F2.** Incident 2023 : la clé MailJet (en clair dans le code) est compromise → **2 jours de spam envoyés au nom de la boutique** ; le domaine a par ailleurs déjà reçu un **avis de phishing abandonné sans analyse** (A-12). Un attaquant abusant de la marque (e-mails frauduleux, page de phishing sur `shopix.example`) escroque des clients et détruit durablement la confiance (A-14). | — | STRIDE-S ; etude-de-cas.md § 6 |
| **M-04** | A-01, A-04 (site public, MySQL) | STRIDE-T | **Falsification des données du site exposé par exploitation de l'application (F1).** Le site public est exposé sur Internet (PHP 8.0 **EOL**, application simple **sans WAF**), la base MySQL 5.7 est en fin de vie avec **un seul compte `shopix` à pleins droits**. Une injection SQL sur un paramètre du catalogue/checkout (aucune mention de requêtes préparées dans le cas) permet de **lire ou modifier** prix, commandes et comptes — accès initial via application publique (`ATT&CK-T1190`). | PHP 8.0 / MySQL 5.7 EOL (pas de CVE énoncée — versions obsolètes, CVE à rechercher) | STRIDE-T ; ATT&CK-T1190 ; etude-de-cas.md § 9 |
| **M-05** | A-01, A-16 (checkout, PayFlow) | STRIDE-T | **Falsification du flux de paiement : exploitation du SDK PayFlow 2.1 vulnérable (F2).** Le SDK de paiement 2.1 porte une vulnérabilité connue **non patchée** au checkout (pages de paiement embarquées) ; `composer audit` n'a **jamais été lancé** et le plugin impressions 3.2.1 n'est pas audité → aucune visibilité sur l'état des dépendances. Un exploit sur ce composant (ou un webhook `payment.ok` falsifié) peut détourner des transactions. | **CVE-2023-XXXX** — placeholder de l'énoncé, **référence exacte à confirmer** (ne pas inventer de numéro) | STRIDE-T ; ATT&CK-T1190 ; etude-de-cas.md § 9 |
| **M-06** | A-06, A-09 (exports .csv, admin) | STRIDE-R | **Répudiation des actions d'administration (F3).** Aucune journalisation centralisée : création/modification de produits, exports .csv (contenant tout), marquage/suppression de commandes ne laissent **aucune trace**. Un admin ou un préparateur peut nier une action (export frauduleux, modification de prix) — aucune preuve exploitable pour un litige client, une enquête ou une réclamation RGPD. | — | STRIDE-R ; etude-de-cas.md § 2 ; 00-description.md F3 |
| **M-07** | A-08 (clé API PayFlow, `.env`) | STRIDE-I | **Divulgation de la clé API PayFlow versionnée (F2).** Incident 2024 : le `.env` contenant la clé PayFlow a été **versionné sur GitHub et oublié 1 mois** (repo privé). Tout accès au dépôt (leak, compte développeur compromis, repo rendu public, CI exposée) divulgue la clé → paiements frauduleux débités sur le compte de la boutique et chargebacks ; rien n'indique une rotation de la clé après découverte. | — | STRIDE-I ; etude-de-cas.md § 6 ; 01-actifs.md A-08 |
| **M-08** | A-07, A-06 (sauvegardes, exports) | STRIDE-I | **Divulgation des sauvegardes en clair au passage de F2/F4.** La sauvegarde hebdo (dump `.sql` complet clients + commandes, `.zip` des uploads) est déposée **par FTP vers un dossier du même hébergeur mutualisé**, **sans chiffrement**. Un autre locataire de la machine (F4, isolation « non vérifiable ») ou un tiers ayant accès à ce dossier peut lire le SQL en clair → fuite massive de données personnelles et d'informations métier. | — | STRIDE-I ; 00-description.md F2, F4 ; etude-de-cas.md § 4 |
| **M-09** | A-13, A-01 (disponibilité, site) | STRIDE-D | **Déni de service / indisponibilité en période critique (F1/F4).** Pas de monitoring, pas de WAF, pas de CDN, pas de redondance ; la VM est **mutualisée** avec d'autres clients sans isolation vérifiable (F4). Un pic légitime ×3 (nov–déc), une saturation par un autre locataire ou une attaque rendent le site indisponible **précisément quand le CA est maximal** (~1 500 €/semaine perdus, irrattrapables selon la règle métier). | — | STRIDE-D ; etude-de-cas.md § 2, § 10 ; 00-description.md F4 |
| **M-10** | A-01, A-03, A-04 (site, back-office, MySQL) | STRIDE-E | **Élévation de privilèges par absence de segmentation (F3).** Site, API interne, back-office, MySQL et fichiers partagent la **même VM** sans cloisonnement ; un seul compte MySQL `shopix` à pleins droits. Une compromission initiale du site public (M-04/M-05, accès via `ATT&CK-T1190`) donne **directement** accès à la base complète, aux exports et au back-office : la compromission d'un composant vaut compromission de tous. | — | STRIDE-E ; ATT&CK-T1190 ; 00-description.md F3 |
| **M-11** | A-06 (exports .csv) | LINDDUN-L, LINDDUN-I | **Corrélation et identification des personnes via les exports non pseudonymisés (F3).** Les `.csv` contiennent **tout** (clients + commandes) **sans pseudonymisation**, conservés **24 mois** : le croisement (L) des commandes, adresses, téléphones et historiques permet d'**identifier** (I) des personnes précises, puis de réutiliser ce fichier client (revente à un concurrent, ciblage frauduleux). | — | LINDDUN-L ; LINDDUN-I ; 01-actifs.md A-06 |
| **M-12** | A-05 (données clients) | LINDDUN-DI | **Divulgation des données personnelles clients.** Nom, e-mail, adresse, téléphone, historique de commandes et hash SHA-1 pour l'ensemble du fichier clients : toute compromission (M-04, M-08, M-10) expose en masse des données personnelles de citoyens européens. La notification de violation (art. 33 RGPD, 72 h) n'est **pas préparée** (aucune procédure) — risque réglementaire en plus du préjudice aux personnes. | — | LINDDUN-DI ; etude-de-cas.md § 4, § 7 |
| **M-13** | A-11, A-05 (consentement newsletter, données clients) | LINDDUN-NC | **Non-conformité RGPD des traitements.** Registre des traitements **absent**, pas de DPO, mentions légales **incomplètes**, droit à l'oubli **non automatisé**, consentement newsletter « cases décochées mal enregistrées » (A-11). Le traitement est en non-conformité récurrente (art. 5, 6, 17, 30, 37 RGPD) : plainte ou contrôle CNIL → mise en demeure puis amende (jusqu'à 2 % du CA mondial), sans compter le risque réputation. | — | LINDDUN-NC ; etude-de-cas.md § 7 ; 01-actifs.md A-11 |
| **M-14** | A-07, A-04 (sauvegardes, base commandes) | STRIDE-D | **Perte de commandes par défaillance de sauvegarde (F3).** Sauvegarde **manuelle hebdomadaire** (cron absent) : si elle est oubliée et que le disque hébergeur est réinitialisé — incident **réel de 2025** — 2 jours de commandes sont perdus **définitivement**. La restauration n'est jamais testée et le dump n'est pas chiffré ; le scénario se reproduit à chaque oubli manuel combiné à une défaillance disque. | — | STRIDE-D ; etude-de-cas.md § 6 |

## 3. Couverture des frontières de confiance (F1–F4)

| Frontière | Menaces concernées | Points d'attention |
|---|---|---|
| **F1** — Internet → HostPlanet | M-01, M-02, M-03, M-04, M-09 | Expositions HTTPS ; brute force `/admin` (2024) ; pas de lockout, pas de MFA, pas de WAF |
| **F2** — HostPlanet → prestataires | M-03, M-05, M-07, M-08 | Clés API en clair dans `.env` (incidents 2023/2024) ; SDK PayFlow non patché ; sauvegardes FTP non chiffrées sur le même hébergeur |
| **F3** — interne, sans segmentation | M-06, M-08, M-10, M-11, M-14 | Site = API = back-office = MySQL = fichiers sur la même VM ; un compte `shopix` à pleins droits ; pas de journalisation |
| **F4** — mutualisation hébergeur | M-08, M-09 | Isolation PHP « non vérifiable » ; autres clients sur la même machine |

## 4. Couverture des scénarios issus des incidents / vulnérabilités documentées

| Scénario (étude de cas) | Menace(s) |
|---|---|
| Brute force `/admin` (2024, ~1 000 tentatives/24 h, pas de lockout) | M-01 |
| Clé MailJet piratée (2023, spam au nom de la boutique) | M-03 |
| Clé PayFlow versionnée sur GitHub (2024, oubliée 1 mois) | M-07 |
| Perte de 2 jours de commandes (2025, sauvegarde manuelle oubliée + disque réinitialisé) | M-14 |
| Avis de phishing sur le domaine (abandonné, non analysé) | M-03 |
| `composer audit` jamais lancé + plugin impressions 3.2.1 non audité | M-05 |
| PayFlow-SDK 2.1 non patché (CVE-2023-XXXX placeholder) | M-05 |
| PHP 8.0 EOL (versions/vulnérabilités obsolètes) | M-04 |
| MySQL 5.7 (fin de vie, un seul compte `shopix`) | M-04 |
| Mots de passe clients hashés SHA-1 (ancien) | M-02 |
| Sessions admin 30 jours, mot de passe simple, pas de MFA | M-01 |
| Aucune journalisation centralisée | M-06 |
| Pas de monitoring / WAF / CDN, mutualisation non isolée | M-09 |

## 5. Sources (ID de `knowledge_base/README.md`)

| ID | Usage |
|---|---|
| `STRIDE-S`, `STRIDE-T`, `STRIDE-R`, `STRIDE-I`, `STRIDE-D`, `STRIDE-E` | Catégorie principale de chaque menace (grille Microsoft / Shostack) |
| `LINDDUN-L`, `LINDDUN-I`, `LINDDUN-DI`, `LINDDUN-NC` | Vie privée sur A-05, A-06, A-11 (KU Leuven ; RGPD UE 2016/679) |
| `ATT&CK-T1190` | Ancrage « Exploit Public-Facing Application » sur M-04, M-05, M-10 |
| `etude-de-cas.md` (§ 2, 4, 6, 7, 9, 10) | Faits documentés (architecture, incidents, vulnérabilités, règles affaires) |
| `00-description.md` (F1–F4, acteurs) | Frontières de confiance et éléments de chaque frontière |
| `01-actifs.md` (A-01…A-14) | Actifs concernés et sensibilité |

## 6. Sources absentes de l'index — à proposer à research (non citées comme validées)

Ces techniques ATT&CK **ne sont pas encore dans `knowledge_base/README.md`** ; elles ne sont **pas citées** dans le tableau ci-dessus et restent non référençables tant que l'index ne les a pas validées :

| Technique proposée | Justification (usage prévu) |
|---|---|
| `ATT&CK-T1110` — Brute Force | M-01 : la tentative documentée de 2024 sur `/admin` est un brute force HTTP pur (T1110.001), plus précis que T1190 |
| `ATT&CK-T1078` — Valid Accounts | M-03 / M-07 : l'abus de clés API valides (MailJet 2023, PayFlow 2024) est un abus de comptes valides, pas une exploitation de faille |
| `ATT&CK-T1566` — Phishing | M-03 : l'avis de phishing sur le domaine et l'usurpation de l'identité e-mail de la boutique relèvent du scénario phishing (T1566) |

⚠️ **CVE-2023-XXXX (M-05)** : identifiant **placeholder de l'énoncé** (`etude-de-cas.md` § 9). Aucun numéro réel n'a été inventé ; la référence exacte (CVE réelle du SDK de paiement) doit être confirmée **avant** la notation CVSS de l'étape 4.