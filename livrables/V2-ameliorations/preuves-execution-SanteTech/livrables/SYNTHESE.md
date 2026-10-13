# Synthèse (étape 7)

> Document d'orientation pour une décision de direction (structure inspirée du guide `ANSSI-PSSI` : faits, décisions, actions). Les chiffres sont CALCULÉS par le programme à partir du registre des risques, pas écrits par un modèle ; chaque risque garde l'identifiant du registre.

## 1. Résumé exécutif

L'analyse porte sur **39 actifs** et **135 risques**. 75 risques sont évalués au niveau Critique (56 %), 35 Élevé, 13 Moyen et 12 Faible. Traitement proposé : 123 à réduire, 7 à éviter, 4 à accepter, 1 à transférer. Aucun risque n'a encore été décidé : les 135 risques sont proposés et attendent la validation d'un analyste. L'actif le plus exposé est **A10 — Applications Cloud Hybride (To-Be) — Logiciel / Service — Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11** (6 risques dont 6 critiques).

**Lecture** (rédigée par le modèle, dont les chiffres ont été recontrôlés par le programme) :

L'analyse porte sur 39 actifs et identifie 135 risques majeurs. Sur l'ensemble,
75 sont classés niveau Critique (56 %) et 35 sont Élevé (26 %). Les traitements principaux
visent à réduire l'impact avec 123 actions prévues sur le catalogue des mesures. Seuls
7 risques peuvent être évités par isolement ou refonte architecturale, tandis que 4 acceptations
et 1 transfert complètent la stratégie de mitigation globale.

Aucun des 135 risques n'a encore été validé par l'équipe d'analyse en charge du
contrôle final. Une validation humaine reste nécessaire pour trancher chaque cas et s'assurer
d'une couverture complète des besoins opérationnels tout en respectant les normes de sécurité
imposées.

## 2. Chiffres clés

| Indicateur | Valeur |
|---|---|
| Actifs analysés | 39 |
| Risques au registre | 135 |
| Niveau Critique | 75 (56 %) |
| Niveau Élevé | 35 (26 %) |
| Niveau Moyen | 13 (10 %) |
| Niveau Faible | 12 (9 %) |
| Traitement : Réduire | 123 |
| Traitement : Éviter | 7 |
| Traitement : Accepter | 4 |
| Traitement : Transférer | 1 |
| Risques décidés par un analyste | 0 sur 135 |

## 3. Où se concentre le risque

| Actif | Risques | Dont Critique | Dont Élevé |
|---|---|---|---|
| A10 — Applications Cloud Hybride (To-Be) — Logiciel / Service — Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11 | 6 | 6 | 0 |
| A24 — API Télémédecine Cloud Hybride — Logiciel / Service — Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146] | 6 | 6 | 0 |
| A25 — Plateforme DPI Nexus (Dossier Patient Informatisé) — Logiciel / Service — Hébergé sur ferme Citrix/RDS (Siège Rennes) [E139] | 5 | 3 | 1 |
| A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | 4 | 3 | 1 |
| A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | 3 | 3 | 0 |
| A03 — Messagerie Sécurisée de Santé (Mél) — Logiciel / Service | 3 | 3 | 0 |
| A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet | 3 | 3 | 0 |
| A18 — Application métier — DPI Progiciel Nexus | 3 | 3 | 0 |

## 4. Risques prioritaires (les 10 premiers par niveau, impact puis probabilité)

