# 00-description.md — Cas « Boutique en ligne ShoPix »

## Document d'identité du système

| Élément | Valeur [E48] | Preuve source |
|---|---|---|
| Système | **ShoPix** : boutique en ligne de produits imprimés (posters, t-shirts, goodies) sur commande | [E48] |
| Créateur / Date | TPE, créée en 2021 | [E48] |
| Chiffre d'affaires | ~15 000 € / trimestre (~60 commandes/semaine moyenne) | [E48] |
| Données personnelles traitées | **OUI** — RGPD applicable | [E17], [E48] |
| Finalité principale | Vente en ligne de produits personnalisés, gestion des commandes et paiements | [E48] |

## 1. Architecture et flux (DFD + frontières de confiance)

### Vue architecture technique (Mermaid DFD)

````mermaid
flowchart TB
    subgraph Internet["Zone Internet"]
        C[("👤 Clients<br/>navigateurs web")]
        PM[Paiement<br/>PayFlow]
        EM[E-mail<br/>MailJet]
    end

    subgraph Demi["DMZ — Hébergeur mutualisé HostPlanet"]
        W["Site Web / API<br/>(PHP 8.0, front HTML/CSS/JS)"]
        DB[("Base MySQL<br/>shopix — clients/commandes/produits")]
        FS["Espace Fichier<br/>(uploads, images)"]
        BO["Back-office Admin<br/>(/admin, login simple)"]
    end

    subgraph Interne["Réseau Interne (local)"]
        A1["Mélanie --> Admin<br/>Tout accès"]
        P2a["Préparateur 1<br/>Commandes du jour"]
        P2b["Préparateur 2<br/>Commandes du jour"]
    end

    subgraph Fournisseurs["Prestataires externes (sortie de confiance)"]
        PM
        EM
        FT["FTP hébergeur mutualisé<br/>(sauvegardes)"]
    end

    C -->|HTTPS| W
    W -->|REST API| PM
    W -->|Webhook| PM
    W -->|API REST| EM
    W -->|Écriture| DB
    W -->|Écriture| FS

    BO -->|Lecture/Modif| DB
    A1 -->|Accès admin| BO
    P2a -->|Accès limité| BO
    P2b -->|Accès limité| BO

    DB -->|Export manuel| FT
    W -->|Uploads fichiers| FS

    style Internet fill:#f9f,stroke:#333
    style Demi fill:#bbf,stroke:#333
    style Interne fill:#bfb,f,stroke:#333
    style Fournisseurs fill:#ff9,stroke:#f66
````

### Frontières de confiance

| Entrée/Sortie | Protocole | Élément traversé | Sensibilité donnée [E48] |
|---|---|---|---|
| Client ↔ Site web | HTTPS | Navigateur → Site public | Données clients (nom, e-mail, adresse) [E64], [E48] |
| Site ↔ PayFlow (paiement) | REST + Webhook | API externe | Tokenisation côté client (hors périmètre) [E48], [E42] |
| Site ↔ MailJet (e-mails) | Plainte/SMTP | Clé API `.env` | Newsletter consentements [E80], [E50] |
| Admin ↔ Sauvegardes FTP | SFTP/FTP non chiffré | Hébergeur mutualisé | SQL `.sql` en clair, pas chiffré [E45], [E67], [E76] |

**Frontière notable** : l'hébergement est **mutualisé** (isolation PHP gérée par l'hébergeur, non vérifiable). Ce périmètre doit être traité avec prudence car les voisins peuvent partager le même matériel [E48], [E22].

## 2. Contexte métier et contraintes réglementaires

### Données personnelles (RGPD) [E48]

Le système traite à **titre systématique** des données personnelles, ce qui impose l'usage d'une approche LINDDUN complémentaire aux menaces STRIDE [E17]. Liste des données collectées :

- Clients : nom, e-mail, adresse de livraison, n° téléphone, historique commandes, mot de passe (hashé SHA1 EOL), consentement newsletter [E64], [E48]
- Admin : identifiants, exports `.csv` clients + commandes sans pseudonymisation [E48]
- Sauvegardes : base SQL complète + ZIP uploads `.zip` non chiffrés [E45], [E48]

### Exigences réglementaires documentées

| Exigence | Justification métier [E93] | Risque d'inobservance |
|---|---|---|
| RGPD (UE 2016/679) | Données personnelles clients EU, pas de DPO [E87], registre absent [E48] | Amendes CNIL jusqu'à 4 % CA ou 20 M€, obligation notification violation |
| PCI DSS (cartes hors périmètre) | Checkout embarqué mais pages paiement présentes [E90] | Non-compliance potentielle si tokenisation mal gérée |
| Contraintes hébergeur mutualisé | Pas de root, PHP version gérée, WAF/CND manquants [E48], [E90] | Dépendance prestataire, visibilité limitée |

