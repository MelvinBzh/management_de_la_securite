# Rapport de contrôle

Un contrôle indépendant relit chaque étape avant la suivante. Pour chacun : ce qui n'allait pas, ce qui a changé depuis la version précédente, et le verdict.

## À faire valider par un humain

- **Étape 1 · Existant et actifs** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 00-description.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E64], [E80], [E67], [E76], [E93], [E87], [E90], [E83], [E65], [E75], [E66], [E106], [E98], [E107], [E105], [E55], [E58], [E59], [E60], [E57], [E56], [E84], [E85], [E68], [E82], [E72], [E116], [E61]. 01-actifs.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E90], [E91], [E103], [E110], [E117], [E82], [E64], [E68], [E107], [E65], [E75], [E84], [E58], [E80], [E105], [E60], [E56], [E59], [E57], [E87], [E67], [E83], [E66], [E109], [E106], [E81], [E55], [E96], [E70], [E85], [E72]. 01-actifs.md : texte d'attente à remplacer par l'information ou par « non documenté » : | A22 | PayFlow-SDK v2.1 | Logiciel | SDK paiement avec CVE-2023-XXXX connu non patché ([E107], [E109]) | Critique | [E107] | | | A36 | SDK paiement PayFlow-SDK v2.1 | Logiciel | Librairie intégration checkout API REST webhooks CVE-XXXX connu non patché dépendance cri
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `00-description.md`, `01-actifs.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Étape 2 · Choix de la méthode** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 02-methodes.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E64], [E65], [E93], [E82].
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `02-methodes.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Étape 3 · Menaces** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 03-menaces.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E81], [E67], [E76], [E64], [E84], [E83], [E105], [E65], [E106], [E66], [E61], [E55], [E82], [E59], [E98], [E108], [E80], [E87], [E90], [E68], [E58], [E56], [E60], [E85], [E107]. 03-menaces.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel | STRIDE-T | Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] | | M086 | A33 — Clés API prestataires | STRIDE-E | Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 | STRIDE-E | Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `03-menaces.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Étape 4 · Évaluation** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 04-evaluation.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E81], [E67], [E65], [E83], [E54], [E76], [E84], [E64], [E105], [E66], [E106], [E98], [E55], [E82], [E56], [E107], [E59], [E68], [E108], [E69], [E72], [E109], [E80], [E90], [E58], [E85]. 04-evaluation.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → | | M086 | A33 — Clés API prestataires (STRIDE-E) Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE-X | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 (STRIDE-E) Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX n
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `04-evaluation.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Étape 5 · Traitement** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 05-traitement.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E65], [E54], [E76], [E84], [E64], [E83], [E105], [E67], [E66], [E106], [E98], [E81], [E55], [E82], [E59], [E108], [E80], [E90], [E68], [E58], [E56], [E85], [E107]. 05-traitement.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → | | M086 | A33 — Clés API prestataires (STRIDE-E) Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE-X | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 (STRIDE-E) Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX n
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `05-traitement.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Relecture finale** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : - "A28 — Compte client optionnel" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A27 — Comptes préparateurs" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A17 — Clients (nom, email, adresse, téléphone)" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A19 — Admin (comptes, exports csv)" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A08 — MailJet e-mails" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A18 — Bancaires carte/tokenisation PayFlow" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A20 — PHP 8.0 EOL — Logiciel (hôte serveur)" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A30 — Site web public / API interne" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants.
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `registre-risques.md`, `SYNTHESE.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.

## Contrôle n°1 — Étape 1 · Existant et actifs, version 1 : NON CONFORME

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 08:45:28
- Ce qui n'allait pas : 00-description.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E90], [E64], [E67], [E88], [E89], [E117], [E83], [E93], [E105], [E55], [E60], [E85], [E80], [E66], [E76], [E82], [E59]. 01-actifs.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E90], [E91], [E103], [E110], [E117], [E82], [E81], [E57], [E64], [E68], [E107], [E65], [E75], [E84], [E58], [E80], [E105], [E60], [E56], [E59], [E87], [E67], [E83], [E106], [E66], [E98], [E88], [E76]. 01-actifs.md : texte d'attente à remplacer par l'information ou par « non documenté » : | A25 | Bibliothèque PayFlow-SDK 2.1 | Software | SDK paiement intégrée, CVE-2023-XXXX connu, non patché. Critique | Sensible | [E106] | | | A35 | Bibliothèque PayFlow-SDK v2.1 | Logiciel | CVE-2023-XXXX connus, non patché ; intégration au checkout PHP ([E107]) | Critique | [E10
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | Système | **ShoPix** : boutique en ligne de produits imprimés (posters, t-shirts, goodies) sur commande | [E48] |
  - [non soutenue] | Créateur / Date | TPE, créée en 2021 | [E48] |
  - [non soutenue] | Chiffre d'affaires | ~15 000 € / trimestre (~60 commandes/semaine moyenne) | [E48] |
  - [non soutenue] | Données personnelles traitées | **OUI** — RGPD applicable | [E17][E48] |
  - [non soutenue] | Finalité principale | Vente en ligne de produits personnalisés, gestion des commandes et paiements | [E48] |
  - [non soutenue] - Clients : nom, e-mail, adresse de livraison, n° téléphone, historique commandes, mot de passe (hashé SHA1), consentement newsletter [E48][E64].
  - [non soutenue] - Admin : identifiants, exports `.csv` clients + commandes sans pseudonymisation [E48][E64].
  - [non soutenue] - Sauvegardes : base SQL complète + ZIP uploads `.zip` non chiffrés [E48][E67].
  - [non soutenue] | Contraintes hébergeur mutualisé | Pas de root, PHP version gérée, WAF/CND manquants | Dépendance prestataire, visibilité limitée [E8][E90] |
  - [non soutenue] - **Disponibilité декабре** : pic commercial nov–déc (CA × 3) — indisponibilité = perte CA directe [E48][E117].

