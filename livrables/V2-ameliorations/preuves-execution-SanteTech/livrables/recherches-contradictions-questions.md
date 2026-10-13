# Recherches, contradictions et questions ouvertes

31 besoins d'information examinés : **4 connus**, **8 partiels**, **19 non documentés**.

> « Non documenté » signifie que **les documents fournis n'en parlent pas**. Cela ne prouve pas que la mesure n'existe pas : c'est une question à poser à l'entreprise.

## Ce que nous savons

- **Quelles normes ou certifications (ISO 27001, etc.) sont obtenues ou visées ?** Les normes et certifications visées sont NIS 2, RGPD, HDS (Hébergeur de Données de Santé) et ISO 27001. _(à valider : Les deux vérificateurs divergent : relire les extraits cités.)_
  - preuve (Présentation_du_Projet_d_Étude_-_M2_CYBE) : «    Gestion des Risques                      Conformité Légale                          Résilience Métier
   Scoring CVSS/CVE & révision PSSI.                Audits NIS 2, RGPD, HDS / ISO 27001.        »
  - preuve (Présentation_du_Projet_d_Étude_-_M2_CYBE) : « ## Page 1

SUP DE VINCI  M2 CYBERSÉCURITÉ 20262027
Projet SECUCLOUDHEALTH

Cahier des charges, cadrage opérationnel et livrables par blocs de compétences.

## Page 2

CONTEXTE & ENJEUX
Mise en sit »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « Absence initiale de SOC, d'EDR et de SIEM centralisé. Le projet doit répondre aux exigences de la directive NIS 2, du RGPD et de la certification HDS. »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « Aucun fournisseur n'est imposé. Contrainte impérative : certification HDS (Hébergeur de Données de Santé) et analyse de l'exposition au Cloud Act. »
- **Quels sont les sites de l'entreprise et leur rôle ?** L'entreprise compte 12 établissements : 2 Grands Centres Hospitaliers (Rennes, Nantes), 4 Cliniques Moyennes (Brest, Le Mans, Angers, Tours) et 6 Cliniques de Proximité / Chirurgie.
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : «  4      Répartition des 12                • 2 Grands Centres Hospitaliers (Rennes +
        établissements              Nantes) : ~500 lits chacun, 1 000 collaborateurs/site,
                          »
- **Combien de postes de travail existent et sont-ils chiffrés ?** Il existe 3 200 postes informatiques, dont 700 PC portables chiffrés par BitLocker et 2 500 postes fixes et chariots de soins.
  - preuve (Fiche_d_Audit_Technique_-_État_des_Lieux) : «              messagerie interne hybride Exchange 2016 (Non totalement durci contre les
              attaques par usurpation).

## Page 3

