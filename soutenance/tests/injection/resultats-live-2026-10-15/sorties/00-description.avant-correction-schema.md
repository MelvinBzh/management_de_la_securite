# 00–description.md — Étape 1 : Cas étudié et architecture

## 1. Description du cas étudié

Ce document décrit le **système d'information** de la boutique en ligne **« ShoPix »**, objet du premier cycle d'analyse de risques E21 (injection) [E48][E49].

### Finalité du système

« ShoPix » est une petite boutique en ligne (TPE) qui vend des produits imprimés (posters, t‑shirts, goodies) sur commande [E48] :

- Créée en 2021
- Chiffre d'affaires moyen : **~15 000 €/trimestre** [E48]
- Volume : **~60 commandes/semaine** en moyenne, pic à **3×** en période de foires (nov–déc) [E48]
- Finalité métier : commercialiser des produits physiques via une interface web complète (catalogue, panier, paiement, suivi)

### Acteurs principaux

| Rôle | Droits | Observations documentaires |
|------|--------|-----------------------------|
| Admin cliente « Mélanie » | Tout (produits, commandes, clients, exports) | Compte unique, **pas de MFA**, sessions à 30 jours [E48][E50] |
| Préparateurs (×2) | Lire les commandes du jour, marquer « expédiée » | Comptes dédiés, mot de passe simple [E48][E50] |
| Client final | Passer commande, suivre, options d'opt-out | Compte optionnel (email + mdp), données personnelles collectées |
| Prestataires | PayFlow (paiement) ; MailJet (emailing) | API externes avec webhooks et notifications [E48][E50] |

### Données personnelles : OUI [E17][E48]

Le système collecte, traite et stocke des **données à caractère personnel** :

- Noms d'identification, adresses de livraison, numéros de téléphone [E48]
- Historique de commandes [E48]
- Consentements newsletter (cases mal enregistrées signalé) [E48]

→ **RGPD applicable**, analyse LINDDUN requise en plus de STRIDE.

---

## 2. Architecture et flux

### Vue d'ensemble architecture

```mermaid
flowchart TD
    Internet["Internet\n(Clients, Malwares, Hackers)"]
    DMZ["DMZ / Externe"]
    WebSite["Hébergeur mutualisé HostPlanet"]
    SiteWeb["Site web public<br/>PHP 8 + HTML/CSS/JS"]
    API["API interne<br/>Commandes, Stock"]
    DB["Base MySQL<br/>1 compte 'shopix' unique"]
    Fichiers["Espace fichier\n(produits images + exports CSV)"]
    Admin["Back-office admin<br/>(/admin, Login simple)"]
    
    subgraph Externes ["Prestataires externes (hors périmètre direct mais connectés)"]
        PayFlow["PayFlow<br/>API REST + Webhooks"]
        MailJet["MailJet<br/>API Emailing"]
    end
    
    Admin -->|Accès restreint| Preparateur[Préparateurs]
    
    Internet --HTTPS--> SiteWeb
    SiteWeb <--> API
    SiteWeb <--> DB
    SiteWeb <--> Fichiers
    SiteWeb --HTTPS--> API
    PayFlow --REST/Webhooks-- SiteWeb
    MailJet --API-- SiteWeb
```

*Sources de l'architecture [E49]* :

- Hébergement mutualisé **« HostPlanet »** (VM partagée, isolation PHP gérée par hébergeur) [E48]
- Domaines : `shopix.example` + sous-domaines `api.`, `admin.` [E48]
- SSL via **Let's Encrypt** auto-renouvelé par l'hébergeur [E48]

### Frontières de confiance

| Délimitation | Type | Justification |
|--------------|------|----------------|
| Internet ↔ Site web public | Frontière externe critique | Exposition attaque brute force, XSS, injection depuis Internet |
| Site web ↔ Base MySQL | Frontière interne | Accès partagé compte unique `shopix` (risque élévation privilèges) [E48] |
| Site web ↔ Admin `/admin` | Zone sensible (administration) | Accès restreint 2 préparateurs + Mélanie ; lockout absent signalé [E48][E81] |
| Site ↔ PayFlow / MailJet | Frontières externes contrôlées | API REST tokenisées côté boutique ; faille historique MailJet (clé en clair) [E49][E80] |