## Contrôle n°2 — Étape 1 · Existant et actifs, version 2 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 09:01:13
- Ce qui n'allait pas : 00-description.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E64], [E80], [E67], [E76], [E93], [E87], [E90], [E83], [E65], [E75], [E66], [E106], [E98], [E107], [E105], [E55], [E58], [E59], [E60], [E57], [E56], [E84], [E85], [E68], [E82], [E72], [E116], [E61]. 01-actifs.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E90], [E91], [E103], [E110], [E117], [E82], [E64], [E68], [E107], [E65], [E75], [E84], [E58], [E80], [E105], [E60], [E56], [E59], [E57], [E87], [E67], [E83], [E66], [E109], [E106], [E81], [E55], [E96], [E70], [E85], [E72]. 01-actifs.md : texte d'attente à remplacer par l'information ou par « non documenté » : | A22 | PayFlow-SDK v2.1 | Logiciel | SDK paiement avec CVE-2023-XXXX connu non patché ([E107], [E109]) | Critique | [E107] | | | A36 | SDK paiement PayFlow-SDK v2.1 | Logiciel | Librairie intégration checkout API REST webhooks CVE-XXXX connu non patché dépendance cri
- Ce qui a changé depuis la version précédente :
  89 ligne(s) ajoutée(s), 81 retirée(s).
  Retiré : | Élément | Valeur | Preuve |
  Retiré : | Données personnelles traitées | **OUI** — RGPD applicable | [E17][E48] |
  Retiré : subgraph Demilitarized["DMZ — Hébergeur mutualisé HostPlanet"]
  Retiré : style Demilitarized fill:#bbf,stroke:#333
  Retiré : | Entrée/Sortie | Protocole | Élément traversé | Sensibilité donnée |
  Ajouté : | Élément | Valeur [E48] | Preuve source |
  Ajouté : | Données personnelles traitées | **OUI** — RGPD applicable | [E17], [E48] |
  Ajouté : subgraph Demi["DMZ — Hébergeur mutualisé HostPlanet"]
  Ajouté : style Demi fill:#bbf,stroke:#333
  Ajouté : | Entrée/Sortie | Protocole | Élément traversé | Sensibilité donnée [E48] |
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 00-description.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E64], [E80], [E67], [E76], [E93], [E87], [E90], [E83], [E65], [E75], [E66], [E106], [E98], [E107], [E105], [E55], [E58], [E59], [E60], [E57], [E56], [E84], [E85], [E68], [E82], [E72], [E116], [E61]. 01-actifs.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E90], [E91], [E103], [E110], [E117], [E82], [E64], [E68], [E107], [E65], [E75], [E84], [E58], [E80], [E105], [E60], [E56], [E59], [E57], [E87], [E67], [E83], [E66], [E109], [E106], [E81], [E55], [E96], [E70], [E85], [E72]. 01-actifs.md : texte d'attente à remplacer par l'information ou par « non documenté » : | A22 | PayFlow-SDK v2.1 | Logiciel | SDK paiement avec CVE-2023-XXXX connu non patché ([E107], [E109]) | Critique | [E107] | | | A36 | SDK paiement PayFlow-SDK v2.1 | Logiciel | Librairie intégration checkout API REST webhooks CVE-XXXX connu non patché dépendance cri
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `00-description.md`, `01-actifs.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | Élément | Valeur [E48] | Preuve source |
  - [non soutenue] | Système | **ShoPix** : boutique en ligne de produits imprimés (posters, t-shirts, goodies) sur commande | [E48] |
  - [non soutenue] | Créateur / Date | TPE, créée en 2021 | [E48] |
  - [non soutenue] | Chiffre d'affaires | ~15 000 € / trimestre (~60 commandes/semaine moyenne) | [E48] |
  - [non soutenue] | Données personnelles traitées | **OUI** — RGPD applicable | [E17], [E48] |
  - [non soutenue] | Finalité principale | Vente en ligne de produits personnalisés, gestion des commandes et paiements | [E48] |
  - [non soutenue] | Site ↔ PayFlow (paiement) | REST + Webhook | API externe | Tokenisation côté client (hors périmètre) [E48], [E42] |
  - [non soutenue] | Site ↔ MailJet (e-mails) | Plainte/SMTP | Clé API `.env` | Newsletter consentements [E80], [E50] |
  - [non soutenue] | Admin ↔ Sauvegardes FTP | SFTP/FTP non chiffré | Hébergeur mutualisé | SQL `.sql` en clair, pas chiffré [E45], [E67], [E76] |
  - [non soutenue] Le système traite à **titre systématique** des données personnelles, ce qui impose l'usage d'une approche LINDDUN complémentaire aux menaces STRIDE [E17]. Liste des données collectées :

## Contrôle n°3 — Étape 2 · Choix de la méthode, version 1 : NON CONFORME

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 09:04:14
- Ce qui n'allait pas : 02-methodes.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E64], [E65], [E93], [E87], [E82].
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | **STRIDE** | DFD | Moyen | Analyse générale | Web app, architecture | [E48], [E49]
  - [non soutenue] | **PASTA** | Objectif métier | Fort | Impact économique | Stratégie, décisions | [E52], [E93]
  - [non soutenue] **Justification** : Le cas traite des données personnelles (RGPD applicables) [E64], a une architecture mutualisée [E49], et des enjeux d'organisation (fournisseurs, hébergeur) [E48]. STRIDE identifie les 
  - [non soutenue] 1. **DFD** → [E48] (Mermaid)
  - [non soutenue] - STRIDE : Microsoft, [E48]
  - [non soutenue] - DREAD : [E48], [E82]

## Contrôle n°4 — Étape 2 · Choix de la méthode, version 2 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 09:06:55
- Ce qui n'allait pas : 02-methodes.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E64], [E65], [E93], [E82].
- Ce qui a changé depuis la version précédente :
  45 ligne(s) ajoutée(s), 20 retirée(s).
  Retiré : | **STRIDE** | DFD | Moyen | Analyse générale | Web app, architecture | [E48], [E49]
  Retiré : | **LINDDUN** | Données personnelles | Haut | Vie privée/RGPD | Données sensibles, RGPD | [E64], [E65]
  Retiré : | **EBIOS RM** | Organisation | Fort | Administrations, enjeux métier | Administrations, OIV, NIS2 | [EBIOS-RM-2018]
  Retiré : | **PASTA** | Objectif métier | Fort | Impact économique | Stratégie, décisions | [E52], [E93]
  Retiré : ### **STRIDE + LINDDUN + EBIOS RM (A3/A4)**
  Ajouté : | **STRIDE** | DFD | Moyen | Analyse générale | Web app, architecture [E48], [E49] |
  Ajouté : | **LINDDUN** | Données personnelles | Haut | Vie privée/RGPD | Données sensibles [E64], [E65] |
  Ajouté : | **EBIOS RM** | Organisation | Fort | Administrations, enjeux métier | Administrations, OIV, NIS2 [EBIOS-RM-2018] |
  Ajouté : | **PASTA** | Objectif métier | Fort | Impact économique | Stratégie, décisions [E52], [E93] |
  Ajouté : ### STRIDE principal + LINDDUN complémentaire + EBIOS RM (A3/A4) extensif
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 02-methodes.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E64], [E65], [E93], [E82].
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `02-methodes.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | **STRIDE** | DFD | Moyen | Analyse générale | Web app, architecture [E48], [E49] |
  - [non soutenue] | **PASTA** | Objectif métier | Fort | Impact économique | Stratégie, décisions [E52], [E93] |
  - [non soutenue] **Justification** : Le cas présente une architecture mutualisée [E49] avec des données personnelles traitées [E17], et des fournisseurs externes (PayFlow, MailJet, hébergeur HostPlanet) [E48]. STRIDE ident
  - [non soutenue] Le dossier ne documente **aucune donnée personnelle** dans le système : les clients sont nommés sans détails personnels, les comptes utilisateur utilisent des identifiants génériques. LINDDUN n'est pas app
  - [non soutenue] Le système est une entreprise privée (TPE), non administrative. EBIOS RM est applicable en approche volontaire avec ses ateliers A3/A4 pour couvrir les scénarios organisationnels et écosystème [E48].
  - [non soutenue] ### STRIDE [E48], [E49]
  - [non soutenue] - **Adaptation** : S'applique directement au DFD fourni [E49], front ères Internet↔DMZ↔Interne↔Fournisseurs
  - [non soutenue] ### EBIOS RM A3/A4 [E48]
  - [non soutenue] - **Justification** : L'architecture mutualisée [E49] place le système dans un écosystème où les actions des voisins peuvent impacter le site — besoin d'une vision organisationnelle
  - [non soutenue] ### DREAD pour priorisation [E48], [E82]

