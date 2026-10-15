# Analyse de risques de référence — SanteTech

**Projet E21 « Des agents IA pour analyser les risques »** — Melvin RAIMBAULT, Lucas HUARD, Jérémy LESSA, David AMARO MONTEIRO.
Date : 15/10/2026. Classeur de travail : `ANALYSE-MANUELLE-SANTETECH.xlsx` (même dossier).

## 1. Méthode

[V2 · après le 24/09/2026 · Melvin RAIMBAULT]

Le sujet demande une analyse de risques menée à la main, comparée ensuite à celle des agents. La référence est une liste de
**30 risques classiques** (incendie, inondation, coupure électrique, indisponibilité du site central, perte d'un lien, absence de
plan de reprise, sauvegardes, rançongiciel, comptes d'administration, VPN, messagerie, supervision, réseau, données de santé, IoT,
cloud, erreur humaine, prestataire) **appliqués aux faits du cas SanteTech** : actifs et incidents tels que décrits dans les pièces
du cas (réseau MPLS en étoile, ferme Citrix/RDS, 16 contrôleurs de domaine, VPN sans MFA sur 60 % des comptes, ≈ 4 000 dispositifs
IoT, PACS en SMBv1, hébergeur cloud non arrêté). Chaque risque a un actif, une menace, une probabilité, un impact, un niveau
(matrice du sujet : probabilité × impact), un traitement, une mesure et une source (mesure ISO/IEC 27002:2022).

Elle a été établie **avant** le rapprochement avec le registre : les risques ne sont pas repris du registre des agents.
Le classeur complet est `soutenance/analyse-manuelle/ANALYSE-MANUELLE-SANTETECH.xlsx` (feuilles : analyse, comparaison, matrice
et bilan ; probabilité, impact et statut de validation y sont modifiables).

## 2. L'analyse de référence : 30 risques