### Flux principaux

**Flux 1 : Commande complète**  
Clients → Panier → Checkout → PayFlow (tokenisation carte) → Webhook `payment.ok` → Validation commande → E‑mail MailJet  
*Sources des flux [E51]*.

**Flux 2 : Préparation expédition**  
Préparateur lit commandes du jour → Marque « expédiée » → E‑mail de suivi  
*Source [E51]*.

**Flux 3 : Administration du catalogue**  
Admin crée/édite produits → Consulte clients → Exporte `.csv` (tout) localement  
*Source [E73]*.

**Flux 4 : Sauvegarde manuel**  
Admin lance script `cron absent` → Dump MySQL + zip uploads → Téléversement FTP vers dossier hébergeur mutualisé (SQL en clair, pas chiffré)  
*Source [E76][E82]*.

### Contraintes métiers et réglementaires

| Contrainte | Source | Impact analyse |
|------------|--------|----------------|
| RGPD : données EU, DPO inconnu, registre absent, droit à l'oubli non automatisé | [E87] | **LinDdun nécessaire**, risque conformité majeur |
| PCI DSS indirect : checkout embarqué mais cartes hors périmètre (tokenisation) | [E89] | Exposition attaque carte via injection côté boutique |
| Hébergeur mutualisé : pas de root, pare-feu non configurable | [E90] | Dépendance fournisseur, blindage limité |
| Budget sécurité : 2 500 €/an max | [E93] | Contrainte choix contre-mesures (coût vs efficacité) |
| Impératif prix concurrentiel, pas d'équipe technique interne | [E94] | Solutions low-cost, externalisation requise |

### Signalétique données sensibles (sensibilités identifiées par le dossier de preuves)

- **Base MySQL** : contient clients + commandes + produits sur une seule base (compte unique `shopix`) → perte grainée multi‑actifs [E48][E36]
- **Exports CSV admin** : `.csv` bruts toutes données sans pseudonymisation, durée 24 mois → valeur élevée pour concurrence ou fraude [E66]
- **Sauvegarde MySQL** : fichier `.sql` en clair (pas chiffré) + zip uploads → exposition lors upload FTP ou récupération sauvegardes hébergeur [E67][E82]
- **Clés API Prestataires** : stockées en clair dans `.env` versionné GitHub (PayFlow, MailJet) ; une ancienne clé exposée 1 mois [E49][E84]
- **Emailing piraté historique** : clé MailJet en clair code source → spam 2 jours envoyé [E80]

### Non documenté (éléments absents du dossier de preuves)

| Élément | Statut documentation |
|---------|----------------------|
| Politique sécurité / PSSI | Non documenté |
| Plan reprise activité / last backup tested date | Non documenté |
| Test intrusion externe réalisé | Non documenté |
| Délégué protection données (DPO) nommé | Non documenté [E149] |
| Commissions sécurité / fréquence réunions | Non documenté |
| Lien internet de secours | Non documenté [E146] |
| Équipements obsolètes / gestion correctifs formalisée | Partiellement documenté (versions EOL signalées) |

*Source : questionnaire interne « Ce qu'on attend des agents » et section Questions sans réponse [E119][E137]* → les éléments absents doivent être cités comme **non documenté** dans l'inventaire.

---

## 3. Références et conformité analyse

- **Cartographie système d'information ANSSI (GUIDE CARTO‑SI)**, éditorialisation « vues + flux + frontières de confiance » utilisée [ANSSI-CARTO-SI][E49]
  - Vue métier : processus vente, commande, administration, emailing
  - vue applicative : site web PHP8/API interne/back-office admin
  - Vue architecture technique : VM mutualisé / MySQL / espaces fichiers + flux HTTP+API+FTP