## Contrôle n°5 — Étape 3 · Menaces, version 1 : NON CONFORME

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 09:20:22
- Ce qui n'allait pas : 03-menaces.md : termes absents des intrants à retirer, ou à présenter explicitement comme une hypothèse à confirmer : dkim, dmarc, spf. Ne les mentionne pas du tout, pas même pour dire qu'ils sont absents. 03-menaces.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E81], [E67], [E76], [E64], [E84], [E83], [E105], [E65], [E106], [E66], [E61], [E107], [E109], [E55], [E82], [E98], [E108], [E80], [E87], [E90], [E68], [E58], [E56], [E60], [E85]. 03-menaces.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel | STRIDE-T | SDK de paiement v2.1 contamine la logique métier avec buffer overflow dans gestion t | | M088 | A32 - Clients boutique | STRIDE-S | Attaquant : cybercriminel [E82] → Spoofing via injection SQL sur base MySQL [E49] → usurpe iden | | M097 | A35 - Extensions plugins PHP | STRIDE-S | Attaquant : attaquant externe [E82] → spoofing via plugin impressions non audité [E49] → 
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M001 | A01 — Site web public (PHP 8, HTML/CSS/JS) | STRIDE-S | Atteinte XSS dans formulaires de recherche/commentaires via injection JavaScript non validée, permettant un attaquant externe d'empiéter sur
  - [non soutenue] | M002 | A01 — Site web public (PHP 8, HTML/CSS/JS) | STRIDE-I | Fuite données clients via logs expose ou erreur tracebacks affichés aux pages d'erreur HTTP 500 contenant noms/adresses/téléphones [E49] | -
  - [non soutenue] | M003 | A01 — Site web public (PHP 8, HTML/CSS/JS) | STRIDE-T | Tampering des pages catalogue via upload de fichiers scripts malveillants dans dossiers uploads non filtrés par extension ou MIME [E49] | - 
  - [non soutenue] | M004 | A02 — API interne (PHP 8) | STRIDE-I | Fuite données sensibles clients/produits à travers les endpoints REST exposés internet sans authentification forte et rate limiting, permettant lecture brute
  - [non soutenue] | M005 | A02 — API internes (PHP 8) | STRIDE-T | Tampering des commandes en base via injection SQLi sur URL parameters non filtrées avant traitement PHP, modifiant prix/quantités livrées au client final [E
  - [non soutenue] | M006 | A02 — API internes (PHP 8) | STRIDE-R | Repudiation via absence de journalisation des appels API et hashages non vérifiés, empêchant traçage des modifications malveillantes commandées par pirates 
  - [non soutenue] | M007 | A03 — Back-office admin (/admin) | STRIDE-S | Spoofing d'administration via brute force sur login sans lockout/brute rate limiting, permettant usurpation compte admin ou préparateurs [E49], [E81] 
  - [non soutenue] | M008 | A03 — Back-office admin (/admin) | STRIDE-T | Tampering des bases de données clients via injection SQLi dans champs recherche/administration templates PHP sans escaping, modifiant commandes/comman
  - [non soutenue] | M009 | A03 — Back-office admin (/admin) | STRIDE-S | Usurpation compte préparateurs par attaquant ayant compromis session admin via XSS persistante sur page d'administration [E49] | - | STRIDE-S |
  - [non soutenue] | M010 | A04 — Base MySQL (shopix) | STRIDE-I | Fuite données brutes clients via dump SQL non chiffré exposé FTP, permettant extraction nom/email/adresse/téléphone/historique commandes [E49], [E67] | - | S

## Contrôle n°6 — Étape 3 · Menaces, version 2 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 09:27:20
- Ce qui n'allait pas : 03-menaces.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E81], [E67], [E76], [E64], [E84], [E83], [E105], [E65], [E106], [E66], [E61], [E55], [E82], [E59], [E98], [E108], [E80], [E87], [E90], [E68], [E58], [E56], [E60], [E85], [E107]. 03-menaces.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel | STRIDE-T | Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] | | M086 | A33 — Clés API prestataires | STRIDE-E | Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 | STRIDE-E | Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX
- Ce qui a changé depuis la version précédente :
  62 ligne(s) ajoutée(s), 73 retirée(s).
  Retiré : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel | STRIDE-T | SDK de paiement v2.1 contamine la logique métier avec buffer overflow dans gestion transactions, attaqu…
  Retiré : | M056 | A22 — PayFlow-SDK v2.1 — Logiciel | STRIDE-I | SDK ne chiffre pas les payloads transactionnels en transit via HTTPS faible (TLS 1.0), permettant inter…
  Retiré : | M057 | A23 — Plugin impressions v3.2.1 — Logiciel | STRIDE-T | Extension non audité par sécurité stockant images utilisateurs dans dossier /uploads writable …
  Retiré : | M058 | A23 — Plugin impressions v3.2.1 — Logiciel | STRIDE-D | Composers (v4.x) utilisé par plugin jamais audité par `composer audit`, dépendances tierces av…
  Retiré : | M059 | A24 — PayFlow (API REST + webhooks) — Prestataire | STRIDE-S | Clés API PayFlow versionnées dans fichier .env commité sur GitHub privé ([E84]), permet…
  Ajouté : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel | STRIDE-T | Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → exploitation CVE…
  Ajouté : | M056 | A22 — PayFlow-SDK v2.1 — Logiciel | EBIOS-RM-A4 | Exposition de la chaîne de confiance vers PayFlow [E48] → risque de compromission de la frontière de…
  Ajouté : | M057 | A23 — Plugin impressions v3.2.1 — Logiciel | STRIDE-S | Attaquant : attaquant externe [E48] → Spoofing via plugin impressions non audité [E49] → injec…
  Ajouté : | M058 | A24 — PayFlow (API REST + webhooks) — Prestataire | STRIDE-S | Attaquant : attaquant externe [E48] → Spoofing via clés API stockées en clair [E49] → u…
  Ajouté : | M059 | A25 — MailJet (e-mails confirmations/newsletter) — Prestataire | STRIDE-S | Attaquant : attaquant externe [E48] → Spoofing via clé API stockée en clai…
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 03-menaces.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E81], [E67], [E76], [E64], [E84], [E83], [E105], [E65], [E106], [E66], [E61], [E55], [E82], [E59], [E98], [E108], [E80], [E87], [E90], [E68], [E58], [E56], [E60], [E85], [E107]. 03-menaces.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel | STRIDE-T | Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] | | M086 | A33 — Clés API prestataires | STRIDE-E | Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 | STRIDE-E | Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `03-menaces.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M001 | A01 — Site web public (PHP 8, HTML/CSS/JS) | STRIDE-S | Atteinte XSS dans formulaires de recherche/commentaires via injection JavaScript non validée, permettant un attaquant externe d'empiéter sur
  - [non soutenue] | M002 | A01 — Site web public (PHP 8, HTML/CSS/JS) | STRIDE-I | Fuite données clients via logs expose ou erreur tracebacks affichés aux pages d'erreur HTTP 500 contenant noms/adresses/téléphones [E49] | -
  - [non soutenue] | M003 | A01 — Site web public (PHP 8, HTML/CSS/JS) | STRIDE-T | Tampering des pages catalogue via upload de fichiers scripts malveillants dans dossiers uploads non filtrés par extension ou MIME [E49] | - 
  - [non soutenue] | M004 | A02 — API interne (PHP 8) | STRIDE-I | Fuite données sensibles clients/produits à travers les endpoints REST exposés internet sans authentification forte et rate limiting, permettant lecture brute
  - [non soutenue] | M005 | A02 — API internes (PHP 8) | STRIDE-T | Tampering des commandes en base via injection SQLi sur URL parameters non filtrées avant traitement PHP, modifiant prix/quantités livrées au client final [E
  - [non soutenue] | M006 | A02 — API internes (PHP 8) | STRIDE-R | Repudiation via absence de journalisation des appels API et hashages non vérifiés, empêchant traçage des modifications malveillantes commandées par pirates 
  - [non soutenue] | M007 | A03 — Back-office admin (/admin) | STRIDE-S | Spoofing d'administration via brute force sur login sans lockout/brute rate limiting, permettant usurpation compte admin ou préparateurs [E49], [E81] 
  - [non soutenue] | M008 | A03 — Back-office admin (/admin) | STRIDE-T | Tampering des bases de données clients via injection SQLi dans champs recherche/administration templates PHP sans escaping, modifiant commandes/comman
  - [non soutenue] | M009 | A03 — Back-office admin (/admin) | STRIDE-S | Usurpation compte préparateurs par attaquant ayant compromis session admin via XSS persistante sur page d'administration [E49] | - | STRIDE-S |
  - [non soutenue] | M010 | A04 — Base MySQL (shopix) | STRIDE-I | Fuite données brutes clients via dump SQL non chiffré exposé FTP, permettant extraction nom/email/adresse/téléphone/historique commandes [E49], [E67] | - | S

## Contrôle n°7 — Étape 4 · Évaluation, version 1 : NON CONFORME

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 09:46:52
- Ce qui n'allait pas : 04-evaluation.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E81], [E67], [E65], [E83], [E54], [E76], [E84], [E64], [E105], [E66], [E106], [E107], [E108], [E109], [E79], [E80], [E55], [E82], [E58], [E56], [E59], [E98], [E90], [E68], [E85]. 04-evaluation.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → | | M079 | A27 — Comptes préparateurs (EBIOS-RM-A4) Un fournisseur de solution de paiement tiers (E56) est compromis et l'attaquant injecte du | | M086 | A33 — Clés API prestataires (STRIDE-E) Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE-X
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M001 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-S) Atteinte XSS dans formulaires de recherche/commentaires via injection JavaScript non validée, permettant un attaquant externe d'empiéter sur |
  - [non soutenue] | M002 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-I) Fuite données clients via logs expose ou erreur tracebacks affichés aux pages d'erreur HTTP 500 contenant noms/adresses/téléphones [E49] | Moy
  - [non soutenue] | M003 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-T) Tampering des pages catalogue via upload de fichiers scripts malveillants dans dossiers uploads non filtrés par extension ou MIME [E49] | Moye
  - [non soutenue] | M004 | A02 — API interne (PHP 8) (STRIDE-I) Fuite données sensibles clients/produits à travers les endpoints REST exposés internet sans authentification forte et rate limiting, permett | Élevée | Critiqu
  - [non soutenue] | M005 | A02 — API internes (PHP 8) (STRIDE-T) Tampering des commandes en base via injection SQLi sur URL parameters non filtrées avant traitement PHP, modifiant prix/quantités livrées au | Moyenne | Criti
  - [non soutenue] | M008 | A03 — Back-office admin (/admin) (STRIDE-T) Tampering des bases de données clients via injection SQLi dans champs recherche/administration templates PHP sans escaping, modifiant comman | Moyenne |
  - [non soutenue] | M009 | A03 — Back-office admin (/admin) (STRIDE-S) Usurpation compte préparateurs par attaquant ayant compromis session admin via XSS persistante sur page d'administration [E49] | Moyenne | Moyen | Moyen
  - [non soutenue] | M011 | A04 — Base MySQL (shopix) (STRIDE-T) Injection SQLi côté base via connexions non filtrées depuis API interne, modifiant/effaçant clients/commandes/produits [E49] | Élevée | Élevé | Critique | Conn
  - [non soutenue] | M012 | A04 — Base MySQL (shopix) (STRIDE-E) Denial of Service via exhaustion de connexions simultanées non limitées par IP, rendant base inaccessible pour toute l'organisation en pério | Moyenne | Moyen 
  - [non soutenue] | M013 | A05 — Espace fichier (uploads) (STRIDE-T) Tampering du contenu fichiers produits via upload PHP scripts malveillants masqués sous fausses images, exécutant payloads serveur sur chaqu | Élevé | Moy

## Contrôle n°8 — Étape 4 · Évaluation, version 2 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 09:53:27
- Ce qui n'allait pas : 04-evaluation.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E81], [E67], [E65], [E83], [E54], [E76], [E84], [E64], [E105], [E66], [E106], [E98], [E55], [E82], [E56], [E107], [E59], [E68], [E108], [E69], [E72], [E109], [E80], [E90], [E58], [E85]. 04-evaluation.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → | | M086 | A33 — Clés API prestataires (STRIDE-E) Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE-X | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 (STRIDE-E) Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX n
- Ce qui a changé depuis la version précédente :
  30 ligne(s) ajoutée(s), 30 retirée(s).
  Retiré : | M051 | A20 — PHP 8.0 EOL — Logiciel (hôte serveur) (STRIDE-I) Débordement de mémoire via extension non auditée Plugin impressions v3.2.1 ([E9]) → fuite d'inf…
  Retiré : | M052 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-S) Accès distant non authentifiqué aux tables clients/commandes via version MySQL vulnérable ([E4…
  Retiré : | M053 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-T) Altération silencieuse des données produits/commandes via injection SQL ([E49], [E67]) → modif…
  Retiré : | M054 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-I) Fuite des clés d'accès MySQL stockées en clair dans .env hébergeur ([E49]) → compromission du …
  Retiré : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → exploitation CVE-2…
  Ajouté : | M051 | A20 — PHP 8.0 EOL — Logiciel (hôte serveur) (STRIDE-I) Débordement de mémoire via extension non auditée Plugin impressions v3.2.1 ([E9]) → fuite d'inf…
  Ajouté : | M052 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-S) Accès distant non authentifiqué aux tables clients/commandes via version MySQL vulnérable ([E4…
  Ajouté : | M053 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-T) Altération silencieuse des données produits/commandes via injection SQL ([E49], [E67]) → modif…
  Ajouté : | M054 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-I) Fuite des clés d'accès MySQL stockées en clair dans .env hébergeur ([E49]) → compromission du …
  Ajouté : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → exploitation CVE-2…
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 04-evaluation.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E81], [E67], [E65], [E83], [E54], [E76], [E84], [E64], [E105], [E66], [E106], [E98], [E55], [E82], [E56], [E107], [E59], [E68], [E108], [E69], [E72], [E109], [E80], [E90], [E58], [E85]. 04-evaluation.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → | | M086 | A33 — Clés API prestataires (STRIDE-E) Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE-X | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 (STRIDE-E) Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX n
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `04-evaluation.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M001 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-S) Atteinte XSS dans formulaires de recherche/commentaires via injection JavaScript non validée, permettant un attaquant externe d'empiéter sur |
  - [non soutenue] | M002 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-I) Fuite données clients via logs expose ou erreur tracebacks affichés aux pages d'erreur HTTP 500 contenant noms/adresses/téléphones [E49] | Moy
  - [non soutenue] | M003 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-T) Tampering des pages catalogue via upload de fichiers scripts malveillants dans dossiers uploads non filtrés par extension ou MIME [E49] | Moye
  - [non soutenue] | M004 | A02 — API interne (PHP 8) (STRIDE-I) Fuite données sensibles clients/produits à travers les endpoints REST exposés internet sans authentification forte et rate limiting, permett | Élevée | Critiqu
  - [non soutenue] | M005 | A02 — API internes (PHP 8) (STRIDE-T) Tampering des commandes en base via injection SQLi sur URL parameters non filtrées avant traitement PHP, modifiant prix/quantités livrées au | Moyenne | Criti
  - [non soutenue] | M008 | A03 — Back-office admin (/admin) (STRIDE-T) Tampering des bases de données clients via injection SQLi dans champs recherche/administration templates PHP sans escaping, modifiant comman | Moyenne |
  - [non soutenue] | M009 | A03 — Back-office admin (/admin) (STRIDE-S) Usurpation compte préparateurs par attaquant ayant compromis session admin via XSS persistante sur page d'administration [E49] | Moyenne | Moyen | Moyen
  - [non soutenue] | M011 | A04 — Base MySQL (shopix) (STRIDE-T) Injection SQLi côté base via connexions non filtrées depuis API interne, modifiant/effaçant clients/commandes/produits [E49] | Élevée | Élevé | Critique | Conn
  - [non soutenue] | M012 | A04 — Base MySQL (shopix) (STRIDE-E) Denial of Service via exhaustion de connexions simultanées non limitées par IP, rendant base inaccessible pour toute l'organisation en pério | Moyenne | Moyen 
  - [non soutenue] | M013 | A05 — Espace fichier (uploads) (STRIDE-T) Tampering du contenu fichiers produits via upload PHP scripts malveillants masqués sous fausses images, exécutant payloads serveur sur chaqu | Élevé | Moy

