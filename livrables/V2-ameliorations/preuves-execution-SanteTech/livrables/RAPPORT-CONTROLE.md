# Rapport de contrôle

Un contrôle indépendant relit chaque étape avant la suivante. Pour chacun : ce qui n'allait pas, ce qui a changé depuis la version précédente, et le verdict.

## À faire valider par un humain

- **Étape 1 · Existant et actifs** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 00-description.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E10], [E19], [E3], [E7], [E44], [E36], [E17], [E9], [E18], [E5], [E2], [E45], [E8], [E6], [E15], [E38], [E16], [E1], [E25]. 00-description.md : trop de lignes sans preuve citée (12 sur 39) : cite [E…] après chaque fait, ou retire la ligne si le dossier de preuves ne la soutient pas. 01-actifs.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E5], [E7], [E9], [E11], [E13].
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `00-description.md`, `01-actifs.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Étape 2 · Choix de la méthode** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 02-methodes.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E5], [E9], [E38], [E40], [E7].
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `02-methodes.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Étape 3 · Menaces** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 03-menaces.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E38], [E9], [E2], [E40], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (03-menaces.md); A5 (03-menaces.md); A7 (03-menaces.md). 03-menaces.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M069 | A21 — Infrastructure Cloud — Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] 
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `03-menaces.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Étape 4 · Évaluation** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 04-evaluation.md : termes absents des intrants à retirer, ou à présenter explicitement comme une hypothèse à confirmer : jwt. Ne les mentionne pas du tout, pas même pour dire qu'ils sont absents. 04-evaluation.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E38], [E24], [E240], [E2], [E9], [E40], [E30], [E4], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (04-evaluation.md); A5 (04-evaluation.md); A7 (04-evaluation.md); R2 (04-evaluation.md). 04-evaluation.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M067 | A21 — Infrastructure Cloud — Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] 
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `04-evaluation.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Étape 5 · Traitement** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 05-traitement.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E24], [E240], [E2], [E38], [E9], [E12], [E13], [E40], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (05-traitement.md); A7 (05-traitement.md).
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `05-traitement.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- **Relecture finale** — Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : - "Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11" (A10) - "Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146]" (A24) - "Hébergé sur ferme Citrix/RDS (Siège Rennes) [E139]" (A25) - "Dossier Patient Informatisé (DPI) Nexus" (A01) - "Messagerie Sécurisée de Santé (Mél)" (A03) - "Portail VPN Télétravail & Praticiens Libéraux" (A04) - "Application métier — DPI Progiciel Nexus" (A18) - "Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142]" (A21)
  - À vérifier : Pour chaque point signalé, chercher l'affirmation dans `registre-risques.md`, `SYNTHESE.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.