| ID | Actif | Menace | Niveau | Pourquoi (étape 4) | Traitement | Risque résiduel |
|---|---|---|---|---|---|---|
| M060 | A19 — Donnée/Structure — Données Patients (DPI) | STRIDE-I — Information leakage via exploitation ProxyShell sur Exchange 2016 non patché (DMZ vulnérable aux attacks Spraying) [E168][A17] | Critique | ProxyShell exploitables sur Exchange 2016 non patché en DMZ + campagnes Spraying permettent extraction massive données patients critiques [E168][A17][CVE-2022-31497] | Réduire | Élevé |
| M054 | A17 — Infrastructure réseau — Active Directory | STRIDE-T — Tampering des permissions AD via exploitation de compte service faible sur 60% des postes (pas de MFA sur VPN) enclinning aux attacks pass-the-hash [E140] | Critique | Compte service faible + 60% postes sans MFA VPN permettent pass-the-hash et tampering permissions AD unique CVE‑2021-38619 [E140][A17] | Réduire | Élevé |
| M058 | A18 — Application métier — DPI Progiciel Nexus | STRIDE-E — Élévation de privilèges via vulnérabilités Citrix XenApp/RDS (XenDesktop 7.15 CVE-2020-34692) permettant l'exécution code sur ferme RDS Siège [E146] | Critique | CVE-2020-34692 Citrix XenApp exploitables sur ferme RDS Siège permettent exécution code et élévation privilèges globale [E146][A17] | Réduire | Élevé |
| M062 | A19 — Donnée/Structure — Données Patients (DPI) | LINDDUN-D — Disclosure de 150 000 dossiers via API Gateway non sécurisée pour télémédecine (no authz, no encryption in transit) [E231][A11] | Critique | API Gateway télémédecine sans authentification/autorisation ni chiffrement transit expose 150 k dossiers patients [E146, E203, CVE-2023-38448] | Réduire | Critique |
| M068 | A21 — Infrastructure Cloud — Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] | LINDDUN-Disclosure — Fuite de données patients via container compromis exposé sur métadonnées publics S3 → exfiltration de dossiers médicaux identifiables [E146,LINDDUN-Disclosure] | Critique | Container S3 exposé à métadonnées publiques permettant exfiltration continue de données médicales identifiées sans chiffrage [E146, E149, LINDDUN-D] | Réduire | Critique |
| M070 | A22 — Infrastructure sécurité — Micro-segmentation VLAN/NAC — Architecture cible pour isoler poste clinique compromis (VLAN IoT/Biomedical 10.1.30.0/24 non cloisonné actuellement) [E146,E150,FichedAuditTechnique-ÉtatdesLieuxSanteTechAs-Is.pdf.md,E205] | STRIDE-R — Attaquant interne : poste clinique compromis contourne NAC mal configuré → mouvement latéral via VLAN IoT non isolé (10.1.30.0/24) vers serveurs critiques PACS/RIS [E146,E205,STRIDE-R] | Critique | Poste clinique compromis atteint PACS/RIS critique via VLAN IoT non cloisonné 10.1.30.0/24 (routage direct) [E169, E203, STRIDE-R] | Éviter | Critique |
| M089 | A26 — Parc IoT Médical | LINDDUN-D — Fuite de données sensibles via les dispositifs IoT non isolés, exploitant le routage direct vers les automates [E203] | Critique | IoT biomédical connecté sans isolation réseau → données capteurs patient fuites routage direct vers automates [E203] → atteinte confidentialité/sécurité patients grave [LINDDUN-D,EBIOS-RM-A4] | Réduire | Faible : IoT biomédical isolé physiquement + flux capteurs cryptés en transit [E140] |
| M091 | A27 — Ferme Citrix/RDS | STRIDE-S — Spoofing via le réseau MPLS non segmenté, permettant l'accès à tous les serveurs physiques [E139] | Critique | Ferme Citrix/RDS connectée sur réseau MPLS non segmenté avec accès physique direct à tous serveurs → compromission systémique tout le siège [E139,STRIDE-S] → atteinte intégrité masse données [EBIOS-RM-A4] | Réduire | Faible : ferme Citrix/RDS isolée sur MPLS segmenté + accès direct restreint à serveurs certifiés [E139] |
| M093 | A28 — Postes legacy | LINDDUN-D — Fuite de données patients via les postes Windows 7/XP, non durcis contre les attaques par usurpation [E150] | Critique | Postes Windows 7/XP non durcis + système de santé sensible → fuites données patients vulnérabilités connues exploitables (MS08-067 SMBv1, EternalBlue) [E150,LINDDUN-D] → données critiques exposées | Éviter | Négligeable : postes Windows 7/XP mis en service de secours uniquement (non critiques) + migration planifiée [E150] |
| M095 | A29 — MPLS Hub & Spoke | STRIDE-S — Spoofing via le réseau centralisé sans isolation, permis par la micro-segmentation absente [E139] | Critique | Réseau MPLS Hub&Spoke centralisé sans isolation micro-segmentation → spoofing routes atteste exposition tous sites [E139,STRIDE-S] → accès transversal clinique à clinique | Réduire | Très Faible : interconnexion sites via IPsec chiffré seul + ACL routage segmenté [E140] |