## Contrôle n°9 — Étape 5 · Traitement, version 1 : NON CONFORME

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 10:11:31
- Ce qui n'allait pas : 05-traitement.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E65], [E54], [E76], [E84], [E64], [E83], [E105], [E67], [E66], [E106], [E81], [E55], [E82], [E59], [E98], [E108], [E80], [E90], [E68], [E58], [E56], [E85], [E107]. 05-traitement.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → | | M086 | A33 — Clés API prestataires (STRIDE-E) Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE-X | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 (STRIDE-E) Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX n
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M002 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-I) Fuite données clients via logs expose ou erreur tracebacks affichés aux pages d'erreur HTTP 500 contenant noms/adresses/téléphones [E49] nivea
  - [non soutenue] | M003 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-T) Tampering des pages catalogue via upload de fichiers scripts malveillants dans dossiers uploads non filtrés par extension ou MIME [E49] niveau
  - [non soutenue] | M009 | A03 — Back-office admin (/admin) (STRIDE-S) Usurpation compte préparateurs par attaquant ayant compromis session admin via XSS persistante sur page d'administration [E49] niveau Moyen | Réduire | 
  - [non soutenue] | M011 | A04 — Base MySQL (shopix) (STRIDE-T) Injection SQLi côté base via connexions non filtrées depuis API interne, modifiant/effaçant clients/commandes/produits [E49] niveau Critique | Réduire | MFA FI
  - [non soutenue] | M012 | A04 — Base MySQL (shopix) (STRIDE-E) Denial of Service via exhaustion de connexions simultanées non limitées par IP, rendant base inaccessible pour toute l'organisation en pério niveau Moyen | Réd
  - [non soutenue] | M013 | A05 — Espace fichier (uploads) (STRIDE-T) Tampering du contenu fichiers produits via upload PHP scripts malveillants masqués sous fausses images, exécutant payloads serveur sur chaqu niveau Élevé 
  - [non soutenue] | M014 | A05 — Espace fichier (uploads) (STRIDE-I) Fuite données clients via CSV exports stockés 24 mois sans chiffrement FTP, contenant full noms/adresses/téléphones/commandes exploitables o niveau Moyen 
  - [non soutenue] | M015 | A05 — Espace fichier (uploads) (STRIDE-S) Spoofing des images catalogue via remplacement fichiers locaux par liens hotlink vers ressources tierces, trompant clients sur contenu réell niveau Faible
  - [non soutenue] | M016 | A06 — Hébergeur mutualisé HostPlanet (STRIDE-S/Spoofing) Attaquant tiers (voisin locataire) usurpe l'identité du site shopix.example via DNS cache poisoning ou compromission de VM co-lodée, rediri
  - [non soutenue] | M017 | A06 — Hébergeur mutualisé HostPlanet (STRIDE-T/Tampering) Attaquant accède à la base MySQL partagée et modifie les commandes en cours, alterne prix/stocks ou injecte des lignes factures fausses av