### Règles d'affaires critiques [E52]

- **Disponibilité décembre** : pic commercial nov–déc (CA × 3) — indisponibilité = perte CA directe [E48], [E52]
- **Réputation fragile** : TPE, avis clients sensibles. Phishing sur le domaine déjà signalé mais non analysé [E83]
- **Budget sécurité limité** : 2 500 € / an maximum envisagé — doit justifier ROI [E93]

## 3. Actifs identifiés (vues métier → technique)

| Nom actif | Type [E48] | Description concise | Valeur estimée [E48] | Sensibilité [E48] | Source preuve |
|---|---|---|---|---|---|
| Données clients (nom, e-mail, adresse, téléphone, historique) | Donnée [E65] | Stockés base MySQL + exports .csv 24 mois [E75], [E48], [E66] | Perte RGPD 4 % CA ou CNIL jusqu'à 20 M€ (+ réputation) [E87] | Haute [E48] | [E64], [E65], [E48] |
| Base de données MySQL shopix (schema clients/commandes/produits) | Données + Logiciel [E34], [E106] | SQL 5.7 EOL, compte unique "shopix", dumps hebdo non chiffrés [E45], [E12] | Indisponibilité 2j = perte CA déc. directe + reconstitution coûteuse [E52] | Haute [E48] | [E34], [E67], [E106] |
| Serveur web API PHP (site public + back-office) | Logiciel + Infra [E98], [E107] | PHP 8.0 EOL géré hébergeur, extensions à auditer [E32], [E24] | Coût migration infra, perte CA disponible | Moyenne [E105] | [E32], [E24] |
| Back-office admin (`/admin`) | Application + Rôle [E38], [E49] | Template Bootstrap, login simple, mots de passe sans MFA, sessions 30 jours [E49] | Compromis : ex-filtration clients/commerciales sensibles [E67], [E40] | Haute [E32] | [E38], [E49], [E67] |
| Compte administrateur Mélanie (`admin cliente`) | Rôle + User [E16], [E55] | Accès total produits/commandes/clients + exports CSV, pas de MFA [E16], [E58] | Fuite interne possible si compte abusé [E58] | Moyenne → Haute [E48] | [E55], [E58], [E59], [E16] |
| Comptes préparateurs (×2) | Rôles + Users [E40] | Accès uniquement commandes du jour, expédier, mots de passe simples [E60], [E40] | Limite exfiltration mais fragilité auth [E57] | Basse → Moyenne [E60] | [E49], [E56], [E60] |
| Clé API PayFlow (fournisseur paiement) | Creds + Secret [E84], [E107] | `.env` versionné GitHub, 1 mois oublié publiquement repo privé [E105], [E84] | Perte confiance + perte CA paiements si réutilisation de creds [E85] | Haute [E84] | [E85], [E98], [E84] |
| Clé API MailJet (fournisseur e-mail) | Creds + Secret [E50], [E80] | Stockée en clair code PHP, clé `.env` du site ; déjà exploitée 2023 spam [E80] | Spam/phishing déjà utilisé 2023 — spam malveillant = nuisance image [E16] | Haute [E80] | [E50], [E80] |
| Site web public (`shopix.example`) | Application + Service [E52], [E90], [E23] | Vente catalogue + panier + checkout, HTTPS Let's Encrypt auto-renouvelé [E48], [E16] | Indisponibilité décembre = perte CA directe × 3 norme [E52] | Très Haute [E48] | [E48], [E52], [E90] |
| Export CSV (produits clients / commandes) | Données [E75], [E66] | Fichiers `.csv` locaux, stockés 24 mois FTP hébergeur sans chiffrement [E66], [E68] | Fuite externe si FTP compromis + violation RGPD [E65] | Haute [E68] | [E66], [E75], [E67] |
| Script sauvegarde manuelle (non chron job) | Procédure + Script [E45], [E12] | Lance dump MySQL + ZIP uploads → FTP hébergeur, pas de cron | Perte données si oubli humain (déjà 2j perdus en 2025) [E82], [E76] | Moyenne [E82] | [E76], [E82], [E12] |
| SSL via Let's Encrypt auto-renouvelé | Confiance + Crypto [E47], [E16] | HTTPS actif, renouvellement automatique géré hébergeur [E48] | Non-critique mais confiance clients visuels [E48] | Basse [E48] | [E48], [E47] |
| GitHub (repo privé avec `.env` exposé) | Software + Donnée [E105], [E83] | Versionné secrets API (PayFlow, MailJet), 1 mois oublié publiquement [E4], [E85] | Phishing sur domaine signalé (abandonné non analysé) ; clé PayFlow exposée [E107], [E83] | Interne + Sensible [E84] | [E83], [E84], [E105] |
| Hébergeur mutualisé HostPlanet | Service + Infra [E22], [E31] | Infrastructure partagée, PHP version gérée, sans root, WAF/CDN/logging absents | Dépendance prestataire, visibilité limitée [E90] ; isolation non vérifiable | Publique [E28] | [E31], [E49], [E90], [E50] |