## 5. Actions recommandées

Chaque action vient du traitement de l'étape 5 pour le risque indiqué ; la revue suit le plan de `06-validation.md`.

| Priorité | Risque | Action (contre-mesures proposées) | Prochaine revue |
|---|---|---|---|
| Critique | M060 | Patch Exchange 2016 (ANSSI-RECYF) + MFA (ISO27002-8.8) | mensuelle |
| Critique | M054 | MFA FIDO2 (ISO27002-8.8) + rotation cred (ANSSI-HYGIENE) | mensuelle |
| Critique | M058 | Patch immédiat CVE-2020-34692 (ANSSI-RECYF) + virtualisation (ISO27002-8.16) | mensuelle |
| Critique | M062 | Authentification à deux facteurs (ISO27002-8.8), Chiffrement transit (ANSSI-HYGIENE-8.14), Audit API Gateway (ANSSI-RECYF) | mensuelle |
| Critique | M068 | Chiffrement S3 (ISO27002-8.14), Séparation containers (ANSSI-HYGIENE-8.11), Audit métadonnées (STRIDE-D) | mensuelle |
| Critique | M070 | Cloisonnement VLAN 10.1.30.0/24 (ANSSI-HYGIENE-8.11), NAC étendu (ISO27002-8.2), Suppression routage direct (STRIDE-R) | mensuelle |
| Critique | M089 | Isolation réseau physique (pas logique seulement) pour dispositifs biomédicaux critiques + chiffrement de bout en bout des flux capteurs [ANSSI-PSSI,ISO27002-8.5,LINDDUN-D] | mensuelle |
| Critique | M091 | Segment MPLS avec micro-segmentation (VLAN par service) + accès direct limité uniquement par IP + authentification réseau 802.1X obligatoire [ANSSI-CARTO-SI,ISO27002-5.4,STRIDE-S] | mensuelle |
| Critique | M093 | Migration progressive vers Windows 10/11 LTSC ou Linux avec agents HDS [ANSSI-HYGIENE-5,EBIOS-RM-A4,LINDDUN-D] | mensuelle |
| Critique | M095 | Intersegment MPLS avec ACL strictes (IPsec VPN entre hubs) + chiffrement TLS obligatoire sur toutes routes transversales + IDS L7 inspection trafic [ANSSI-CARTO-SI,ISO27002-6.3,STRIDE-S] | mensuelle |

## 6. Décisions de l'analyste

Aucune décision enregistrée : les 135 risques restent « À valider par l'analyste ».

## 7. Limites et points à vérifier

- **Niveaux à relire en priorité** : 75 risques sur 135 (56 %) sont évalués Critique. Le niveau est CALCULÉ par le programme (matrice probabilité × impact) à partir des valeurs proposées par le modèle ; quand presque tout est critique, la hiérarchie ne guide plus : relisez d'abord les probabilités et les impacts.
- **Étapes à valider par une personne** : 1, 2, 3, 4, 5 ; 163 ligne(s) dont la preuve citée n'a pas pu être établie par la machine (page ④, « Lignes à relire », par pages de dix).

## 8. Comment lire ce dossier

- `registre-risques.md` : tous les risques, une ligne chacun, de la menace au traitement.
- `06-validation.md` : ce qui reste à décider, le plan de suivi, et les décisions prises.
- `03-menaces.md`, `04-evaluation.md`, `05-traitement.md` : le détail et les preuves `[E…]`.
- `RAPPORT-CONTROLE.md` : ce que le contrôle a relevé, étape par étape.