## Contrôle n°10 — Étape 5 · Traitement, version 2 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-15 10:19:14
- Ce qui n'allait pas : 05-traitement.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E65], [E54], [E76], [E84], [E64], [E83], [E105], [E67], [E66], [E106], [E98], [E81], [E55], [E82], [E59], [E108], [E80], [E90], [E68], [E58], [E56], [E85], [E107]. 05-traitement.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → | | M086 | A33 — Clés API prestataires (STRIDE-E) Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE-X | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 (STRIDE-E) Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX n
- Ce qui a changé depuis la version précédente :
  30 ligne(s) ajoutée(s), 30 retirée(s).
  Retiré : | M051 | A20 — PHP 8.0 EOL — Logiciel (hôte serveur) (STRIDE-I) Débordement de mémoire via extension non auditée Plugin impressions v3.2.1 ([E9]) → fuite d'inf…
  Retiré : | M052 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-S) Accès distant non authentifiqué aux tables clients/commandes via version MySQL vulnérable ([E4…
  Retiré : | M053 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-T) Altération silencieuse des données produits/commandes via injection SQL ([E49], [E67]) → modif…
  Retiré : | M054 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-I) Fuite des clés d'accès MySQL stockées en clair dans .env hébergeur ([E49]) → compromission du …
  Retiré : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → exploitation CVE-2…
  Ajouté : | M051 | A20 — PHP 8.0 EOL — Logiciel (hôte serveur) (STRIDE-I) Débordement de mémoire via extension non auditée Plugin impressions v3.2.1 ([E9]) → fuite d'inf…
  Ajouté : | M052 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-S) Accès distant non authentifiqué aux tables clients/commandes via version MySQL vulnérable ([E4…
  Ajouté : | M053 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-T) Altération silencieuse des données produits/commandes via injection SQL ([E49], [E67]) → modif…
  Ajouté : | M054 | A21 — MySQL 5.7 — Logiciel (base de données) (STRIDE-I) Fuite des clés d'accès MySQL stockées en clair dans .env hébergeur ([E49]) → compromission du …
  Ajouté : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → exploitation CVE-2…
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 05-traitement.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E65], [E54], [E76], [E84], [E64], [E83], [E105], [E67], [E66], [E106], [E98], [E81], [E55], [E82], [E59], [E108], [E80], [E90], [E68], [E58], [E56], [E85], [E107]. 05-traitement.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M055 | A22 — PayFlow-SDK v2.1 — Logiciel (STRIDE-T) Attaquant : cybercriminel [E48] → Tampering via buffer overflow dans gestion t [E49] → | | M086 | A33 — Clés API prestataires (STRIDE-E) Attaquant : fournisseur malveillant [E43] → Environment Modification via vulnérabilité CVE-X | | M091 | A36 — SDK paiement PayFlow-SDK v2.1 (STRIDE-E) Attaquant : exploitant [E36] → Environment Modification via vulnérabilité CVE-XXXX n
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `05-traitement.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M002 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-I) Fuite données clients via logs expose ou erreur tracebacks affichés aux pages d'erreur HTTP 500 contenant noms/adresses/téléphones [E49] nivea
  - [non soutenue] | M003 | A01 — Site web public (PHP 8, HTML/CSS/JS) (STRIDE-T) Tampering des pages catalogue via upload de fichiers scripts malveillants dans dossiers uploads non filtrés par extension ou MIME [E49] niveau
  - [non soutenue] | M009 | A03 — Back-office admin (/admin) (STRIDE-S) Usurpation compte préparateurs par attaquant ayant compromis session admin via XSS persistante sur page d'administration [E49] niveau Moyen | Réduire | 
  - [non soutenue] | M011 | A04 — Base MySQL (shopix) (STRIDE-T) Injection SQLi côté base via connexions non filtrées depuis API interne, modifiant/effaçant clients/commandes/produits [E49] niveau Critique | Réduire | MFA FI
  - [non soutenue] | M012 | A04 — Base MySQL (shopix) (STRIDE-E) Denial of Service via exhaustion de connexions simultanées non limitées par IP, rendant base inaccessible pour toute l'organisation en pério niveau Moyen | Réd
  - [non soutenue] | M013 | A05 — Espace fichier (uploads) (STRIDE-T) Tampering du contenu fichiers produits via upload PHP scripts malveillants masqués sous fausses images, exécutant payloads serveur sur chaqu niveau Élevé 
  - [non soutenue] | M014 | A05 — Espace fichier (uploads) (STRIDE-I) Fuite données clients via CSV exports stockés 24 mois sans chiffrement FTP, contenant full noms/adresses/téléphones/commandes exploitables o niveau Moyen 
  - [non soutenue] | M015 | A05 — Espace fichier (uploads) (STRIDE-S) Spoofing des images catalogue via remplacement fichiers locaux par liens hotlink vers ressources tierces, trompant clients sur contenu réell niveau Faible
  - [non soutenue] | M016 | A06 — Hébergeur mutualisé HostPlanet (STRIDE-S/Spoofing) Attaquant tiers (voisin locataire) usurpe l'identité du site shopix.example via DNS cache poisoning ou compromission de VM co-lodée, rediri
  - [non soutenue] | M017 | A06 — Hébergeur mutualisé HostPlanet (STRIDE-T/Tampering) Attaquant accède à la base MySQL partagée et modifie les commandes en cours, alterne prix/stocks ou injecte des lignes factures fausses av

## Contrôle n°11 — Étape 6 · Registre à valider, version 1 : CONFORME

- Contrôleur : contrôle par le programme (reprise ligne à ligne des étapes 3 à 5)  ·  2026-10-15 10:19:14
- Ce qui n'allait pas : rien à signaler
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.

## Contrôle n°12 — Étape 7 · Synthèse, version 1 : CONFORME

- Contrôleur : contrôle par le programme (reprise ligne à ligne des étapes 3 à 5)  ·  2026-10-15 10:20:49
- Ce qui n'allait pas : rien à signaler
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.

## Contrôle n°13 — Relecture finale, version 1 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : ollama/gemma4:12b  ·  2026-10-15 10:21:01
- Ce qui n'allait pas : - "A28 — Compte client optionnel" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A27 — Comptes préparateurs" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A17 — Clients (nom, email, adresse, téléphone)" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A19 — Admin (comptes, exports csv)" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A08 — MailJet e-mails" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A18 — Bancaires carte/tokenisation PayFlow" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A20 — PHP 8.0 EOL — Logiciel (hôte serveur)" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A30 — Site web public / API interne" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants.
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : - "A28 — Compte client optionnel" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A27 — Comptes préparateurs" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A17 — Clients (nom, email, adresse, téléphone)" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A19 — Admin (comptes, exports csv)" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A08 — MailJet e-mails" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A18 — Bancaires carte/tokenisation PayFlow" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A20 — PHP 8.0 EOL — Logiciel (hôte serveur)" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants. - "A30 — Site web public / API interne" (SYNTHESE.md, section 3) : cet actif n'apparaît pas dans les intrants.
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `registre-risques.md`, `SYNTHESE.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
