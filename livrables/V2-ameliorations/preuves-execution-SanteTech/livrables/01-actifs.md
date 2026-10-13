# Inventaire des actifs (étape 1)

| ID | Actif | Type | Description, périmètre et valeur | Sensibilité | Preuve source |
|---|---|---|---|---|---|
| A01 | Dossier Patient Informatisé (DPI) Nexus | Logiciel / Service | 185 serveurs (65 physiques, 120 virtuels), Progiciel Nexus version legacy sur ferme Citrix/RDS, accès soignants RDP interne, valeur métier critique pour le traitement administratif et médical [E203] | Critique | [E203][E5][E7] |
| A02 | PACS/RIS (Archivage & Imagerie) | Logiciel / Service | Stockage DICOM/SMBv1 sur baies SAN locales vieillissantes, caches DICOM/PACS restants en local des cliniques, protocoles SMBv1 pour compatibilité scanners anciens [E203][E7] | Critique | [E203][E5][E7] |
| A03 | Messagerie Sécurisée de Santé (Mél) | Logiciel / Service | Serveur Exchange 2016 exposé DMZ, Webmail OWA webmail.santetech-sante.fr, vulnérable ProxyShell/Spraying si non patché [E7][E5] | Sensible | [E7][E203][E5] |
| A04 | Portail VPN Télétravail & Praticiens Libéraux | Service / Site Internet | vpn.santetech-sante.fr (Passerelle FortiGate/FortiSSL), Login/Mot de passe AD sans MFA sur 60% des comptes, authentification simple [E7][E5] | Sensible | [E7][E203][E5] |
| A05 | Webmail de Santé & Accès Externe (OWA) | Service / Site Internet | webmail.santetech-sante.fr (Exchange 2016 DMZ), non filtré SSL si vulnérabilités, campagnes Spraying/ProxyShell potentielles [E7][E5] | Sensible | [E7][E203][E5] |
| A06 | Extranet Partenaires / Médecins Libéraux | Service / Site Internet | extranet.santetech-sante.fr (accès résultats médicaux), authentification par certificat faible, accès médecins traitants extérieurs [E7][E5] | Sensible | [E7][E203][E5] |
| A07 | Sites Web Cliniques (12 sites) | Site Internet / Prestataire | Hébergés prestataire tiers WordPress non durci, sans liaison SI interne mais cibles défacement/phishing rebond [E7][E5] | Publique | [E7][E203][E5] |
| A08 | Domaine Active Directory (corp.santetech.local) | Logiciel / Infrastructure | Forêt AD unique, 16 contrôleurs de domaine (1 DC/RODC par clinique), pas de MFA systématique VPN As-Is [E9][E7][E5] | Sensible | [E9][E7][E203] |
| A09 | Contrôleurs de Domaine AD (16 unités) | Matériel / Infrastructure | 1 DC complet + 1 RODC par clinique (12 sites), gestion identités centralisée, patching potentiellement hétérogène [E9][E5] | Critique | [E9][E7][E203] |
| A10 | Applications Cloud Hybride (To-Be) | Logiciel / Service | Migration DPI Nexus vers Cloud HDS, télémédecine et portail patient en Cloud, API Gateway sécurisée nouvelle brique [E9][E5][E11] | Sensible | [E9][E7][E203] |
| A11 | Fournisseur Cloud HDS (Prestataire) | Prestataire | Certification HDS obligatoire pour hébergeur données de santé, analyse exposition Cloud Act, aucun fournisseur imposé [E9][E7][E5] | Sensible | [E9][E7][E203] |
| A12 | Parc IoT Médical (4 000 dispositifs) | Matériel | ~350 par site (pompes perfusion, moniteurs, scanners), OS non patchables partie parc, interdictions accès Internet direct [E9][E11] | Critique | [E9][E7][E203] |
| A13 | Segmentation Réseau VLAN/NAC IoT (Micro-segmentation) | Infrastructure / Service | Micro-segmentation VLAN/NAC pour iso logique automate compromis, 10.1.30.0/24 VLAN IoT/Biomédical non cloisonné routage direct [E9][E203] | Sensible | [E9][E7][E203] |
| A14 | Wi-Fi Invités/Patients (VLAN 10.1.40.0/24) | Infrastructure / Service | 10.1.40.0/24 VLAN sortant Internet direct sans filtrage SSL, cibles défacement/phishing rebond potentiel [E7][E5][E203] | Publique | [E9][E203][E7] |
| A15 | API SaaS / APIs Télémedecine (Nouvelle) | Logiciel / Service | Exposition API Gateway Cloud Hybride vers brique télémédecine sécurisée, signature images Docker/SBOM à intégrer [E11][E13] | Critique | [E11][E7][E203] |
| A16 | Domaine hospitalier | Site | ~4500 collaborateurs sur 12 cliniques (Rennes, Nantes, Brest, Le Mans, Angers, Tours + 6 proximité), périmètre: établissement physique et ses locaux informatiques, valeur : coût de remplacement > 50 M€ (construction+installation) [E142] | Publique | Présentation_du_Projet_d_Étude_-_M2_CYBE.pdf.md,E142 [E142] |
| A17 | Infrastructure réseau | Active Directory | Forêt unique corp.santetech.local, 16 DC/RODC (1 par clinique), non encore cloisonné [E140] | Interne,Sensible | FAQ___Complément_de_Cadrage_-_SanteTech__Bloc_1_.pdf.md,E140,Fiche_d_Audit_Technique_-_État_des_Lieux_SanteTech__As-Is_.pdf.md,E205 [E140] |
| A18 | Application métier | DPI Progiciel Nexus | Dossier Patient Informatisé hébergé sur ferme Citrix/RDS Siège de Rennes (As-Is) [E146] | Sensible,Critique | FAQ___Complément_de_Cadrage_-_SanteTech__Bloc_1_.pdf.md,E146 [E140] [E205] [E231] |
| A19 | Donnée/Structure | Données Patients (DPI) | 150 000 dossiers patients actifs, hébergés sur ferme Citrix/RDS Rennes [E223] | Critique | Présentation_du_Projet_d_Étude_-_M2_CYBE.pdf.md,E223 |
| A20 | Matériel IoT | Dispositifs Médicaux Connectés | ~4 000 unités (~350/site : pompes perfusion, moniteurs multiparamétriques, scanners) OS non patchables [E146,E229] | Critique | FAQ___Complément_de_Cadrage_-_SanteTech__Bloc_1_.pdf.md,E146,Fiche_d_Audit_Technique_-_État_des_Lieux_SanteTech__As-Is_.pdf.md,E205 |
| A21 | Infrastructure Cloud | Hébergeur Cloud Hybride | HDS certifié, choix entre Scaleway/OVHcloud/Azure (pas d'imposition) [E142] | Sensible,Sensible | FAQ___Complément_de_Cadrage_-_SanteTech__Bloc_1_.pdf.md,E146,Presentation_du_Projet_d_Étude_-_M2_CYBE.pdf.md |
| A22 | Infrastructure sécurité | Micro-segmentation VLAN/NAC | Architecture cible pour isoler poste clinique compromis (VLAN IoT/Biomedical 10.1.30.0/24 non cloisonné actuellement) [E146,E150,Fiche_d_Audit_Technique_-_État_des_Lieux_SanteTech__As-Is_.pdf.md,E205] | Interne,Sensible | FAQ___Complément_de_Cadrage_-_SanteTech__Bloc_1_.pdf.md,E146,Presentation_du_Projet_d_Étude_-_M2_CYBE.pdf.md,E231 |
| A23 | Application/Rôle | IdP Gestion Identités (TO-BE) | Déploiement cible IdP centralisé (Entra ID/Keycloak) avec MFA FIDO2/Carte CPS [E146] | Interne,Sensible | FAQ___Complément_de_Cadrage_-_SanteTech__Bloc_1_.pdf.md,E146 |
| A24 | API Télémédecine Cloud Hybride | Logiciel / Service | Interface REST/HTTPS sécurisée via API Gateway dans Cloud Hybride [E146] | Critique | [E146] |
| A25 | Plateforme DPI Nexus (Dossier Patient Informatisé) | Logiciel / Service | Hébergé sur ferme Citrix/RDS (Siège Rennes) [E139] | Critique | [E139] |
| A26 | Parc IoT Médical (~4000 dispositifs) | Matériel / Donnée | Capteurs, pompes à perfusion, moniteurs, scanners [E149] | Sensible | [E149] |
| A27 | Ferme Citrix/RDS au Siège Rennes | Matériel / Logiciel | Infrastructure legacy avec 65 serveurs physiques [E139] | Critique | [E139] |
| A28 | Postes informatiques legacy (~5% Windows 7/XP Embedded) | Matériel / Logiciel | 200 postes irréductibles pour imagerie médicale [E139] | Sensible | [E139] |
| A29 | Infrastructure MPLS Hub & Spoke | Matériel / Réseaux | Backbone interconnecté avec micro-segmentation absente [E139] | Critique | [E139] |
| A30 | Forêt Active Directory corp.santetech.local | Logiciel / Donnée | 16 contrôleurs de domaine (1 DC/RODC par clinique) [E139] | Sensible | [E139] |
| A31 | Base de Données PACS/RIS Imagerie | Donnée / Logiciel | Stockage images radiologiques dans cliniques [E140] | Critique | [E140] |
| A32 | Messagerie Exchange 2016 OWA Webmail | Logiciel / Service | Accès via webmail.santetech-sante.fr [E139] | Sensible | [E139] |
| A33 | Portail VPN FortiGate vpn.santetech-sante.fr | Logiciel / Service | Accès sécurisé avec MFA non systématique [E139] | Critique | [E139] |
| A34 | Contrôleur de Domaine RODC par Clinique | Matériel / Logiciel | 12 contrôleurs de domaine (1 par clinique) [E139] | Sensible | [E139] |
| A35 | Sécurité IT (SOC/EDR/SIEM) | Service | Absente actuellement [E140] | Critique | [E140] |
| A36 | Attestation de relecture croisée | Rôle / Organisation | Signée par 4 membres de l'équipe [E140] | Interne | [E140] |
| A37 | CISO / Lead GRC | Rôle / Organisation | Chef de projet sécurité [E224] | Critique | [E224] |
| A38 | Blue Team & SOC | Service | Analyse de menace non implémentée [E140] | Critique | [E140] |
| A39 | CTI & OSINT | Service | Analyse de menace non implémentée [E140] | Critique | [E140] |