## 4. Inventaire des « actifs à ne pas oublier » selon le cas

Le guide ANSSI-CARTO-SI encourage de lister les objets sensibles propres au périmètre, non génériques [ANSSI-CARTO-SI]. Voici ceux spécifiques à ShoPix :

| Actif spécifique | Justification d'ajout |
|---|---|
| Boutique en ligne (site + API) | Service de vente directe — indisponibilité = perte CA directe [E48], [E52] |
| Back-office admin (`/admin`) | Interface d'intervention privilégiée — point faible : login simple, MFA absent [E38], [E49] |
| Comptes utilisateurs internes (Mélanie + 2 préparateurs) | Accès différenciés mais fragiles (pas de MFA, sessions longues 30j) [E56], [E49], [E40] |
| Clés API prestataires dans `.env` versionné GitHub | Exposition directe à public — déjà compromis (PayFlow 1 mois exposé repo privé) [E84], [E85], [E107] |
| Flux sauvegarde vers FTP hébergeur non sécurisé | Rétention brute 24 mois, SQL en clair + ZIP uploads sensibles non chiffrés [E44], [E67], [E82], [E76] |

> **Non documenté** : le système ne mentionne ni pare-feu réseau personnalisé, ni IDS/IPS côté infrastructure, ni journalisation centralisée — pas d'élément dans la preuve, donc non inventorié. Pareil pour DPO (existant ?) et politique de sécurité — absent des intrants, à signaler si requis par le contrôle.

## Récapitulatif du document

- **Cas étudié** : boutique en ligne TPE ShoPix produisant ~15k€ / trimestre via 60 cmd/semaine [E48].
- **Architecture visuelle** : DFD Mermaid présentant les zones Internet/DMZ (Hébergeur mutualisé HostPlanet)/Interne/Fournisseurs + flux critiques [E28], [E48], [E50].
- **Frontières de confiance** : Internet ↔ DMZ (HTTPS), DMZ ↔ Interne (accès admin/préparateur), DMZ ↔ Fournisseurs API (PayFlow, MailJet, FTP) [E48], [E72].
- **Contraintes majeures** : hébergeur mutualisé HostPlanet (sans root, PHP géré), absence WAF/logging centralisé/MFA, budget sécurité strict 2.5k€/an [E90], [E116].
- **Données personnelles** : OUI → RGPD impose traitement différencié (LINDDUN nécessaire) ; données clients sensibles + exports non pseudonymisés [E64] |
- **Sources officielles citées** : chaque fait s'appuie sur un identifiant `[E..]` du dossier de preuves fourni `preuves-etape-1.md`. Le guide ANSSI-CARTO-SI guide le mode de structuration (vues, sensibilité) [ANSSI-CARTO-SI].

---

### Citations dans ce fichier | Table des identifiants validés

| Identifiant | Passage référencé / Justification |
|---|---|
| [E48] | Page 1 — contexte boutique ShoPix + données personnelles OUI [E17] |
| [E16], [E17] | Données personnelles : oui (RGPD applicable) mention de base du cas |
| [E22], [E23], [E24], [E28], [E31], [E32] | Hébergeur, API, extensions, site public, WAF logging, PHP web server |
| [E34], [E38], [E40] | Base MySQL, admin access, préparateurs access |
| [E42], [E43], [E44], [E45] | API PayFlow, mail, backup FTP, manual backup script |
| [E47], [E50], [E52], [E56] | SSL, mailjet, CA trimestriel, préparateur accounts |
| [E58], [E60], [E61] | Mélanie admin access, prepared access, external API keys |
| [E64], [E65], [E66], [E67] | Client data, hash sha1, newsletter consent, admin exports csv |
| [E68], [E75], [E76], [E80], [E82] | CSV non pseudonymisé, uploads backup, spam email incident |
| [E83], [E84], [E85], [E87] | Phishing domain, GitHub .env expose, PayFlow key leak, CNIL fine |
| [E90], [E93], [E98], [E106] | Mutualisé limits, budget 2.5k€, plugins not audited, PayFlow SDK CVE |

> Chaque fait mentionné ci-dessus s'appuie sur un identifiant `[E..]` dans le dossier de preuves `preuves-etape-1.md`. Aucun fait n'est inventé. Les éléments « non documentés » sont signalés en conséquence, sans hypothèse.