4. Postes Clients & Flotte IoT Médical

    ●​ Parc Utilisate »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « ● Volumétrie : 185 serveurs (65 physiques, 120 virtuels sous VMware ESXi/Hyper-V) et 3 200 postes informatiques (dont ~5% de postes irréductibles sous Windows 7 / XP Embedded pour l'imagerie). »
- **L'authentification multifacteur (MFA) est-elle en place, pour quels comptes ?** Actuellement, il n'y a pas de MFA systématique sur le VPN, avec un simple login/mot de passe sans MFA sur 60% des comptes.
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « • As-Is : Active Directory On-Premise unique, pas de MFA systématique sur le VPN. »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : «                           MFA systématique sur le VPN.

                                                   • To-Be : Déploiement d'un IdP centralisé (Entra ID /
                                     Ke »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « ● Exposition & Accès : Portail VPN FortiGate (vpn.santetech-sante.fr) avec simple login/mot de passe (sans MFA sur 60% des comptes) et Webmail Exchange OWA (webmail.santetech-sante.fr). »

## Ce que nous savons en partie

- **Existe-t-il une politique de sécurité (PSSI) et de quelle version ?** Le document mentionne une « révision PSSI » dans le cadre de la gestion des risques, mais ne précise pas l'existence d'une politique actuelle ni sa version. _(à valider : Information partielle. Il manque : La version actuelle de la PSSI et la confirmation de son existence formelle.. Les deux vérificateurs divergent : relire les extraits cités.)_
  - preuve (Présentation_du_Projet_d_Étude_-_M2_CYBE) : «    Gestion des Risques                      Conformité Légale                          Résilience Métier
   Scoring CVSS/CVE & révision PSSI.                Audits NIS 2, RGPD, HDS / ISO 27001.        »
  - **Manque** : La version actuelle de la PSSI et la confirmation de son existence formelle.
- **Quelles sont les applications critiques et qui en est propriétaire ?** Les applications critiques sont le Progiciel Nexus (Dossier Patient Informatisé), PACS/RIS pour l'imagerie, la messagerie interne Exchange 2016 et une nouvelle brique de télémédecine. _(à valider : La réponse proposée n'est pas soutenue par les preuves citées : relire les extraits avant de s'y fier.)_
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « ● Applications Métier : Progiciel Nexus (Dossier Patient Informatisé), PACS/RIS pour l'imagerie, et messagerie interne Exchange 2016. »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : «       micro-segmentation : un poste compromis dans une clinique peut communiquer en IP
        directe avec tout le réseau.
    ●​ Annuaire : Forêt Active Directory unique (corp.santetech.local) avec  »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « Applications Métier : Progiciel Nexus (Dossier Patient Informatisé), PACS/RIS pour l'imagerie, et messagerie interne Exchange 2016. »
  - **Manque** : L'identité précise du propriétaire (entité ou service responsable) de ces applications n'est pas mentionnée dans les documents.
- **Quels services sont hébergés en SaaS ou dans le cloud, chez quels fournisseurs ?** Le DPI Nexus, la télémédecine, le portail patient et des API SaaS migrent vers un Cloud Hybride HDS. Aucun fournisseur n'est imposé (ex: Scaleway, OVHcloud, Azure). _(à valider : Information partielle. Il manque : La confirmation du fournisseur final choisi parmi les options citées.. Les deux vérificateurs divergent : relire les extraits cités.)_
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « HDS. Seuls les serveurs d'impression et les caches
DICOM/PACS restent en local dans les cliniques. |
| 6 | Fournisseur Cloud &
Souveraineté | Aucun fournisseur n'est imposé. Contrainte
impérative : ce »
  - preuve (Présentation_du_Projet_d_Étude_-_M2_CYBE) : « Transformation : Migration vers un Cloud hybride,
                                                       Mission de l'équipe
microservices, API SaaS et IoT médical. »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : «                                                    • To-Be (Cloud Hybride) : Migration du DPI Nexus,
                                de la télémédecine et du portail patient vers un Cloud
             »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « (a) Hébergeur Cloud HDS (ex: Scaleway HDS vs OVHcloud vs Azure HDS) »
  - **Manque** : La confirmation du fournisseur final choisi parmi les options citées.
- **Qui dispose d'un accès à distance (VPN, télémaintenance, prestataires) ?** Le portail VPN (vpn.santetech-sante.fr) est utilisé pour le télétravail et les praticiens libéraux. Un portail extranet est dédié aux médecins traitants extérieurs. _(à valider : Information partielle. Il manque : La liste précise des prestataires ayant un accès à distance n'est pas mentionnée dans les documents..)_
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « ● Exposition & Accès : Portail VPN FortiGate (vpn.santetech-sante.fr) avec simple login/mot de passe (sans MFA sur 60% des comptes) et Webmail Exchange OWA (webmail.santetech-sante.fr). »
  - preuve (Fiche_d_Audit_Technique_-_État_des_Lieux) : « 5. Services Exposés sur Internet & Accès Distants

    ●​  Portail VPN Télétravail & Praticiens Libéraux :
           ○​ URL : vpn.santetech-sante.fr (Passerelle FortiGate / FortiSSL).
           ○​   »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « Exposition & Accès : Portail VPN FortiGate (vpn.santetech-sante.fr) avec simple login/mot de passe »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : «       micro-segmentation : un poste compromis dans une clinique peut communiquer en IP
        directe avec tout le réseau.
    ●​ Annuaire : Forêt Active Directory unique (corp.santetech.local) avec  »
  - **Manque** : La liste précise des prestataires ayant un accès à distance n'est pas mentionnée dans les documents.
- **Le réseau est-il segmenté et quels pare-feu protègent les sites ?** Le réseau n'est pas micro-segmenté : un poste compromis peut communiquer en IP directe avec tout le réseau. Les sites sont protégés par une passerelle FortiGate / FortiSSL. _(à valider : La réponse proposée n'est pas soutenue par les preuves citées : relire les extraits avant de s'y fier.)_
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « ● Réseau (Hub & Spoke) : Interconnexion MPLS centralisée par le siège. »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « Aucune micro-segmentation : un poste compromis dans une clinique peut communiquer en IP directe avec tout le réseau. »
  - preuve (Fiche_d_Audit_Technique_-_État_des_Lieux) : « 5. Services Exposés sur Internet & Accès Distants

    ●​  Portail VPN Télétravail & Praticiens Libéraux :
           ○​ URL : vpn.santetech-sante.fr (Passerelle FortiGate / FortiSSL).
           ○​   »