| N° | Risque (actif — menace) | P / I | Niveau | Mesure proposée (source) |
|---|---|---|---|---|
| MR-01 | **Salle serveurs du siège (Rennes) : ferme Citrix/RDS, DPI Nexus, AD** — Incendie de la salle serveurs du siège : perte simultanée du DPI, de l'annuaire et de la ferme Citrix/RDS | Faible / Élevé | Moyen | Détection et extinction automatiques adaptées aux salles IT ; copie des données et site de secours hors du bâtiment (ISO27002-7.5) |
| MR-02 | **Locaux techniques du siège et des cliniques** — Inondation ou dégât des eaux d'un local technique (baies, onduleurs, répartiteurs réseau) | Faible / Élevé | Moyen | Salles hors zone inondable ou surélevées, détection d'eau, procédure d'arrêt contrôlé, équipement de secours (ISO27002-7.5) |
| MR-03 | **Alimentation électrique du siège et des 12 cliniques** — Coupure électrique prolongée ou onduleurs défaillants : arrêt des serveurs et des équipements réseau | Moyenne / Élevé | Élevé | Onduleurs entretenus, groupe électrogène testé périodiquement, extinction ordonnée des systèmes (ISO27002-7.11) |
| MR-04 | **Locaux techniques, postes et supports des cliniques** — Intrusion ou vol de matériel dans un local technique ou d'un poste contenant des données patients | Moyenne / Moyen | Moyen | Contrôle d'accès et journal des entrées, chiffrement des disques, verrouillage des locaux techniques (ISO27002-7.2) |
| MR-05 | **Réseau MPLS en étoile : le siège est le centre de toutes les cliniques** — Indisponibilité du site central : tout le trafic des 12 cliniques transite par le siège ; une panne du siège paralyse l'ensemble | Moyenne / Élevé | Élevé | Lien et équipements redondants, second point d'accès, cliniques capables de fonctionner en mode dégradé (ISO27002-8.14) |
| MR-06 | **Lien opérateur d'une clinique** — Perte du lien MPLS d'une clinique : site isolé du système d'information central | Moyenne / Moyen | Moyen | Second lien (4G/5G ou opérateur différent), mode dégradé local documenté (ISO27002-8.14) |
| MR-07 | **Ensemble du système d'information (aucun site de secours documenté)** — Absence de plan de reprise d'activité éprouvé et de site secondaire : en cas de sinistre majeur, reprise longue et incertaine | Moyenne / Élevé | Élevé | Plan de reprise d'activité avec objectifs de reprise, site secondaire, test annuel ; point à vérifier : non documenté dans les pièces (ISO27002-5.30) |
| MR-08 | **Sauvegardes du DPI, de l'annuaire et des serveurs** — Sauvegardes absentes, non testées ou stockées au même endroit : perte de données lors d'un sinistre ou d'un rançongiciel | Moyenne / Élevé | Élevé | Règle 3-2-1 avec copie hors ligne et immuable, test de restauration régulier ; point à vérifier : non documenté (ISO27002-8.13) |
| MR-09 | **Baies SAN vieillissantes du PACS/RIS** — Défaillance du stockage vieillissant : perte ou indisponibilité des images médicales | Moyenne / Élevé | Élevé | Renouvellement planifié, réplication des images, surveillance de l'état des disques (ISO27002-8.14) |
| MR-10 | **Serveurs et systèmes en fin de support (ESXi 6.5, Windows Server 2012 R2)** — Panne ou compromission sans correctif possible d'un système en fin de support | Élevée / Moyen | Élevé | Inventaire des versions, plan de migration daté, isolation des systèmes non migrables (ISO27002-8.8) |
| MR-11 | **Annuaire Active Directory (forêt unique, 16 contrôleurs de domaine)** — Rançongiciel qui chiffre l'annuaire et les serveurs en se propageant dans un réseau peu cloisonné | Élevée / Élevé | Critique | Segmentation, sauvegardes immuables, EDR, comptes administrateurs séparés, exercice de crise cyber (ISO27002-8.7) |
| MR-12 | **Comptes d'administration de l'annuaire** — Compromission d'un compte administrateur de domaine et élévation de privilèges sur toute la forêt | Moyenne / Élevé | Élevé | Comptes d'administration dédiés et protégés (MFA, postes d'administration), modèle de niveaux, revue des droits (ISO27002-8.2) |
| MR-13 | **Portail VPN FortiGate (MFA absente sur une partie des comptes)** — Accès au VPN par vol ou bourrage d'identifiants : entrée directe dans le réseau interne | Élevée / Élevé | Critique | MFA obligatoire pour tous les comptes distants (carte CPS ou application), blocage des essais répétés, géo-filtrage (ISO27002-8.5) |
| MR-14 | **Messagerie Exchange 2016 exposée et webmail OWA** — Exploitation d'une vulnérabilité de type ProxyShell sur le serveur de messagerie exposé sur Internet | Élevée / Élevé | Critique | Correctifs appliqués sans délai, mise à jour ou migration du serveur, filtrage applicatif (WAF), surveillance (ISO27002-8.8) |
| MR-15 | **Messagerie et postes des soignants et du personnel administratif** — Hameçonnage ciblant le personnel : vol d'identifiants ou ouverture d'une pièce jointe malveillante | Élevée / Moyen | Élevé | Sensibilisation régulière avec campagnes de test, filtrage des messages, MFA, signalement simple des mails suspects (ISO27002-6.3) |
| MR-16 | **Supervision de sécurité (aucun SOC, EDR ni SIEM en place)** — Intrusion non détectée pendant des semaines faute de supervision et de journaux centralisés | Élevée / Élevé | Critique | Journalisation centralisée, EDR sur serveurs et postes, supervision par un SOC interne ou externalisé (ISO27002-8.16) |
| MR-17 | **Postes legacy d'imagerie (≈ 5 % en Windows 7 / XP Embedded)** — Compromission d'un poste legacy, non patchable, comme point d'entrée dans le réseau de la clinique | Élevée / Moyen | Élevé | Isolation dans un VLAN dédié, liste blanche d'applications, accès Internet interdit, plan de remplacement (ISO27002-8.22) |
| MR-18 | **Réseau interne des cliniques (VLAN IoT/biomédical non cloisonné, aucune isolation entre sites)** — Mouvement latéral d'un attaquant depuis un poste ou un équipement compromis vers les serveurs et les autres cliniques | Élevée / Élevé | Critique | Micro-segmentation, filtrage inter-sites et inter-VLAN, contrôle d'accès réseau (NAC) (ISO27002-8.22) |
| MR-19 | **Wi-Fi invités et patients (sortie Internet directe sans filtrage)** — Utilisation du Wi-Fi invité pour attaquer ou rebondir, ou pour des usages illicites imputables à l'établissement | Moyenne / Moyen | Moyen | Réseau isolé du SI, filtrage web, authentification des invités, journalisation, limitation de débit (ISO27002-8.20) |
| MR-20 | **Services exposés sur Internet (VPN, webmail, extranet, sites des cliniques)** — Déni de service rendant indisponibles les services exposés aux patients, praticiens et partenaires | Moyenne / Moyen | Moyen | Protection anti-DDoS chez l'opérateur ou l'hébergeur, limitation de débit, exploitation en mode dégradé (ISO27002-8.20) |
| MR-21 | **Dossiers patients (≈ 150 000) du DPI Nexus** — Fuite de données de santé par exfiltration, mauvaise gestion des droits ou compte compromis | Moyenne / Élevé | Élevé | Droits au moindre privilège, chiffrement, détection d'exfiltration, journal d'accès aux dossiers (ISO27002-8.12) |
| MR-22 | **Dossiers patients accessibles au personnel** — Consultation abusive de dossiers par un agent interne (curiosité, personnalités) sans contrôle effectif | Élevée / Moyen | Élevé | Journalisation nominative des accès, revue régulière et alertes sur accès atypiques, sanctions rappelées (ISO27002-8.15) |
| MR-23 | **Traitement de données de santé (RGPD, hébergement de données de santé)** — Non-conformité réglementaire (RGPD, hébergement de données de santé) : sanctions et obligations de notification manquées | Moyenne / Élevé | Élevé | Registre des traitements, analyses d'impact, procédure de notification, référent protection des données (ISO27002-5.34) |
| MR-24 | **Postes et supports mobiles des cliniques** — Perte ou vol d'un poste ou d'un support non chiffré contenant des données patients | Moyenne / Moyen | Moyen | Chiffrement des disques et supports, gestion des postes, procédure de déclaration de perte (ISO27002-8.1) |
| MR-25 | **Parc IoT médical (≈ 4 000 dispositifs, certains non patchables)** — Compromission d'un dispositif connecté non patchable (pompe, moniteur) : perturbation des soins ou rebond vers le réseau | Moyenne / Élevé | Élevé | VLAN dédié, flux strictement filtrés, inventaire, supervision passive, mesures compensatoires convenues avec les fabricants (ISO27002-8.22) |
| MR-26 | **PACS/RIS (stockage DICOM, protocole SMBv1)** — Propagation d'un ver exploitant SMBv1 (type WannaCry) : arrêt de l'imagerie dans les cliniques | Moyenne / Élevé | Élevé | Désactiver SMBv1 ou isoler les systèmes qui en dépendent, correctifs, segmentation, sauvegardes hors ligne (ISO27002-8.8) |
| MR-27 | **Hébergeur cloud certifié pour les données de santé (choix non arrêté)** — Dépendance à l'hébergeur : réversibilité difficile, exposition à des lois extra-européennes, indisponibilité du fournisseur | Moyenne / Moyen | Moyen | Clauses de réversibilité et de localisation, choix d'un hébergeur certifié et européen, stratégie de sortie testée (ISO27002-5.23) |
| MR-28 | **Applications et API du cloud hybride (télémédecine)** — Erreur de configuration ou exposition non prévue d'une API pendant la migration : accès non autorisé aux données | Moyenne / Élevé | Élevé | Revue de configuration avant mise en service, passerelle d'API avec authentification, tests d'intrusion, gestion des secrets (ISO27002-8.9) |
| MR-29 | **Administration des pare-feu, serveurs et annuaire** — Erreur humaine d'un administrateur (règle trop ouverte, suppression) sans revue ni retour arrière | Moyenne / Moyen | Moyen | Gestion des changements avec revue, sauvegarde de configuration, séparation des tâches, procédure de retour arrière (ISO27002-8.32) |
| MR-30 | **Sites web des 12 cliniques hébergés chez un prestataire (WordPress non durci)** — Défacement ou compromission des sites des cliniques, ou défaillance du prestataire : atteinte à l'image et phishing de patients | Moyenne / Moyen | Moyen | Contrat avec exigences de sécurité et de reprise, durcissement et mises à jour, surveillance de l'intégrité (ISO27002-5.20) |

Répartition : 5 Critique, 15 Élevé, 10 Moyen, 0 Faible. Les 30 risques ont le traitement « Réduire », sauf MR-30
(« Transférer » : sites hébergés chez un prestataire). Point à vérifier : l'existence d'un plan de reprise et de sauvegardes
testées n'est pas documentée dans les pièces (MR-07, MR-08) ; le risque est posé comme « non démontré », à confirmer auprès
du client.

## 3. Comparaison avec le registre des agents

Registre des agents : **135 risques** (75 Critique, 35 Élevé, 13 Moyen, 12 Faible).

| N° | Risque de référence | Niv. | Couverture | Risques des agents rapprochés | Écart | Observation |
|---|---|---|---|---|---|---|
| MR-01 | Incendie de la salle serveurs du siège | Moyen | Non couvert | — | — | Aucun risque de sinistre physique dans le registre : les agents ne produisent que des scénarios d'attaque (STRIDE, LINDDUN). |
| MR-02 | Inondation ou dégât des eaux d'un local technique (baies, onduleurs, répartiteurs réseau) | Moyen | Non couvert | — | — | Idem : aucun risque d'inondation ou de dégât des eaux. |
| MR-03 | Coupure électrique prolongée ou onduleurs défaillants | Élevé | Non couvert | — | — | Idem : aucun risque de coupure électrique ni d'onduleur. |
| MR-04 | Intrusion ou vol de matériel dans un local technique ou d'un poste contenant des données patients | Moyen | Partiel | M053, M099 | Même niveau | M053 traite l'exposition physique des locaux informatiques, M099 le stockage non chiffré en clinique. Le vol de matériel n'est pas nommé comme scénario. |
| MR-05 | Indisponibilité du site central | Élevé | Partiel | M091, M095, M127, M033, M055 | Même niveau | Le MPLS en étoile est vu comme un défaut de cloisonnement (propagation), pas comme un point unique de défaillance : la panne du siège n'est pas décrite. M033 et M055 touchent la perte d'authentification. |
| MR-06 | Perte du lien MPLS d'une clinique | Moyen | Non couvert | — | — | La perte du lien d'une clinique n'est pas traitée (M127 concerne l'isolation logique, pas la disponibilité). |
| MR-07 | Absence de plan de reprise d'activité éprouvé et de site secondaire | Élevé | Non couvert | — | — | Aucun risque d'absence de plan de reprise ou de site secondaire (M118 parle de surcharge des serveurs de secours, pas du plan de reprise). |
| MR-08 | Sauvegardes absentes, non testées ou stockées au même endroit | Élevé | Non couvert | — | — | Aucun risque sur les sauvegardes (absence, test de restauration, copie hors ligne). |
| MR-09 | Défaillance du stockage vieillissant | Élevé | Partiel | M004, M005, M016 | Agents plus haut (+1) | La perte des images est décrite comme conséquence d'une attaque (SMB, rançongiciel, malware) ; la panne matérielle du stockage vieillissant n'est pas décrite. |
| MR-10 | Panne ou compromission sans correctif possible d'un système en fin de support | Élevé | Couvert | M001, M002, M034, M058, M093, M094, M116 | Agents plus haut (+1) | Bien couvert, sous l'angle des vulnérabilités des systèmes legacy (Citrix, Windows 7/XP, serveurs non patchés). |
| MR-11 | Rançongiciel qui chiffre l'annuaire et les serveurs en se propageant dans un réseau peu cloisonné | Critique | Couvert | M005, M012, M111 | Même niveau | Rançongiciel couvert sur les images, l'accès distant et l'absence de détection. |
| MR-12 | Compromission d'un compte administrateur de domaine et élévation de privilèges sur toute la forêt | Élevé | Couvert | M027, M054, M097, M098, M108, M109 | Agents plus haut (+1) | Couvert avec plus de finesse technique que la référence (DCSync, Kerberoasting, LSASS, objets Kerberos). |
| MR-13 | Accès au VPN par vol ou bourrage d'identifiants | Critique | Couvert | M010, M011, M052, M106, M122, M114 | Même niveau | Couvert : absence de MFA sur 60 % des comptes, vol d'identifiants, usurpation. |
| MR-14 | Exploitation d'une vulnérabilité de type ProxyShell sur le serveur de messagerie exposé sur Internet | Critique | Couvert | M007, M060, M104, M124, M115 | Même niveau | Couvert, ProxyShell nommé explicitement. |
| MR-15 | Hameçonnage ciblant le personnel | Élevé | Couvert | M072, M082, M102, M114 | Agents plus haut (+1) | Couvert sous plusieurs angles (soignants, patients par SMS, usurpation de messagerie). |
| MR-16 | Intrusion non détectée pendant des semaines faute de supervision et de journaux centralisés | Critique | Couvert | M111, M112, M113, M125 | Agents plus bas (-1) | Couvert : détection inexistante, absence de SIEM, exfiltration non détectée. |
| MR-17 | Compromission d'un poste legacy, non patchable, comme point d'entrée dans le réseau de la clinique | Élevé | Couvert | M093, M094 | Agents plus haut (+1) | Couvert : fuite de données et élévation de privilèges depuis les postes Windows 7/XP. |
| MR-18 | Mouvement latéral d'un attaquant depuis un poste ou un équipement compromis vers les serveurs et les autres cliniques | Critique | Couvert | M070, M057, M127, M128, M092, M095 | Agents plus bas (-1) | Couvert : micro-segmentation absente, VLAN IoT non cloisonné, propagation entre cliniques. |
| MR-19 | Utilisation du Wi-Fi invité pour attaquer ou rebondir, ou pour des usages illicites imputables à l'établissement | Moyen | Couvert | M048, M049, M132, M133, M071 | Agents plus haut (+1) | Couvert, avec des niveaux plus élevés que la référence (le Wi-Fi invité n'a pas de lien direct avec le DPI). |
| MR-20 | Déni de service rendant indisponibles les services exposés aux patients, praticiens et partenaires | Moyen | Couvert | M015, M077, M125, M055 | Agents plus haut (+1) | Couvert : Exchange, API de télémédecine, contrôleur de domaine unique. |
| MR-21 | Fuite de données de santé par exfiltration, mauvaise gestion des droits ou compte compromis | Élevé | Couvert | M002, M040, M062, M080, M085 | Agents plus haut (+1) | Très couvert (39 risques du registre parlent de fuite ou d'exfiltration) ; risque de redite plutôt que de manque. |
| MR-22 | Consultation abusive de dossiers par un agent interne (curiosité, personnalités) sans contrôle effectif | Élevé | Partiel | M061, M129 | Même niveau | Traçabilité insuffisante des accès (M061) et accès RDP interne non contrôlé (M129) ; la consultation abusive par un agent n'est pas nommée comme scénario. |
| MR-23 | Non-conformité réglementaire (RGPD, hébergement de données de santé) | Élevé | Partiel | M043, M044, M117 | Agents plus haut (+1) | Conformité vue sous l'angle HDS et Cloud Act (M043, M044). Le RGPD n'est traité que par M117 (niveau Faible, formulation hors sujet) : notification, registre des traitements, analyse d'impact absents. |
| MR-24 | Perte ou vol d'un poste ou d'un support non chiffré contenant des données patients | Moyen | Partiel | M099, M053 | Même niveau | Stockage non chiffré en clinique (M099) ; la perte ou le vol d'un poste n'est pas évoqué comme tel. |
| MR-25 | Compromission d'un dispositif connecté non patchable (pompe, moniteur) | Élevé | Couvert | M045, M064, M063, M088, M089, M130 | Agents plus haut (+1) | Couvert, plusieurs angles (dosage, commandes Wi-Fi 6, botnets, routage direct vers les automates). |
| MR-26 | Propagation d'un ver exploitant SMBv1 (type WannaCry) | Élevé | Couvert | M004, M005, M016, M059, M094 | Agents plus haut (+1) | Couvert : SMBv1 sur le PACS/RIS nommé explicitement. |
| MR-27 | Dépendance à l'hébergeur | Moyen | Partiel | M043, M044 | Agents plus haut (+2) | Cloud Act et certification HDS traités ; réversibilité et indisponibilité du fournisseur absentes. |
| MR-28 | Erreur de configuration ou exposition non prévue d'une API pendant la migration | Élevé | Couvert | M003, M050, M062, M041, M134 | Agents plus haut (+1) | Couvert : API Gateway non sécurisée, flux non inventoriés, migration du DPI. |
| MR-29 | Erreur humaine d'un administrateur (règle trop ouverte, suppression) sans revue ni retour arrière | Moyen | Non couvert | — | — | Aucun risque d'erreur humaine d'administration ni de gestion des changements. |
| MR-30 | Défacement ou compromission des sites des cliniques, ou défaillance du prestataire | Moyen | Couvert | M021, M023, M025, M126, M121 | Agents plus haut (+1) | Défacement et CMS couverts ; la défaillance du prestataire (volet contractuel) n'est pas traitée. |

## 4. Ce que montre la comparaison

- **Couverture : 16 risques sur 30 sont couverts, 7 partiellement, 7 pas du tout.**
  Les 7 risques absents du registre sont tous de l'ordre du **sinistre physique, de la continuité et de
  l'organisation** : incendie, inondation, coupure électrique, perte d'un lien, plan de reprise, sauvegardes, erreur d'administration.
  Les 7 partiels vont dans le même sens (panne du site central, stockage vieillissant, vol de matériel, RGPD,
  réversibilité de l'hébergeur). Le registre des agents est un registre de **scénarios d'attaque** (STRIDE, LINDDUN) : l'angle
  « disponibilité et continuité » est le point faible. Hypothèse, non vérifiée : les référentiels indexés orientent vers
  l'attaquant, pas vers le sinistre.
- **Profondeur : les agents vont plus loin sur le technique.** 135 risques contre 30, avec un détail que la référence n'a pas
  (DCSync, Kerberoasting, vidage de LSASS, CVE de Citrix, commandes Wi-Fi 6 non chiffrées, détournement DNS, XSS d'administration).
- **Niveaux : les agents classent plus haut.** Sur les 23 risques rapprochés, 14 sont notés plus haut par les agents,
  7 au même niveau, 2 plus bas. 75 risques sur 135
  (56 %) sont « Critique » contre 5 sur 30 (17 %) en référence :
  un registre où plus d'un risque sur deux est critique ne permet plus de prioriser. C'est un des rôles de la validation humaine.
- **Qualité : des risques du registre sont à écarter ou à reformuler.** 6 risques sont rattachés à des « actifs »
  qui n'en sont pas (A36 « Attestation de relecture croisée », A37 « CISO / Lead GRC », A38 « Blue Team & SOC » : pièces de méthode et
  rôles, pas des actifs du système d'information) : M114, M115, M116, M117, M118, M119. Le risque M114, classé Critique, est rattaché à
  l'actif A36. M020 (extranet) et M023 (sites des cliniques) répètent la même menace mot pour mot, avec des niveaux différents (Faible, Élevé). M117 et M119 portent sur le
  projet (ignorance du RGPD par un chef de projet, norme ISO 27001) plutôt que sur le système d'information.
- **Aucun risque du registre n'est validé** (`valide_par` vide pour les 135) : ces constats sont exactement ce que la validation
  page ④ doit trancher, risque par risque.

## 5. Limites de cette comparaison

- La référence est une liste de revue de 30 risques, non un inventaire exhaustif. Elle n'est pas une vérité terrain ; un risque
  « non couvert » indique un écart entre deux listes, pas forcément un oubli grave.
- Le rapprochement (quel risque des agents correspond à quel risque de référence) a été fait par lecture et mots-clés puis jugement,
  sans second relecteur : les identifiants donnés sont les principaux rapprochements.