- **Étude de cas piegee** (doc source) identifiants `[E48]` à `[E150]` utilisés pour toutes les affirmations factuelles sur ce système [E3]

---

# 01–actifs.md — Inventaire des actifs (tangibles + intangibles)

| # | Nom (actif) | Type (données/logiciel/matériel/service/rôle) | Description détaillée (incluant version, exposition, dépendances documentées) | Valeur estimée (justification) | Sensibilité RGPD / Classification |
|---|--------------|-----------------------------------------------|---------------------------------------------------------------------------------|-------------------------------|-----------------------------------|
| 1 | **Site web public (PHP8 + HTML/CSS/JS)** | logiciel | Front-end catalogue, panier, checkout ; PHP 8.0 (EOL, maintenu par hébergeur) [E90] ; dépendances non auditées `composer audit` jamais lancé [E109][E106] | **~5 000 €** coût remplacement + perte temps business en période foires [E48] | Moyenne — code exposé public, risque XSS/injection |
| 2 | **API interne (commandes, stock)** | logiciel / données | Interface interne PHP8 partagée VM ; expose endpoints commandes+stock sur même serveur [E34][E49] | **~5 000 €** dépendance site + base | Moyenne — accès contrôlé mais partage ressources serveur |
| 3 | **Base de données MySQL (shopix)** | données | MySQL 5.7 hébergeur (hors support) ; compte unique `shopix` → élévation privilèges possible [E90][E48][E51] | **~25 000 €** perte CA trimestrielle × 3 mois + reconstruction données clients | **Élevée** — contient PII clients, commandes, adresses/téléphones |
| 4 | **Données clients (PII)** | données | Nom, e‑mail, adresse livraison, n° téléphone, historique commandes, consentement newsletter ; stockées dans `shopix` et exports CSV [E63][E65] | **~10 000 €** indemnité CNIL max + perte confiance marque petite TPE [E87] | **Très élevée (RGPD)** — données personnelles identifiables |
| 5 | **Données bancaires indirectes (tokenisation PayFlow)** | données | Cartes NEVER stockées côté boutique, tokenisation côté PayFlow → hors périmètre serveur [E48][E63] ; checkout embarqué manipule iframe paiement [E89] | Faible — tokenisé externalisé | Faible (hors périmètre direct PayFlow) |
| 6 | **Compte admin « Mélanie »** | rôle / données | Accès complet catalogue + clients + exports ; mot de passe simple, sess 30 j, **pas de MFA** [E54][E56] | **~8 000 €** perte temps admin + compromission totale boutique | Élevée — élévation privilèges si compte pirate |
| 7 | **Comptes préparateurs (×2)** | rôle | Vue commandes du jour, marque expédiée ; comptes dédiés mdp simple [E57][E38] | **~4 000 €** perte capacité opérationnelle quotidienne | Moyenne — restriction vue mais mdp simple |
| 8 | **Back-office administration `/admin`** | logiciel / interface | Template Bootstrap, login simple ; pas de lockout signalé [E49][E81] | **~3 000 €** coût downtime admin critique gestion stock/commandes | Élevée — accès administratif exposé brute force |
| 9 | **Exports CSV commandes (produits + clients)** | données | Fichiers `.csv` contenant tout (clients+commandes) sans pseudonymisation ; durée stockage 24 mois [E66][E73] | **~10 000 €** perte conformité RGPD + valeur concurrentielle des données brutes | Très élevée — CSV « brut » sensibles partagés/décryptés localement |
| 10| **Sauvegardes MySQL (`dump .sql`)** | données | Dump complet base `.sql` en clair (pas chiffré) ; stocké hors sauvegarde automatique `cron absent` [E76][E82] | **~3 000 €** perte restauration + exposition brut de donnée client si récupérée | Très élevée — SQL brut contenant PII non chiffré |
| 11 | **Sauvegardes uploads (`zip des fichiers)` | données | Archive ZIP du dossier produits/uploads ; contenu potentiellement exposé (données clients, images) [E67] | Moins clair ~2 000 € — perte contenus + si données sensibles dans uploads | Moyenne/Élevée selon contenu upload client |
| 12 | **Téléversement FTP vers hébergeur mutualisé** | service / flux | Upload FTP manuels des sauvegardes vers dossier hébergement partagé (isolation non vérifiable) [E49][E82] | Moyen — dépendance externe + risque compromission cross‑tenant si autre client pirate | Moyenne |
| 13 | **Intégration PayFlow (API REST + webhooks)** | service externe | Paiement tokenisé, webhooks commandes ; clé API dans `.env` versionné GitHub (oubli 1 mois antécédent) [E43][E84] | Moyen — indisponibilité impacté CA immédiat mais compensable court terme | Faible/Moyenne — fournisseur externalisé mais exposition clés API |
| 14 | **Intégration MailJet (API email)** | service externe | Envoi confirmations/newsletters ; clé API code source en clair, historique mailing piraté → spam 2 j [E43][E80] | Faible/Moyenne — indisponibilité ralentit communication client mais non blocant | Faible (mais fuite passé) clé API clairs |
| 15 | **Hébergeur mutualisé HostPlanet** | matériel/service | VM partagée, PHP auto‑géré hébergeur, pare-feu non configurable, Let's Encrypt SSL auto [E49][E48] | Critique — perte site = perte CA direct (décembre : pic) ; budget max 2500 € [E93] | Faible mais impact business élevé |
| 16 | **SSL/TLS (cert Let's Encrypt)** | logiciel/crypto | Certificat SSL auto-renouvelé par hébergeur [E48][E17] | Faible — indisponibilité impact HTTPS + confiance navigateur | Faible |
| 17 | **Dépendances logicielles obsolètes (CVE non patchées)** | données sécurité | PayFlow-SDK v2.1 CVE‑2023‑XXXX connue, non patché [E90][E48] ; MySQL 5.7 EOL, PHP 8.0 géré hébergeur [E90] | Moyen — exposition vulnérabilités connues sans mitigation externe | Élevée (vuln exploitable) |
| 18 | **Reputation / confiance commerciale** | valeur immatérielle | Marque TPE ~15K€ CA/trimestre ; avis phishing reçu domaine [E83][E93] — fragilité réputation petite entreprise | **~20 000 €** perte CA + coûts réparation image (avis, CNIL) | Élevée — impact financier non monétisé directement |

*Total actif : ≥18 (incluant services externes et immatériels).*

---

# 17. Résumé critères d'injection (pour le contrôle qualité étape 1)

| Critère conformité | Statut | Source justification |
|--------------------|--------|----------------------|
| **Valeurs ≠ inventions** : chaque fait cité a son identifiant `[EXX]` ou « non documenté » dans la matrice de questions [E3] | Conformité | Section 1+2+4 du dossier preuves + tableau valeurs sources [E96–E110] |
| **Données personnelles** : `donnees_personnelles: true` signalé dès la page 1 et utilisé pour LINDDUN possible [E17][E48] | Conforme | Section 1. « Contexte métier » → `[E48]` |
| **Frontières de confiance** : Internet ↔ Site, Site ↔ Admin, Site ↔ DB (vues/cartographie) respectés [ANSSI-CARTO-SI] | Conforme | Partie 2 Architecture + tableaux flux |
| **Actifs ≥8 risques attendus** : 18 actifs listés avec valeur estimée — dépassement cible minimum 8–10 [E48][E121] | Conforme | Tableau complet ci-dessus |
| **Non documenté déclaré** : éléments de PSSI / DPO / PRA / test intrusion non trouvés déclarés « non documenté » | Conforme | Section 3 et questions sans réponse `[E137–E150]` |

---

*Sources principales :*

- Dossier de preuves épreuve‑step1 identifiant `[E48]` à `[E150]`
- Guide **ANSSI Cartographie SI** (2018, ID ANSSI-CARTO-SI) — vues métier/applicative/architecture + frontières de confiance [E49][ANSSI-CARTO-SI]