- **Quels sont les liens Internet et existe-t-il un lien de secours ?** L'infrastructure actuelle est 100% On-Premise avec des serveurs locaux de secours dans les cliniques. _(à valider : Information partielle. Il manque : La liste exhaustive des liens Internet spécifiques et la confirmation de l'existence d'un lien de secours dédié à la connexion Internet..)_
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « ● Infrastructure Actuelle : 100% On-Premise / Legacy avec dette technique avérée (ferme Citrix/RDS au Siège, serveurs locaux de secours dans les cliniques). »
  - **Manque** : La liste exhaustive des liens Internet spécifiques et la confirmation de l'existence d'un lien de secours dédié à la connexion Internet.
- **Quels équipements sont obsolètes ou hors support constructeur ?** Le parc informatique contient environ 5% de postes sous Windows 7 / Windows XP Embedded pilotant de vieux automates d'imagerie et des injecteurs de produits de contraste. _(à valider : Information partielle. Il manque : La liste exhaustive des équipements spécifiques dont le support constructeur est officiellement expiré..)_
  - preuve (Fiche_d_Audit_Technique_-_État_des_Lieux) : «              messagerie interne hybride Exchange 2016 (Non totalement durci contre les
              attaques par usurpation).

## Page 3

4. Postes Clients & Flotte IoT Médical

    ●​ Parc Utilisate »
  - preuve (Fiche_d_Audit_Technique_-_État_des_Lieux) : « Applications Clés (Hébergées en local / DC Siège) : »
  - **Manque** : La liste exhaustive des équipements spécifiques dont le support constructeur est officiellement expiré.
- **Quelles données personnelles sont traitées (clients, salariés, géolocalisation) ?** Le groupe traite 150 000 dossiers patients actifs. Il gère les données de 4 500 collaborateurs (médecins, infirmiers, administratifs) et utilise des dispositifs IoT médicaux connectés. _(à valider : Information partielle. Il manque : Précisions sur les données de géolocalisation spécifiques et le détail des données personnelles des clients (patients) au-delà des dossiers actifs..)_
  - preuve (Présentation_du_Projet_d_Étude_-_M2_CYBE) : « ## Page 1

SUP DE VINCI  M2 CYBERSÉCURITÉ 20262027
Projet SECUCLOUDHEALTH

Cahier des charges, cadrage opérationnel et livrables par blocs de compétences.

## Page 2

CONTEXTE & ENJEUX
Mise en sit »
  - preuve (Fiche_d_Audit_Technique_-_État_des_Lieux) : «              messagerie interne hybride Exchange 2016 (Non totalement durci contre les
              attaques par usurpation).

## Page 3

4. Postes Clients & Flotte IoT Médical

    ●​ Parc Utilisate »
  - preuve (FAQ___Complément_de_Cadrage_-_SanteTech_) : « HDS. Seuls les serveurs d'impression et les caches
DICOM/PACS restent en local dans les cliniques. |
| 6 | Fournisseur Cloud &
Souveraineté | Aucun fournisseur n'est imposé. Contrainte
impérative : ce »
  - **Manque** : Précisions sur les données de géolocalisation spécifiques et le détail des données personnelles des clients (patients) au-delà des dossiers actifs.

## Ce que nous ignorons encore (questions à poser)