## Contrôle n°1 — Étape 1 · Existant et actifs, version 1 : NON CONFORME

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-12 13:50:29
- Ce qui n'allait pas : 00-description.md : termes absents des intrants à retirer, ou à présenter explicitement comme une hypothèse à confirmer : gcp. Ne les mentionne pas du tout, pas même pour dire qu'ils sont absents. 00-description.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E4], [E11], [E8], [E10], [E25], [E6], [E16], [E20], [E5], [E9], [E7], [E3], [E27], [E31], [E28], [E26], [E37], [E43]. 00-description.md : trop de lignes sans preuve citée (22 sur 57) : cite [E…] après chaque fait, ou retire la ligne si le dossier de preuves ne la soutient pas. 01-actifs.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E5], [E7], [E9], [E11], [E13].
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | A01 | Dossier Patient Informatisé (DPI) Nexus | Logiciel / Service | 185 serveurs (65 physiques, 120 virtuels), Progiciel Nexus version legacy sur ferme Citrix/RDS, accès soignants RDP interne, valeur mé
  - [non soutenue] | A02 | PACS/RIS (Archivage & Imagerie) | Logiciel / Service | Stockage DICOM/SMBv1 sur baies SAN locales vieillissantes, caches DICOM/PACS restants en local des cliniques, protocoles SMBv1 pour compatibil
  - [non soutenue] | A03 | Messagerie Sécurisée de Santé (Mél) | Logiciel / Service | Serveur Exchange 2016 exposé DMZ, Webmail OWA webmail.santetech-sante.fr, vulnérable ProxyShell/Spraying si non patché [E7][E5] | Sensible
  - [non soutenue] | A04 | Portail VPN Télétravail & Praticiens Libéraux | Service / Site Internet | vpn.santetech-sante.fr (Passerelle FortiGate/FortiSSL), Login/Mot de passe AD sans MFA sur 60% des comptes, authentificatio
  - [non soutenue] | A05 | Webmail de Santé & Accès Externe (OWA) | Service / Site Internet | webmail.santetech-sante.fr (Exchange 2016 DMZ), non filtré SSL si vulnérabilités, campagnes Spraying/ProxyShell potentielles [E7][
  - [non soutenue] | A06 | Extranet Partenaires / Médecins Libéraux | Service / Site Internet | extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants extérie
  - [non soutenue] | A07 | Sites Web Cliniques (12 sites) | Site Internet / Prestataire | Hébergés prestataire tiers WordPress non durci, sans liaison SI interne mais cibles défacement/phishing rebond [E7][E5] | Publique | [
  - [non soutenue] | A08 | Domaine Active Directory (corp.santetech.local) | Logiciel / Infrastructure | Forêt AD unique, 16 contrôleurs de domaine (1 DC/RODC par clinique), pas de MFA systématique VPN As-Is [E9][E7][E5] | S
  - [non soutenue] | A09 | Contrôleurs de Domaine AD (16 unités) | Matériel / Infrastructure | 1 DC complet + 1 RODC par clinique (12 sites), gestion identités centralisée, patching potentiellement hétérogène [E9][E5] | Crit
  - [non soutenue] | A10 | Applications Cloud Hybride (To-Be) | Logiciel / Service | Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique [E9][E5][E11] | Sensibl

## Contrôle n°2 — Étape 1 · Existant et actifs, version 2 : NON CONFORME

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-12 13:52:27
- Ce qui n'allait pas : 00-description.md : termes absents des intrants à retirer, ou à présenter explicitement comme une hypothèse à confirmer : gcp. Ne les mentionne pas du tout, pas même pour dire qu'ils sont absents. 00-description.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E4], [E11], [E8], [E10], [E25], [E6], [E16], [E20], [E5], [E9], [E7], [E3], [E27], [E31], [E28], [E26], [E37], [E43]. 00-description.md : trop de lignes sans preuve citée (22 sur 57) : cite [E…] après chaque fait, ou retire la ligne si le dossier de preuves ne la soutient pas. 01-actifs.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E5], [E7], [E9], [E11], [E13]. 00-description.md : texte d'attente à remplacer par l'information ou par « non documenté » : | **RTO/RPO vitaux** | Seuils de RTO (Recovery Time Objective) et RPO (Recovery Point Objective) pour services santé critiques DPI/PACS IoT 
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | A01 | Dossier Patient Informatisé (DPI) Nexus | Logiciel / Service | 185 serveurs (65 physiques, 120 virtuels), Progiciel Nexus version legacy sur ferme Citrix/RDS, accès soignants RDP interne, valeur mé
  - [non soutenue] | A02 | PACS/RIS (Archivage & Imagerie) | Logiciel / Service | Stockage DICOM/SMBv1 sur baies SAN locales vieillissantes, caches DICOM/PACS restants en local des cliniques, protocoles SMBv1 pour compatibil
  - [non soutenue] | A03 | Messagerie Sécurisée de Santé (Mél) | Logiciel / Service | Serveur Exchange 2016 exposé DMZ, Webmail OWA webmail.santetech-sante.fr, vulnérable ProxyShell/Spraying si non patché [E7][E5] | Sensible
  - [non soutenue] | A04 | Portail VPN Télétravail & Praticiens Libéraux | Service / Site Internet | vpn.santetech-sante.fr (Passerelle FortiGate/FortiSSL), Login/Mot de passe AD sans MFA sur 60% des comptes, authentificatio
  - [non soutenue] | A05 | Webmail de Santé & Accès Externe (OWA) | Service / Site Internet | webmail.santetech-sante.fr (Exchange 2016 DMZ), non filtré SSL si vulnérabilités, campagnes Spraying/ProxyShell potentielles [E7][
  - [non soutenue] | A06 | Extranet Partenaires / Médecins Libéraux | Service / Site Internet | extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants extérie
  - [non soutenue] | A07 | Sites Web Cliniques (12 sites) | Site Internet / Prestataire | Hébergés prestataire tiers WordPress non durci, sans liaison SI interne mais cibles défacement/phishing rebond [E7][E5] | Publique | [
  - [non soutenue] | A08 | Domaine Active Directory (corp.santetech.local) | Logiciel / Infrastructure | Forêt AD unique, 16 contrôleurs de domaine (1 DC/RODC par clinique), pas de MFA systématique VPN As-Is [E9][E7][E5] | S
  - [non soutenue] | A09 | Contrôleurs de Domaine AD (16 unités) | Matériel / Infrastructure | 1 DC complet + 1 RODC par clinique (12 sites), gestion identités centralisée, patching potentiellement hétérogène [E9][E5] | Crit
  - [non soutenue] | A10 | Applications Cloud Hybride (To-Be) | Logiciel / Service | Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique [E9][E5][E11] | Sensibl

## Contrôle n°3 — Étape 1 · Existant et actifs, version 3 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-12 14:00:39
- Ce qui n'allait pas : 00-description.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E10], [E19], [E3], [E7], [E44], [E36], [E17], [E9], [E18], [E5], [E2], [E45], [E8], [E6], [E15], [E38], [E16], [E1], [E25]. 00-description.md : trop de lignes sans preuve citée (12 sur 39) : cite [E…] après chaque fait, ou retire la ligne si le dossier de preuves ne la soutient pas. 01-actifs.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E5], [E7], [E9], [E11], [E13].
- Ce qui a changé depuis la version précédente :
  119 ligne(s) ajoutée(s), 142 retirée(s).
  Retiré : # 00-description.md — Étape 1 : Description du cas étudié
  Retiré : ## Dossier de preuves
  Retiré : Ce dossier REMPLACE la lecture des documents d'origine : ne relis pas d'autre fichier. Il reproduit le TEXTE des documents (sections et tableaux, avec leur en-…
  Retiré : > Ce fichier décrit le système d'information du groupe **SanteTech**, conformément aux exigences de l'ANSSI (`Cartographie du système d'information — Guide d'é…
  Retiré : ## 1. Cas étudié
  Ajouté : # Analyse E21 — Étape 1 : Description du cas & Cartographie du système (ANSSI-CARTO-SI)
  Ajouté : ## 📄 1. Résumé de la fiche (cas étudié)
  Ajouté : **Cas SanteTech : Étude de Sécurité — Projet SECU‑CLOUD‑HEALTH (M2 Cybersécurité, bloc 1)**
  Ajouté : Ce document résume l'architecture **AS-IS** du groupe hospitalier **SanteTech**, les périmètres, les contraintes réglementaires et techniques, ainsi que les hy…
  Ajouté : | Éléments | Valeurs validées |
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 00-description.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E10], [E19], [E3], [E7], [E44], [E36], [E17], [E9], [E18], [E5], [E2], [E45], [E8], [E6], [E15], [E38], [E16], [E1], [E25]. 00-description.md : trop de lignes sans preuve citée (12 sur 39) : cite [E…] après chaque fait, ou retire la ligne si le dossier de preuves ne la soutient pas. 01-actifs.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E5], [E7], [E9], [E11], [E13].
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `00-description.md`, `01-actifs.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | **Périmètre physique** | Siège social (Rennes) + 12 cliniques régionales (Grand Ouest & Île-de-France) [E10][E224] |
  - [non soutenue] | **Dossiers patients actifs** | 150 000 dossiers dans le DPI Nexus legacy [E19][E223] |
  - [non soutenue] | **Serveurs & applications** | 185 serveurs (65 physiques, 120 virtuels) ; 3 200 postes + ~4 000 dispositifs IoT médicaux [E147][E3][E230] |
  - [non soutenue] | **Objectif de la mission** | Concevoir une architecture sécurisée (To‑Be) : cloud hybride HDS, microservices, zero trust et API Gateway. Tester la résilience contre ransomwares/fuites [E224] |
  - [non soutenue] | **DMZ / VPN Gateway** | Point d'entrée principal (vpn.santetech-sante.fr) + OWA. Authentification simple → risque accès non filtré [E7][E203] | FortiGate + login/mot de passe sans MFA sur 60% des comptes
  - [non soutenue] | **Réseau interne (Hub & Spoke)** | Backbone MPLS centralisé par le siège. Routage direct entre clinique et siège. Micro‑segmentation absente : un poste compromis peut tout atteindre [E36][E203] | Interne
  - [non soutenue] | **MFA systématique** | Déploiement cible Entra ID / Keycloak avec MFA FIDO2 / Carte CPS pour les soignants [E45]. | As‑Is : pas de MFA sur le VPN → 60% des comptes sans MFA, simple login/mot de passe [E7
  - [non soutenue] | **VLAN IoT vs VLAN Wi‑Fi** | Isolation logique stricte (micro‑segmentation) pour la cible To‑Be. Actuellement : routage direct entre automate et cœur réseau, VLAN IoT non cloisonné [E15]. | Écart documen
  - [non soutenue] | **SOC / EDR / SIEM** | Absence initiale des 3 briques SOC centralisé. Projet doit répondre aux exigences NIS 2/RGPD/HDS. | Aucun SOC/EDR/SIEM déployé en As‑Is ; Blue Team & SOC non implémentée [E140][E38
  - [non soutenue] | **Postes irréductibles (Windows 7/XP Embedded)** | ~5% du parc (~200 postes) ne peuvent être patchés ou upgradées. Utilisés pour l'imagerie médicale et automates vieux scanners. | Pas de plan de remplace

## Contrôle n°4 — Étape 2 · Choix de la méthode, version 1 : NON CONFORME

- Contrôleur : ollama/gemma4:12b  ·  2026-10-12 14:11:16
- Ce qui n'allait pas : MAL LU : STRIDE permet de valider les frontières de confiance [E146] — Fiche_d_Audit_Technique_-_État_des_Lieux_SanteTech__As-Is_.pdf : Le document mentionne une "Interconnexion MPLS centralisée" et précise "Aucune isolation inter-sites", ce qui contredit l'idée de frontières de confiance actuelles. MAL LU : LINDDUN analyse la confidentialité [E149] — FAQ___Complément_de_Cadrage_-_SanteTech__Bloc_1_.pdf : Le document mentionne le RGPD mais ne définit pas LINDDUN comme l'outil d'analyse de la confidentialité. INVENTÉ : STRIDE : python3 -m tools.methodes.stride.check_dfd ... — Aucun document ne mentionne ces commandes ou outils spécifiques. INVENTÉ : LINDDUN : python3 -m tools.methodes.linddun ... — Aucun document ne mentionne ces commandes ou outils spécifiques. INVENTÉ : EBIOS RM : python3 -m tools.methodes.ebios ... — Aucun document ne mentionne ces commandes ou outils spécifiques. MAL LU : EBIOS RM étend l'analyse au-delà du DFD [E140] — Fiche_d_Audit_Technique_-_État_des_Lieux_SanteTech__As-Is_.pdf : Le document ne mentionne pas EBIOS RM ni l'extension au-delà du DFD. OMIS : Le document FAQ mentionne 150 000 dossiers patients, mais le livrable ne mentionne pas cette volumétrie dans la justification du choix des méthodes. OMIS : Le document Fiche_d_Audit mentionne 4 500 collaborateurs, mais cette donnée est absente du livrable. OMIS : Le document Fiche_d_Audit mentionne 3 200 postes de travail, mais cette donnée est absente du livrable. OMIS : Le document FAQ mentionne un budget Build de 1,5 million d'euros, mais cette donnée est absente du livrable. OMIS : Le document FAQ mentionne un budget Run de 300 k€/an, mais cette donnée est absente du livrable. OMIS : Le document Fiche_d_Audit mentionne l'utilisation de protocoles SMBv1, mais cette donnée est absente du livrable.
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | **STRIDE** | DFD | Bas | Applications web | Données critiques, migration cloud, RGPD (menaces de type *Disclosure of personal data*) [E149][E203] |
  - [non soutenue] | **LINDDUN** | Données personnelles | Moyen | RGPD | Circulation de données sensibles (p. ex. dossiers patients) [E149][E203] |
  - [non soutenue] | **EBIOS RM** | Organisation | Elevé | Administrations/OIV | Conformité NIS 2, audit HDS, analyse stratégique [E140][E205] |
  - [non soutenue] | **PASTA** | Objectifs métier | Moyen | Impact business | Justification économique des mesures de sécurité [E142][E150] |
  - [non soutenue] - **STRIDE + LINDDUN** : Le projet manipule des données patients critiques [A19] et migre vers un cloud hybride [A10], nécessitant une analyse technique des menaces via STRIDE (DFD [E146]) et une spécialis
  - [non soutenue] - **EBIOS RM** (atelier A3/A4) : L'analyse doit couvrir l'écosystème (fournisseurs Cloud HDS [A11], micro-segmentation [A13]) comme vecteur d'attaque [E140]. EBIOS RM étend l'analyse au-delà du DFD [E140],

## Contrôle n°5 — Étape 2 · Choix de la méthode, version 2 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-12 14:14:15
- Ce qui n'allait pas : 02-methodes.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E5], [E9], [E38], [E40], [E7].
- Ce qui a changé depuis la version précédente :
  51 ligne(s) ajoutée(s), 21 retirée(s).
  Retiré : # Dossier de preuves — étape 2
  Retiré : > Ce dossier REMPLACE la lecture des documents d'origine : ne relis pas d'autre fichier. Il reproduit le TEXTE des documents (sections et tableaux, avec leur e…
  Retiré : | Méthode | Point de départ | Effort | Idéal pour | Quand choisir |
  Retiré : | **STRIDE** | DFD | Bas | Applications web | Données critiques, migration cloud, RGPD (menaces de type *Disclosure of personal data*) [E149][E203] |
  Retiré : | **LINDDUN** | Données personnelles | Moyen | RGPD | Circulation de données sensibles (p. ex. dossiers patients) [E149][E203] |
  Ajouté : # Choix de méthode — Analyse des risques SanteTech
  Ajouté : Le projet « SanteTech » vise la sécurisation d'un SI hospitalier hérité (legacy) migrant vers un cloud hybride, avec 150 000 dossierspatients actifs [E223], 4 …
  Ajouté : | Méthode | Point de départ | Effort* | Idéal pour | Quand choisir |
  Ajouté : | **STRIDE** | DFD / Frontières de confiance | Bas | Applications web, systèmes distribués [E146] | Données critiques (dossiers patients), migration cloud hybr…
  Ajouté : | **LINDDUN** | Données personnelles / RGPD | Moyen | Confidentialité, vie privée [E149] | Circulation de données sensibles (dossiers patients 150 k+) ; spécia…
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 02-methodes.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E5], [E9], [E38], [E40], [E7].
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `02-methodes.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] Le projet « SanteTech » vise la sécurisation d'un SI hospitalier hérité (legacy) migrant vers un cloud hybride, avec 150 000 dossierspatients actifs [E223], 4 500 collaborateurs et une flotte de ~3 200 pos
  - [non soutenue] | **STRIDE** | DFD / Frontières de confiance | Bas | Applications web, systèmes distribués [E146] | Données critiques (dossiers patients), migration cloud hybride, API Gateway télémédecine [E231], menaces 
  - [non soutenue] | **LINDDUN** | Données personnelles / RGPD | Moyen | Confidentialité, vie privée [E149] | Circulation de données sensibles (dossiers patients 150 k+) ; spécialise l'analyse sur *D*isclosure of personal da
  - [non soutenue] | **PASTA** | Objectifs métier | Moyen | Impact économique business [E207] | Justification des investissements de sécurité (ROI), alignement avec la stratégie COMEX ; utilisé en complément pour prioriser l
  - [non soutenue] | **DREAD / CVSS** | Priorisation | Variable | Scoring menaces/vulnérabilités [E150] | Vulnérabilités connues (ProxyShell, SMBv1) ; DREAD subjectif pour triage rapide, CVSS v4.0 objectif pour rapport à la 
  - [non soutenue] - **Justification de l'association** : STRIDE valide la sécurité technique des frontières (A17, A22), tandis que LINDDUN spécialise l'analyse sur les menaces RGPD/Dataprivacy ; sans LINDDUN, les menaces de
  - [non soutenue] L'écosystème externe (fournisseurs Cloud HDS, prestataires IT) représente un vecteur d'attaque majeur [E140][A11].
  - [non soutenue] - EBIOS RM peut étendre l'analyse au-delà du DFD en traitant les risques liés aux sous-traitants et hébergeurs tiers (A11). Cependant, aucun des documents ne mentionne une extension explicite « au-delà du 
  - [non soutenue] - **Justification retenue** : Le choix de l'appliquer reste optionnel pour élargir la couverture aux risques organisationnels (gestion des prestataires Cloud, sous-traitance SaaS), surtout si la direction 
  - [non soutenue] - **LINDDUN** : KU Leuven (RGPD, vie privée/ confidentialité) — grille DPF incluse dans les livrables LINDDUN [E149]

## Contrôle n°6 — Étape 3 · Menaces, version 1 : NON CONFORME

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-12 14:29:52
- Ce qui n'allait pas : 03-menaces.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E38], [E40], [E9], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E2], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A5 (03-menaces.md); A7 (03-menaces.md); R2 (03-menaces.md). 03-menaces.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M021 | A07 - Sites Web Cliniques (12 sites) — Site Internet / Prestataire — Hébergés prestataire tiers WordPress non durci, sans liaison S | | M025 | A07 - Sites Web Cliniques (12 sites) — Site Internet / Prestataire — Hébergés prestataire tiers WordPress non durci, sans liaison S | | M032 | A09 - Contrôleurs de Domaine AD (16 unités) — Matériel / Infrastructure — 1 DC complet + 1 RODC par clinique (12 sites), gestion id
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M001 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | STRIDE-T | Attentat cyber : accès aux dossiers patients via exploitation des vulnérabilités legacy sur Citrix/RDS avec RDP non 
  - [non soutenue] | M002 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | LINDDUN-Disclosure | Fuite de données patients : progression horizontale (MOVElaterally) depuis les 185 serveurs legacy vers au
  - [non soutenue] | M003 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | STRIDE-I | Injection malveillante : modification des dossiers patients pendant la migration legacy-to-cloud via API Gateway non
  - [non soutenue] | M004 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | STRIDE-S | Substitution d'imagerie : injection de fichiers DICOM malformés ou corrompus via SMBv1 non patché dans les baies SAN locales
  - [non soutenue] | M005 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | STRIDE-R | Ransomware : chiffrement des images DICOM stockées sur baies SAN sans EDR, exploitant les failles de partage SMB [E203][EBIO
  - [non soutenue] | M006 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | LINDDUN-Disclosure | Accès non autorisé aux images médicales : compromission d'un cache local en clinique via VLAN IoT non cloisonné (1
  - [non soutenue] | M012 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet | STRIDE-R | Ransomware sur accès distant : compromission du FortiGate via failles de certificats TLS non renouvelés, 
  - [non soutenue] | M016 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | STRIDE-D | Destruction d'images DICOM : corruption des baies SAN locales via malware SMB qui supprime les données critiques [E203][EBIO
  - [non soutenue] | M017 | A06 - Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants 
  - [non soutenue] | M018 | A06 - Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants 

## Contrôle n°7 — Étape 3 · Menaces, version 2 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-12 14:33:41
- Ce qui n'allait pas : 03-menaces.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E38], [E9], [E2], [E40], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (03-menaces.md); A5 (03-menaces.md); A7 (03-menaces.md). 03-menaces.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M069 | A21 — Infrastructure Cloud — Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] 
- Ce qui a changé depuis la version précédente :
  119 ligne(s) ajoutée(s), 118 retirée(s).
  Retiré : | M017 | A06 - Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification pa…
  Retiré : | M018 | A06 - Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification pa…
  Retiré : | M019 | A06 - Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification pa…
  Retiré : | M020 | A06 - Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification pa…
  Retiré : | M021 | A07 - Sites Web Cliniques (12 sites) — Site Internet / Prestataire — Hébergés prestataire tiers WordPress non durci, sans liaison SI interne mais cibl…
  Ajouté : | M017 | A06 — Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification pa…
  Ajouté : | M018 | A06 — Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification pa…
  Ajouté : | M019 | A06 — Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification pa…
  Ajouté : | M020 | A06 — Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification pa…
  Ajouté : | M021 | A07 — Sites Web Cliniques (12 sites) — Site Internet / Prestataire — Hébergés prestataire tiers WordPress non durci, sans liaison SI interne mais cibl…
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 03-menaces.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E38], [E9], [E2], [E40], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (03-menaces.md); A5 (03-menaces.md); A7 (03-menaces.md). 03-menaces.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M069 | A21 — Infrastructure Cloud — Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] 
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `03-menaces.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M001 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | STRIDE-T | Attentat cyber : accès aux dossiers patients via exploitation des vulnérabilités legacy sur Citrix/RDS avec RDP non 
  - [non soutenue] | M002 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | LINDDUN-Disclosure | Fuite de données patients : progression horizontale (MOVElaterally) depuis les 185 serveurs legacy vers au
  - [non soutenue] | M003 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | STRIDE-I | Injection malveillante : modification des dossiers patients pendant la migration legacy-to-cloud via API Gateway non
  - [non soutenue] | M004 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | STRIDE-S | Substitution d'imagerie : injection de fichiers DICOM malformés ou corrompus via SMBv1 non patché dans les baies SAN locales
  - [non soutenue] | M005 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | STRIDE-R | Ransomware : chiffrement des images DICOM stockées sur baies SAN sans EDR, exploitant les failles de partage SMB [E203][EBIO
  - [non soutenue] | M006 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | LINDDUN-Disclosure | Accès non autorisé aux images médicales : compromission d'un cache local en clinique via VLAN IoT non cloisonné (1
  - [non soutenue] | M012 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet | STRIDE-R | Ransomware sur accès distant : compromission du FortiGate via failles de certificats TLS non renouvelés, 
  - [non soutenue] | M016 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | STRIDE-D | Destruction d'images DICOM : corruption des baies SAN locales via malware SMB qui supprime les données critiques [E203][EBIO
  - [non soutenue] | M017 | A06 — Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants 
  - [non soutenue] | M018 | A06 — Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants 

## Contrôle n°8 — Étape 4 · Évaluation, version 1 : NON CONFORME

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-12 14:51:27
- Ce qui n'allait pas : 04-evaluation.md : termes absents des intrants à retirer, ou à présenter explicitement comme une hypothèse à confirmer : jwt. Ne les mentionne pas du tout, pas même pour dire qu'ils sont absents. 04-evaluation.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E38], [E24], [E240], [E2], [E9], [E40], [E30], [E4], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (04-evaluation.md); A5 (04-evaluation.md); A7 (04-evaluation.md); R2 (04-evaluation.md). 04-evaluation.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M069 | A21 — Infrastructure Cloud — Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] 
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M001 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service (STRIDE-T) Attentat cyber : accès aux dossiers patients via exploitation des vulnérabilités legacy sur Citrix/RDS avec RDP non fi
  - [non soutenue] | M002 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service (LINDDUN-Disclosure) Fuite de données patients : progression horizontale (MOVElaterally) depuis les 185 serveurs legacy vers autr
  - [non soutenue] | M003 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service (STRIDE-I) Injection malveillante : modification des dossiers patients pendant la migration legacy-to-cloud via API Gateway non s
  - [non soutenue] | M004 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service (STRIDE-S) Substitution d'imagerie : injection de fichiers DICOM malformés ou corrompus via SMBv1 non patché dans les baies SAN locales v
  - [non soutenue] | M005 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service (STRIDE-R) Ransomware : chiffrement des images DICOM stockées sur baies SAN sans EDR, exploitant les failles de partage SMB [E203][EBIOS-
  - [non soutenue] | M008 | A03 — Messagerie Sécurisée de Santé (Mél) — Logiciel / Service (LINDDUN-Disclosure) Fuite d'emails sensibles : exfiltration via OWA vulnérable et absence de filtrage SSL sur webmail.santetech-sant
  - [non soutenue] | M010 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet (STRIDE-I) Injection de session : authentification compromise par absence de MFA sur 60% des comptes AD, permettant pr
  - [non soutenue] | M012 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet (STRIDE-R) Ransomware sur accès distant : compromission du FortiGate via failles de certificats TLS non renouvelés, ex
  - [non soutenue] | M013 | A05 — Webmail de Santé & Accès Externe (OWA) — Service / Site Internet (STRIDE-E) Escalade de privilèges : exfiltration et modification des données via OWA Exchange 2016 non patché sur DMZ, sans f
  - [non soutenue] | M014 | A05 — Webmail de Santé & Accès Externe (OWA) — Service / Site Internet (LINDDUN-Disclosure) Fuite massive via campagnes Spraying : botnets exploitant Exchange 2016 DMZ pour exfiltrer données patie

## Contrôle n°9 — Étape 4 · Évaluation, version 2 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-12 14:56:38
- Ce qui n'allait pas : 04-evaluation.md : termes absents des intrants à retirer, ou à présenter explicitement comme une hypothèse à confirmer : jwt. Ne les mentionne pas du tout, pas même pour dire qu'ils sont absents. 04-evaluation.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E38], [E24], [E240], [E2], [E9], [E40], [E30], [E4], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (04-evaluation.md); A5 (04-evaluation.md); A7 (04-evaluation.md); R2 (04-evaluation.md). 04-evaluation.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M067 | A21 — Infrastructure Cloud — Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] 
- Ce qui a changé depuis la version précédente :
  12 ligne(s) ajoutée(s), 12 retirée(s).
  Retiré : | M061 | A19 — Donnée/Structure — Données Patients (DPI) (STRIDE-R) Repudiation des accès via logs citrix incomplets sur RDS legacy ne traçant pas les connexio…
  Retiré : | M062 | A19 — Donnée/Structure — Données Patients (DPI) (LINDDUN-D) Disclosure de 150 000 dossiers via API Gateway non sécurisée pour télémédecine (no authz, …
  Retiré : | M063 | A20 — Matériel IoT — Dispositifs Médicaux Connectés (STRIDE-S) Spoofing des commandes médicales via protocole Wi-Fi 6 non crypté (moniteurs, pompes pe…
  Retiré : | M064 | A20 — Matériel IoT — Dispositifs Médicaux Connectés (STRIDE-T) Tamper des paramètres d'automates via micro-noyaux temps réel non patchables permettant…
  Retiré : | M065 | A20 — Matériel IoT — Dispositifs Médicaux Connectés (STRIDE-D) Disclosure de logs médicaux via exploitation Bluetooth LE sur appareils non isolés rése…
  Ajouté : | M061 | A19 — Donnée/Structure — Données Patients (DPI) (STRIDE-R) Repudiation des accès via logs citrix incomplets sur RDS legacy ne traçant pas les connexio…
  Ajouté : | M062 | A19 — Donnée/Structure — Données Patients (DPI) (LINDDUN-D) Disclosure de 150 000 dossiers via API Gateway non sécurisée pour télémédecine (no authz, …
  Ajouté : | M063 | A20 — Matériel IoT — Dispositifs Médicaux Connectés (STRIDE-S) Spoofing des commandes médicales via protocole Wi-Fi 6 non crypté (moniteurs, pompes pe…
  Ajouté : | M064 | A20 — Matériel IoT — Dispositifs Médicaux Connectés (STRIDE-T) Tamper des paramètres d'automates via micro-noyaux temps réel non patchables permettant…
  Ajouté : | M065 | A20 — Matériel IoT — Dispositifs Médicaux Connectés (STRIDE-D) Disclosure de logs médicaux via exploitation Bluetooth LE sur appareils non isolés rése…
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 04-evaluation.md : termes absents des intrants à retirer, ou à présenter explicitement comme une hypothèse à confirmer : jwt. Ne les mentionne pas du tout, pas même pour dire qu'ils sont absents. 04-evaluation.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E38], [E24], [E240], [E2], [E9], [E40], [E30], [E4], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (04-evaluation.md); A5 (04-evaluation.md); A7 (04-evaluation.md); R2 (04-evaluation.md). 04-evaluation.md : texte d'attente à remplacer par l'information ou par « non documenté » : | M067 | A21 — Infrastructure Cloud — Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] 
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `04-evaluation.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M001 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service (STRIDE-T) Attentat cyber : accès aux dossiers patients via exploitation des vulnérabilités legacy sur Citrix/RDS avec RDP non fi
  - [non soutenue] | M002 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service (LINDDUN-Disclosure) Fuite de données patients : progression horizontale (MOVElaterally) depuis les 185 serveurs legacy vers autr
  - [non soutenue] | M003 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service (STRIDE-I) Injection malveillante : modification des dossiers patients pendant la migration legacy-to-cloud via API Gateway non s
  - [non soutenue] | M004 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service (STRIDE-S) Substitution d'imagerie : injection de fichiers DICOM malformés ou corrompus via SMBv1 non patché dans les baies SAN locales v
  - [non soutenue] | M005 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service (STRIDE-R) Ransomware : chiffrement des images DICOM stockées sur baies SAN sans EDR, exploitant les failles de partage SMB [E203][EBIOS-
  - [non soutenue] | M008 | A03 — Messagerie Sécurisée de Santé (Mél) — Logiciel / Service (LINDDUN-Disclosure) Fuite d'emails sensibles : exfiltration via OWA vulnérable et absence de filtrage SSL sur webmail.santetech-sant
  - [non soutenue] | M010 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet (STRIDE-I) Injection de session : authentification compromise par absence de MFA sur 60% des comptes AD, permettant pr
  - [non soutenue] | M012 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet (STRIDE-R) Ransomware sur accès distant : compromission du FortiGate via failles de certificats TLS non renouvelés, ex
  - [non soutenue] | M013 | A05 — Webmail de Santé & Accès Externe (OWA) — Service / Site Internet (STRIDE-E) Escalade de privilèges : exfiltration et modification des données via OWA Exchange 2016 non patché sur DMZ, sans f
  - [non soutenue] | M014 | A05 — Webmail de Santé & Accès Externe (OWA) — Service / Site Internet (LINDDUN-Disclosure) Fuite massive via campagnes Spraying : botnets exploitant Exchange 2016 DMZ pour exfiltrer données patie

## Contrôle n°10 — Étape 5 · Traitement, version 1 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : contrôle déterministe (termes absents des intrants, citations)  ·  2026-10-12 15:19:49
- Ce qui n'allait pas : 05-traitement.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E24], [E240], [E2], [E38], [E9], [E12], [E13], [E40], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (05-traitement.md); A7 (05-traitement.md).
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : 05-traitement.md : identifiants de preuve INEXISTANTS à retirer ou remplacer : [E7], [E5], [E24], [E240], [E2], [E38], [E9], [E12], [E13], [E40], [E32], [E3], [E57], [E36], [E271], [E274], [E277], [E25], [E18], [E16]. Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : A3 (05-traitement.md); A7 (05-traitement.md).
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `05-traitement.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
- Lignes à relire (les deux vérificateurs divergent sur la preuve citée) :
  - [non soutenue] | M001 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service (STRIDE-T) Attentat cyber : accès aux dossiers patients via exploitation des vulnérabilités legacy sur Citrix/RDS avec RDP non fi
  - [non soutenue] | M002 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service (LINDDUN-Disclosure) Fuite de données patients : progression horizontale (MOVElaterally) depuis les 185 serveurs legacy vers autr
  - [non soutenue] | M003 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service (STRIDE-I) Injection malveillante : modification des dossiers patients pendant la migration legacy-to-cloud via API Gateway non s
  - [non soutenue] | M004 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service (STRIDE-S) Substitution d'imagerie : injection de fichiers DICOM malformés ou corrompus via SMBv1 non patché dans les baies SAN locales v
  - [non soutenue] | M005 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service (STRIDE-R) Ransomware : chiffrement des images DICOM stockées sur baies SAN sans EDR, exploitant les failles de partage SMB [E203][EBIOS-
  - [non soutenue] | M006 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service (LINDDUN-Disclosure) Accès non autorisé aux images médicales : compromission d'un cache local en clinique via VLAN IoT non cloisonné (10.
  - [non soutenue] | M007 | A03 — Messagerie Sécurisée de Santé (Mél) — Logiciel / Service (STRIDE-S) ProxyShell exploitation : accès distant aux dossiers Exchange 2016 DMZ via vulnérabilité ProxyShell/Spraying sur webmail.s
  - [non soutenue] | M008 | A03 — Messagerie Sécurisée de Santé (Mél) — Logiciel / Service (LINDDUN-Disclosure) Fuite d'emails sensibles : exfiltration via OWA vulnérable et absence de filtrage SSL sur webmail.santetech-sant
  - [non soutenue] | M009 | A03 — Messagerie Sécurisée de Santé (Mél) — Logiciel / Service (STRIDE-E) Modification d'identité : création de comptes malveillants ou usurpation d'identité via exploitation Exchange 2016 sans MF
  - [non soutenue] | M010 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet (STRIDE-I) Injection de session : authentification compromise par absence de MFA sur 60% des comptes AD, permettant pr

## Contrôle n°11 — Étape 6 · Registre à valider, version 1 : CONFORME

- Contrôleur : contrôle par le programme (reprise ligne à ligne des étapes 3 à 5)  ·  2026-10-12 15:19:49
- Ce qui n'allait pas : rien à signaler
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.

## Contrôle n°12 — Étape 7 · Synthèse, version 1 : CONFORME

- Contrôleur : contrôle par le programme (reprise ligne à ligne des étapes 3 à 5)  ·  2026-10-12 15:21:49
- Ce qui n'allait pas : rien à signaler
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.

## Contrôle n°13 — Relecture finale, version 1 : NÉCESSITE UNE VALIDATION HUMAINE

- Contrôleur : ollama/gemma4:12b  ·  2026-10-12 15:22:03
- Ce qui n'allait pas : - "Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11" (A10) - "Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146]" (A24) - "Hébergé sur ferme Citrix/RDS (Siège Rennes) [E139]" (A25) - "Dossier Patient Informatisé (DPI) Nexus" (A01) - "Messagerie Sécurisée de Santé (Mél)" (A03) - "Portail VPN Télétravail & Praticiens Libéraux" (A04) - "Application métier — DPI Progiciel Nexus" (A18) - "Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142]" (A21)
- Ce qui a changé depuis la version précédente :
  Première version de l'étape.
- Pourquoi une validation humaine : Le contrôle signale toujours des points non conformes après les reprises demandées à l'agent : - "Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11" (A10) - "Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146]" (A24) - "Hébergé sur ferme Citrix/RDS (Siège Rennes) [E139]" (A25) - "Dossier Patient Informatisé (DPI) Nexus" (A01) - "Messagerie Sécurisée de Santé (Mél)" (A03) - "Portail VPN Télétravail & Praticiens Libéraux" (A04) - "Application métier — DPI Progiciel Nexus" (A18) - "Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142]" (A21)
- Quoi vérifier : Pour chaque point signalé, chercher l'affirmation dans `registre-risques.md`, `SYNTHESE.md` puis dans les documents d'origine ; si elle n'y est pas, c'est une invention à retirer ; si elle y est, le contrôle s'est trompé.
