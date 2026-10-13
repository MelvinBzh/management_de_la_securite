# Validation et suivi (étape 6)

> Document établi par le programme à partir du registre des risques. Il ne contient AUCUNE décision : les décisions sont prises par une personne dans la page ④ du site, puis ajoutées en bas de ce document (qui, quand, pourquoi).

## 1. État de la validation

- Risques au registre : **135**.
- Décidés par un analyste : **0** (0 acceptés, 0 acceptés avec modification, 0 refusés).
- Restant à valider : **135**.

| Niveau | Risques | Dont décidés |
|---|---|---|
| Critique | 75 | 0 |
| Élevé | 35 | 0 |
| Moyen | 13 | 0 |
| Faible | 12 | 0 |

## 2. Risques à décider en priorité (niveaux Critique et Élevé)

La colonne « Décision » se remplit dans le site (page ④) ; elle est ici pour mémoire.

| ID | Actif | Niveau | Traitement proposé | Risque résiduel | Décision | Responsable |
|---|---|---|---|---|---|---|
| M060 | A19 — Donnée/Structure — Données Patients (DPI) | Critique | Réduire | Élevé | À décider | À désigner |
| M054 | A17 — Infrastructure réseau — Active Directory | Critique | Réduire | Élevé | À décider | À désigner |
| M058 | A18 — Application métier — DPI Progiciel Nexus | Critique | Réduire | Élevé | À décider | À désigner |
| M062 | A19 — Donnée/Structure — Données Patients (DPI) | Critique | Réduire | Critique | À décider | À désigner |
| M068 | A21 — Infrastructure Cloud — Hébergeur Cloud Hybride — HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] | Critique | Réduire | Critique | À décider | À désigner |
| M070 | A22 — Infrastructure sécurité — Micro-segmentation VLAN/NAC — Architecture cible pour isoler poste clinique compromis (VLAN IoT/Biomedical 10.1.30.0/24 non cloisonné actuellement) [E146,E150,FichedAuditTechnique-ÉtatdesLieuxSanteTechAs-Is.pdf.md,E205] | Critique | Éviter | Critique | À décider | À désigner |
| M089 | A26 — Parc IoT Médical | Critique | Réduire | Faible : IoT biomédical isolé physiquement + flux capteurs cryptés en transit [E140] | À décider | À désigner |
| M091 | A27 — Ferme Citrix/RDS | Critique | Réduire | Faible : ferme Citrix/RDS isolée sur MPLS segmenté + accès direct restreint à serveurs certifiés [E139] | À décider | À désigner |
| M093 | A28 — Postes legacy | Critique | Éviter | Négligeable : postes Windows 7/XP mis en service de secours uniquement (non critiques) + migration planifiée [E150] | À décider | À désigner |
| M095 | A29 — MPLS Hub & Spoke | Critique | Réduire | Très Faible : interconnexion sites via IPsec chiffré seul + ACL routage segmenté [E140] | À décider | À désigner |
| M097 | A30 — Active Directory | Critique | Réduire | Élevée·Critique·Moyen | À décider | À désigner |
| M102 | A32 — Messagerie Exchange 2016 OWA Webmail | Critique | Réduire | Élevée·Critique·Faible | À décider | À désigner |
| M104 | A32 — Messagerie Exchange 2016 OWA Webmail | Critique | Réduire | Élevée·Critique·Faible | À décider | À désigner |
| M108 | A34 — Contrôleur de Domaine RODC par Clinique | Critique | Réduire | Élevée·Critique·Moyen | À décider | À désigner |
| M111 | A35 — Sécurité IT (SOC/EDR/SIEM) | Critique | Réduire | Élevée — Critique — Faible | À décider | À désigner |
| M113 | A35 — Sécurité IT (SOC/EDR/SIEM) | Critique | Réduire | Élevée — Critique — Faible | À décider | À désigner |
| M114 | A36 — Attestation de relecture croisée | Critique | Réduire | Moyenne — Critique — Faible | À décider | À désigner |
| M115 | A36 — Attestation de relecture croisée | Critique | Réduire | Faible — Critique — Faible | À décider | À désigner |
| M120 | A39 — CTI & OSINT | Critique | Réduire | Faible — Critique — Moyenne | À décider | À désigner |
| M130 | Frontière VLAN IoT ↔ Core_Net (routage direct) | Critique | Éviter | Faible - Faible | À décider | À désigner |
| M001 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | Critique | Réduire | Élevé | À décider | À désigner |
| M002 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | Critique | Réduire | Medium | À décider | À désigner |
| M003 | A01 — Dossier Patient Informatisé (DPI) Nexus — Logiciel / Service | Critique | Réduire | Élevé | À décider | À désigner |
| M004 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | Critique | Réduire | Medium | À décider | À désigner |
| M005 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | Critique | Réduire | Élevé | À décider | À désigner |
| M006 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | Critique | Réduire | Medium | À décider | À désigner |
| M007 | A03 — Messagerie Sécurisée de Santé (Mél) — Logiciel / Service | Critique | Réduire | Élevé | À décider | À désigner |
| M008 | A03 — Messagerie Sécurisée de Santé (Mél) — Logiciel / Service | Critique | Réduire | Medium | À décider | À désigner |
| M009 | A03 — Messagerie Sécurisée de Santé (Mél) — Logiciel / Service | Critique | Réduire | Élevé | À décider | À désigner |
| M010 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet | Critique | Réduire | Medium | À décider | À désigner |
| M011 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet | Critique | Réduire | Élevé | À décider | À désigner |
| M012 | A04 — Portail VPN Télétravail & Praticiens Libéraux — Service / Site Internet | Critique | Réduire | Medium | À décider | À désigner |
| M013 | A05 — Webmail de Santé & Accès Externe (OWA) — Service / Site Internet | Critique | Réduire | Élevé → Moyenne | À décider | À désigner |
| M014 | A05 — Webmail de Santé & Accès Externe (OWA) — Service / Site Internet | Critique | Réduire | Critique → Élevé | À décider | À désigner |
| M026 | A08 — Domaine Active Directory (corp.santetech.local) — Logiciel / Infrastructure — Forêt AD unique, 16 contrôleurs de domaine (1 DC/RODC par clinique), pas de MFA systématique VPN As-Is E9E7E5 | Critique | Réduire | Critique | À décider | À désigner |
| M027 | A08 — Domaine Active Directory (corp.santetech.local) — Logiciel / Infrastructure — Forêt AD unique, 16 contrôleurs de domaine (1 DC/RODC par clinique), pas de MFA systématique VPN As-Is E9E7E5 | Critique | Réduire | Critique | À décider | À désigner |
| M037 | A10 — Applications Cloud Hybride (To-Be) — Logiciel / Service — Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11 | Critique | Réduire | Élevé | À décider | À désigner |
| M038 | A10 — Applications Cloud Hybride (To-Be) — Logiciel / Service — Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11 | Critique | Réduire | Élevé | À décider | À désigner |
| M039 | A10 — Applications Cloud Hybride (To-Be) — Logiciel / Service — Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11 | Critique | Réduire | Élevé | À décider | À désigner |
| M040 | A10 — Applications Cloud Hybride (To-Be) — Logiciel / Service — Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11 | Critique | Réduire + Transférer | Élevé | À décider | À désigner |
| M041 | A10 — Applications Cloud Hybride (To-Be) — Logiciel / Service — Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11 | Critique | Éviter | Critique | À décider | À désigner |
| M042 | A10 — Applications Cloud Hybride (To-Be) — Logiciel / Service — Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique E9E5E11 | Critique | Réduire | Élevé | À décider | À désigner |
| M043 | A11 — Fournisseur Cloud HDS | Critique | Éviter | Critique | À décider | À désigner |
| M044 | A11 — Fournisseur Cloud HDS | Critique | Réduire + Transférer | Élevé | À décider | À désigner |
| M045 | A12 — Parc IoT Médical | Critique | Accepter | Critique | À décider | À désigner |
| M046 | A12 — Parc IoT Médical | Critique | Réduire + Éviter | Élevé | À décider | À désigner |
| M047 | A13 — Segmentation Réseau VLAN/NAC | Critique | Éviter | Élevé | À décider | À désigner |
| M048 | A14 — Wi-Fi Invités/Patients | Critique | Réduire | Élevé | À décider | À désigner |
| M049 | A14 — Wi-Fi Invités/Patients | Critique | Réduire | Élevé | À décider | À désigner |
| M050 | A15 — API SaaS / APIs Télémedecine | Critique | Réduire | Élevé | À décider | À désigner |
| M052 | A16 — Domaine hospitalier — Site | Critique | Réduire | Élevé | À décider | À désigner |
| M057 | A18 — Application métier — DPI Progiciel Nexus | Critique | Réduire | Élevé | À décider | À désigner |
| M059 | A18 — Application métier — DPI Progiciel Nexus | Critique | Réduire | Élevé | À décider | À désigner |
| M063 | A20 — Matériel IoT — Dispositifs Médicaux Connectés | Critique | Réduire | Élevé | À décider | À désigner |
| M072 | A22 — Infrastructure sécurité — Micro-segmentation VLAN/NAC — Architecture cible pour isoler poste clinique compromis (VLAN IoT/Biomedical 10.1.30.0/24 non cloisonné actuellement) [E146,E150,FichedAuditTechnique-ÉtatdesLieuxSanteTechAs-Is.pdf.md,E205] | Critique | Réduire | Critique | À décider | À désigner |
| M073 | A23 — Application/Rôle — IdP Gestion Identités (TO-BE) — Déploiement cible IdP centralisé (Entra ID/Keycloak) avec MFA FIDO2/Carte CPS [E146] | Critique | Réduire | Risque moyen | À décider | À désigner |
| M076 | A23 — Application/Rôle — IdP Gestion Identités (TO-BE) — Déploiement cible IdP centralisé (Entra ID/Keycloak) avec MFA FIDO2/Carte CPS [E146] | Critique | Réduire | Risque critique | À décider | À désigner |
| M077 | A24 — API Télémédecine Cloud Hybride — Logiciel / Service — Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146] | Critique | Réduire | Risque critique | À décider | À désigner |
| M078 | A24 — API Télémédecine Cloud Hybride — Logiciel / Service — Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146] | Critique | Réduire | Risque critique | À décider | À désigner |
| M079 | A24 — API Télémédecine Cloud Hybride — Logiciel / Service — Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146] | Critique | Réduire | Risque critique | À décider | À désigner |
| M080 | A24 — API Télémédecine Cloud Hybride — Logiciel / Service — Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146] | Critique | Réduire | Risque critique | À décider | À désigner |
| M081 | A24 — API Télémédecine Cloud Hybride — Logiciel / Service — Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146] | Critique | Réduire | Risque critique | À décider | À désigner |
| M082 | A24 — API Télémédecine Cloud Hybride — Logiciel / Service — Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146] | Critique | Réduire | Risque critique | À décider | À désigner |
| M083 | A25 — Plateforme DPI Nexus (Dossier Patient Informatisé) — Logiciel / Service — Hébergé sur ferme Citrix/RDS (Siège Rennes) [E139] | Critique | Réduire | Risque critique | À décider | À désigner |
| M084 | A25 — Plateforme DPI Nexus (Dossier Patient Informatisé) — Logiciel / Service — Hébergé sur ferme Citrix/RDS (Siège Rennes) [E139] | Critique | Réduire | Risque critique | À décider | À désigner |
| M085 | A25 — Plateforme DPI Nexus (Dossier Patient Informatisé) — Logiciel / Service — Hébergé sur ferme Citrix/RDS (Siège Rennes) [E139] | Critique | Réduire | Faible : logs exposés corrigés via journalisation chiffrée + page 404 fixée | À décider | À désigner |
| M088 | A26 — Parc IoT Médical | Critique | Réduire | Moyen : VLAN IoT médical isolé de production + routage restreint vers automates [E140] | À décider | À désigner |
| M094 | A28 — Postes legacy | Critique | Réduire | Faible : SMBv1 bloqué réseau local + postes XP en mode sandbox avec isolation [E203] | À décider | À désigner |
| M098 | A30 — Active Directory | Critique | Réduire | Élevée·Critique·Faible | À décider | À désigner |
| M099 | A31 — Base de Données PACS/RIS Imagerie | Critique | Réduire | Élevée·Critique·Faible | À décider | À désigner |
| M103 | A32 — Messagerie Exchange 2016 OWA Webmail | Critique | Réduire | Élevée·Élevé·Faible | À décider | À désigner |
| M106 | A33 — Portail VPN FortiGate | Critique | Réduire | Élevée·Critique·Faible | À décider | À désigner |
| M109 | A34 — Contrôleur de Domaine RODC par Clinique | Critique | Réduire | Moyenne — Élevé — Moyen | À décider | À désigner |
| M123 | Frontière Internet ↔ VPN_Gateway (FortiGate) | Critique | Réduire | Faible - Moyen | À décider | À désigner |
| M134 | Frontière Cloud_HDS ↔ API Gateway (hybride To-Be) | Critique | Réduire | Élevé (menace persistante jusqu'à migration complète de l'API Gateway sécurisée dans Cloud HDS) | À décider | À désigner |
| M055 | A17 — Infrastructure réseau — Active Directory | Élevé | Réduire | Élevé | À décider | À désigner |
| M015 | A05 — Webmail de Santé & Accès Externe (OWA) — Service / Site Internet | Élevé | Réduire | Élevé → Moyen | À décider | À désigner |
| M016 | A02 — PACS/RIS (Archivage & Imagerie) — Logiciel / Service | Élevé | Réduire | Élevé → Moyen | À décider | À désigner |
| M017 | A06 — Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants extérieurs E7E5 | Élevé | Réduire | Élevé → Moyen | À décider | À désigner |
| M018 | A06 — Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants extérieurs E7E5 | Élevé | Réduire | Élevé → Moyen | À décider | À désigner |
| M019 | A06 — Extranet Partenaires / Médecins Libéraux — Service / Site Internet — extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants extérieurs E7E5 | Élevé | Réduire | Élevé → Faible-Moyen | À décider | À désigner |
| M021 | A07 — Sites Web Cliniques (12 sites) — Site Internet / Prestataire — Hébergés prestataire tiers WordPress non durci, sans liaison SI interne mais cibles défacement/phishing rebond E7E5 | Élevé | Éviter | Élevé → Faible | À décider | À désigner |
| M023 | A07 — Sites Web Cliniques (12 sites) — Site Internet / Prestataire — Hébergés prestataire tiers WordPress non durci, sans liaison SI interne mais cibles défacement/phishing rebond E7E5 | Élevé | Réduire | Moyen → Faible-Moyen | À décider | À désigner |
| M028 | A08 — Domaine Active Directory (corp.santetech.local) — Logiciel / Infrastructure — Forêt AD unique, 16 contrôleurs de domaine (1 DC/RODC par clinique), pas de MFA systématique VPN As-Is E9E7E5 | Élevé | Réduire | Élevé | À décider | À désigner |
| M029 | A08 — Domaine Active Directory (corp.santetech.local) — Logiciel / Infrastructure — Forêt AD unique, 16 contrôleurs de domaine (1 DC/RODC par clinique), pas de MFA systématique VPN As-Is E9E7E5 | Élevé | Réduire | Élevé | À décider | À désigner |
| M056 | A17 — Infrastructure réseau — Active Directory | Élevé | Réduire | Élevé | À décider | À désigner |
| M061 | A19 — Donnée/Structure — Données Patients (DPI) | Élevé | Réduire | Moyen | À décider | À désigner |
| M064 | A20 — Matériel IoT — Dispositifs Médicaux Connectés | Élevé | Réduire | Élevé | À décider | À désigner |
| M066 | A20 — Matériel IoT — Dispositifs Médicaux Connectés | Élevé | Réduire | Élevé | À décider | À désigner |
| M074 | A23 — Application/Rôle — IdP Gestion Identités (TO-BE) — Déploiement cible IdP centralisé (Entra ID/Keycloak) avec MFA FIDO2/Carte CPS [E146] | Élevé | Réduire | Risque élevé | À décider | À désigner |
| M075 | A23 — Application/Rôle — IdP Gestion Identités (TO-BE) — Déploiement cible IdP centralisé (Entra ID/Keycloak) avec MFA FIDO2/Carte CPS [E146] | Élevé | Réduire | Risque moyen | À décider | À désigner |
| M086 | A25 — Plateforme DPI Nexus (Dossier Patient Informatisé) — Logiciel / Service — Hébergé sur ferme Citrix/RDS (Siège Rennes) [E139] | Élevé | Réduire | Faible : interface admin durcie sans authentification sans MFA + CSP mis [E146] | À décider | À désigner |
| M092 | A27 — Ferme Citrix/RDS | Élevé | Réduire | Faible : micro-segmentation déployée sur ferme Citrix/RDS + lateralité bloquée [E146] | À décider | À désigner |
| M096 | A29 — MPLS Hub & Spoke | Élevé | Réduire | Très Faible : trafic inter-clinique crypté TLS 1.3 + gateway WAF inspectant réplication [E150] | À décider | À désigner |
| M100 | A31 — Base de Données PACS/RIS Imagerie | Élevé | Réduire | Élevée·Élevé·Faible | À décider | À désigner |
| M110 | A34 — Contrôleur de Domaine RODC par Clinique | Élevé | Réduire | Faible — Moyen — Faible | À décider | À désigner |
| M112 | A35 — Sécurité IT (SOC/EDR/SIEM) | Élevé | Réduire | Moyenne — Moyen — Faible | À décider | À désigner |
| M116 | A37 — CISO / Lead GRC | Élevé | Réduire | Faible — Moyen — Faible | À décider | À désigner |
| M124 | Frontière Internet ↔ Portail OWA (Exchange 2016 DMZ) | Élevé | Réduire | Moyen - Moyen | À décider | À désigner |
| M127 | Frontière Réseau Interne ↔ Backbone MPLS (sans micro-segmentation) | Élevé | Réduire | Faible - Faible | À décider | À désigner |
| M128 | Frontière Réseau Interne ↔ Backbones AD (Forêt unique) | Élevé | Réduire | Faible - Moyen | À décider | À désigner |
| M129 | Frontière Réseau Interne ↔ Citrix Farm (DPI Nexus) | Élevé | Réduire | Faible - Moyen | À décider | À désigner |
| M135 | Frontière Cloud_HDS ↔ API Gateway (hybride To-Be) | Élevé | Réduire | Élevé (fuites possibles via endpoints API non signés réduites mais signature intégration progressive) | À décider | À désigner |
| M025 | A07 — Sites Web Cliniques (12 sites) — Site Internet / Prestataire — Hébergés prestataire tiers WordPress non durci, sans liaison SI interne mais cibles défacement/phishing rebond E7E5 | Élevé | Réduire | Élevé | À décider | À désigner |
| M034 | A09 — Contrôleurs de Domaine AD (16 unités) — Matériel / Infrastructure — 1 DC complet + 1 RODC par clinique (12 sites), gestion identités centralisée, patching potentiellement hétérogène E9E5 | Élevé | Réduire | Élevé | À décider | À désigner |
| M051 | A15 — API SaaS / APIs Télémedecine | Élevé | Réduire | Élevé | À décider | À désigner |
| M122 | Frontière Internet ↔ VPN_Gateway (FortiGate) | Élevé | Réduire | Faible - Faible | À décider | À désigner |
| M125 | Frontière DMZ ↔ WAF optionnel (non déployé As-Is) | Élevé | Réduire | Faible - Faible | À décider | À désigner |
| M132 | Frontière Wi-Fi Invités ↔ Internet (sans SSL filtering) | Élevé | Réduire | Moyen - Faible | À décider | À désigner |
| M133 | Frontière Wi-Fi Invités ↔ Internet (sans SSL filtering) | Élevé | Réduire | Moyen (risque d'interception passif réduit mais non nul pour connexions sans HTTPS résiduel) | À décider | À désigner |

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