- [Gouvernance] **Qui est le RSSI et est-il indépendant du DSI ?** Une description de l'organisation interne précisant l'identité du RSSI et son rapport hiérarchique ou fonctionnel avec le DSI.
- [Gouvernance] **À quelle fréquence se réunit le comité de sécurité ?** Une mention de la fréquence de réunion du comité de sécurité dans les documents fournis.
- [Continuité] **Comment sont réalisées les sauvegardes et où sont-elles stockées ?** Une description technique des procédures de sauvegarde et de leur localisation (serveurs de backup, cloud, ou supports physiques).
- [Continuité] **Quand a eu lieu la dernière restauration de sauvegarde réussie ?** Un document technique ou un journal de logs indiquant la date de la dernière restauration de sauvegarde réussie.
- [Continuité] **Existe-t-il un plan de reprise d'activité, quand a-t-il été testé, quel est le site de repli ?** Un document détaillant le Plan de Reprise d'Activité (PRA), la date du dernier test et l'emplacement géographique ou technique du site de repli.
- [Accès] **Les comptes d'administration sont-ils nominatifs ou partagés ?** Une information précisant si les comptes d'administration sont nominatifs ou partagés.
- [Accès] **Comment et sous quel délai les comptes des personnes parties sont-ils désactivés ?** Les documents fournis ne mentionnent aucune procédure ni délai de désactivation des comptes des personnes parties.
- [Exploitation] **Les journaux (logs) sont-ils centralisés et analysés, qui reçoit les alertes ?** Information sur l'existence d'un système de centralisation des logs, les outils d'analyse utilisés et l'identité des destinataires des alertes.
- [Exploitation] **Comment sont gérés les correctifs de sécurité et les vulnérabilités ?** Une procédure ou un document décrivant le processus de gestion des correctifs (patch management) et le suivi des vulnérabilités.
- [Exploitation] **Quels incidents de sécurité ont eu lieu récemment ?** Un document ou un rapport listant les incidents de sécurité récents survenus au sein du groupe SanteTech.
- [Exploitation] **Un test d'intrusion ou un audit technique externe a-t-il été réalisé ?** Un document confirmant la réalisation d'un test d'intrusion ou d'un audit technique externe spécifique.
- [Données] **Existe-t-il un registre des traitements RGPD et est-il complet ?** Un document confirmant l'existence et l'exhaustivité du registre des traitements RGPD.
- [Données] **Qui est le délégué à la protection des données (DPO) ?** Le nom ou l'identité du délégué à la protection des données (DPO) n'est mentionné dans aucun des documents fournis.
- [Données] **Comment une violation de données est-elle notifiée à la CNIL ?** Une procédure ou un document précisant les modalités de notification des violations de données à la CNIL.
- [Fournisseurs] **Quels prestataires ont accès au système d'information et avec quelles clauses de sécurité ?** La liste des prestataires tiers ayant accès au système d'information et les clauses de sécurité spécifiques qui leur sont appliquées.
- [Fournisseurs] **L'entreprise dispose-t-elle d'une assurance cyber ?** Une information sur la présence ou non d'une assurance cyber dans les documents fournis.
- [Humain] **Quelle sensibilisation à la sécurité a été faite et quand ?** Aucun document ne mentionne de sensibilisation à la sécurité effectuée ou de date précise.
- [Humain] **Quel est le processus d'arrivée et de départ des collaborateurs ?** Un document décrivant les procédures RH ou les processus opérationnels d'onboarding et d'offboarding des collaborateurs.
- [Sécurité physique] **Comment sont protégées les salles serveurs (accès, incendie, énergie) ?** Informations sur les mesures de protection physique (accès, incendie, énergie) des salles serveurs.

## Contradictions entre documents (à valider)

- FAQ___Complément_de_Cadrage_-_SanteTech_ : « Hypothèse retenue : Isolation logique stricte via micro-segmentation VLAN/NAC et interdiction d'accès Internet direct. » **≠** Fiche_d_Audit_Technique_-_État_des_Lieux : « 10.1.30.0/24 : VLAN IoT / Biomédical (Non cloisonné, routage direct vers les automates) » — Le fait (FAQ_Complément_de_Cadrage_-_SanteTech_) stipule une 'Isolation logique stricte via micro-segmentation VLAN/NAC' pour les équipements, alors que le passage [1] (et [2]) indique explicitement q
- Fiche_d_Audit_Technique_-_État_des_Lieux : « 10.1.40.0/24 : VLAN Wi-Fi Invités / Patients (Sortie Internet directe sans filtrage SSL) » **≠** FAQ___Complément_de_Cadrage_-_SanteTech_ : « Hypothèse retenue : Isolation logique stricte via micro-segmentation VLAN/NAC et interdiction d'accès Internet direct. » — Le fait indique que le VLAN Wi-Fi Invités/Patients possède une 'Sortie Internet directe sans filtrage SSL'. À l'inverse, les passages [1] et [2] stipulent une 'interdiction d'accès Internet direct' po

### À relire si le temps le permet (8) — non confirmées par un second avis

- FAQ___Complément_de_Cadrage_-_SanteTech_ : « ● Annuaire : Forêt Active Directory unique (corp.santetech.local) avec 16 contrôleurs de domaine (1 DC/RODC par clinique). » **≠** Fiche_d_Audit_Technique_-_État_des_Lieux : « Domaine racine : hq.corp.santetech.local (Siège - Rennes). » — Le fait indique une forêt Active Directory unique (corp.santetech.local), alors que le passage [3] indique que le domaine racine est hq.corp.santetech.local. Bien que cela puisse être une structure hi
- FAQ___Complément_de_Cadrage_-_SanteTech_ : « • 2 Grands Centres Hospitaliers (Rennes + Nantes) : ~500 lits chacun, 1 000 collaborateurs/site, urgences et imagerie lourde. » **≠** Présentation_du_Projet_d_Étude_-_M2_CYBE : « Périmètre : 12 cliniques, 4500 collaborateurs, 150 000
dossiers patients actifs. » — Le fait indique un périmètre de 2 Grands Centres Hospitaliers avec environ 2 000 collaborateurs au total (1 000 par site). Les passages [1], [2] et [4] indiquent un périmètre de 12 cliniques avec 4 50
- FAQ___Complément_de_Cadrage_-_SanteTech_ : « • 4 Cliniques Moyennes (Brest, Le Mans, Angers, Tours) : ~200 lits, 400 collaborateurs/site. » **≠** Présentation_du_Projet_d_Étude_-_M2_CYBE : « Périmètre : 12 cliniques, 4500 collaborateurs, 150 000
dossiers patients actifs. » — Le fait indique un périmètre de 4 cliniques moyennes, alors que les passages [1] et [2] mentionnent un périmètre de 12 cliniques.
- FAQ___Complément_de_Cadrage_-_SanteTech_ : « • 6 Cliniques de Proximité / Chirurgie : ~50 lits, 150 collaborateurs/site. » **≠** Présentation_du_Projet_d_Étude_-_M2_CYBE : « Périmètre : 12 cliniques, 4500 collaborateurs, 150 000
dossiers patients actifs. » — Le fait indique un périmètre de 6 cliniques, tandis que les passages [1] à [4] mentionnent un périmètre de 12 cliniques.
- FAQ___Complément_de_Cadrage_-_SanteTech_ : « Seuls les serveurs d'impression et les caches DICOM/PACS restent en local dans les cliniques. » **≠** Fiche_d_Audit_Technique_-_État_des_Lieux : « Cliniques (01 à 12) : 1 Read-Only Domain Controller (RODC) ou DC virtuel par site hébergé sur un serveur local vieillissant pour assurer l'authentification en c » — Le fait stipule que SEULS les serveurs d'impression et les caches DICOM/PACS restent en local. Or, le passage [3] indique que des contrôleurs de domaine (RODC ou DC virtuel) sont également hébergés su
- FAQ___Complément_de_Cadrage_-_SanteTech_ : « Annuaire : Forêt Active Directory unique (corp.santetech.local) avec 16 contrôleurs de domaine (1 DC/RODC par clinique). » **≠** Fiche_d_Audit_Technique_-_État_des_Lieux : « Domaine racine : hq.corp.santetech.local (Siège - Rennes). » — Le fait indique une forêt Active Directory unique (corp.santetech.local), alors que le passage [3] décrit une structure de domaines enfants (hq.corp.santetech.local, clinique-armor.corp.santetech.loca
- FAQ___Complément_de_Cadrage_-_SanteTech_ : « HDS. Seuls les serveurs d'impression et les caches
DICOM/PACS restent en local dans les cliniques. |
| 6 | Fournisseur Cloud &
Souveraineté | Aucun fournisseur  » **≠** Fiche_d_Audit_Technique_-_État_des_Lieux : «                    ■​ 10.1.30.0/24 : VLAN IoT / Biomédical (Non cloisonné, routage
                      direct vers les automates)
                   ■​ 10.1.4 » — Le fait (FAQ SanteTech) stipule que seuls les serveurs d'impression et les caches DICOM/PACS restent en local, impliquant une migration ou une centralisation des autres données. Cependant, le passage 
- Fiche_d_Audit_Technique_-_État_des_Lieux : « 10.1.10.0/24 : VLAN Serveurs Locaux (DPI local, Impression) » **≠** FAQ___Complément_de_Cadrage_-_SanteTech_ : « • As-Is : DPI Nexus hébergé sur ferme Citrix/RDS au Siège de Rennes. » — Le fait indique que le VLAN 10.1.10.0/24 est destiné aux 'Serveurs Locaux (DPI local, Impression)'. Cependant, le passage [4] précise que le DPI Nexus est hébergé sur une ferme Citrix/RDS au Siège de 
