# Recherches, contradictions et questions ouvertes

31 besoins d'information examinés : **4 connus**, **11 partiels**, **16 non documentés**.

> « Non documenté » signifie que **les documents fournis n'en parlent pas**. Cela ne prouve pas que la mesure n'existe pas : c'est une question à poser à l'entreprise.

## Ce que nous savons

- **Comment sont réalisées les sauvegardes et où sont-elles stockées ?** L'admin lance manuellement un script qui dump MySQL et zip les uploads, puis les transfère via FTP vers un dossier du même hébergeur mutualisé.
  - preuve (etude_de_cas_piegee.md) : « - Sauvegarde hebdo : un `.sql` complet + un `.zip` des uploads (SQL en clair, pas chiffré). »
  - preuve (etude_de_cas_piegee.md) : « 4. **Sauvegarde** : admin lance manuellement un script (cron absent) qui dump MySQL + zip uploads → FTP vers un dossier du même hébergeur mutualisé.

## 6. Incidents passés / signaux

- 2023 : **email »
- **Les comptes d'administration sont-ils nominatifs ou partagés ?** Les comptes sont nominatifs : un compte pour l'admin cliente « Mélanie » et des comptes dédiés pour les deux préparateurs.
  - preuve (etude_de_cas_piegee.md) : «    ├─ Espace fichier (produits images, exports .csv commandes)
   └─ Back-office admin (/admin, template Bootstrap, login mot de passe simple)
        ↑── Admin cliente (1 personne)
        └── 2 prép »
  - preuve (etude_de_cas_piegee.md) : « | Client | Passer commande, suivre, se désinscrire de la newsletter | compte optionnel (e-mail + mot de passe) |
| Prestataires | PayFlow : webhooks commandes ; MailJet : envoi | clés API dans .env du »
- **Quels incidents de sécurité ont eu lieu récemment ?** En 2023, un emailing a été piraté via MailJet. En 2024, une tentative brute force sur /admin a été détectée. En 2025, une perte de 2 jours de commandes a eu lieu.
  - preuve (etude_de_cas_piegee.md) : « 4. **Sauvegarde** : admin lance manuellement un script (cron absent) qui dump MySQL + zip uploads → FTP vers un dossier du même hébergeur mutualisé.

## 6. Incidents passés / signaux

- 2023 : **email »
- **Existe-t-il un registre des traitements RGPD et est-il complet ?** Le registre est absent.
  - preuve (etude_de_cas_piegee.md) : « - **RGPD** : données personnelles côté EU ; pas de DPO, registre absent, mentions légales incomplètes, droit à l'oubli non automatisé. »

## Ce que nous savons en partie

- **Quelles normes ou certifications (ISO 27001, etc.) sont obtenues ou visées ?** La norme PCI DSS est mentionnée : les cartes sont hors périmètre via la tokenisation, mais le checkout manipule des pages de paiement embarquées. _(à valider : Information partielle. Il manque : Préciser si d'autres normes (comme ISO 27001) sont obtenues ou visées..)_
  - preuve (etude_de_cas_piegee.md) : « **PCI DSS** : cartes hors périmètre (tokenisation) mais le checkout manipule des pages de paiement embarquées. »
  - **Manque** : Préciser si d'autres normes (comme ISO 27001) sont obtenues ou visées.
- **Quelles sont les applications critiques et qui en est propriétaire ?** La disponibilité du site est critique en décembre. L'entreprise propriétaire est « ShoPix », une petite boutique en ligne (TPE). _(à valider : Information partielle. Il manque : Le document ne précise pas explicitement quelles applications spécifiques sont considérées comme critiques, seulement la disponibilité du site en décembre..)_
  - preuve (etude_de_cas_piegee.md) : « - **Règles affaires** : la disponibilité du site est critique en décembre (sinon perte de CA directe) ; le respect RGPD est une exigence réglementaire ; la réputation est fragile (petite entreprise). »
  - preuve (etude_de_cas_piegee.md) : « « ShoPix » est une petite boutique en ligne (TPE) qui vend des produits imprimés (posters, t-shirts, goodies) sur commande. »
  - **Manque** : Le document ne précise pas explicitement quelles applications spécifiques sont considérées comme critiques, seulement la disponibilité du site en décembre.
- **Quels sont les sites de l'entreprise et leur rôle ?** Le site possède un back-office admin (/admin) pour la gestion et un espace fichier pour les produits, images et exports. Il utilise aussi des sous-domaines api. et admin. _(à valider : Information partielle. Il manque : La liste exhaustive et précise de tous les sites physiques ou numériques de l'entreprise n'est pas explicitement détaillée.. Les deux vérificateurs divergent : relire les extraits cités.)_
  - preuve (etude_de_cas_piegee.md) : «    ├─ Espace fichier (produits images, exports .csv commandes)
   └─ Back-office admin (/admin, template Bootstrap, login mot de passe simple)
        ↑── Admin cliente (1 personne)
        └── 2 prép »
  - **Manque** : La liste exhaustive et précise de tous les sites physiques ou numériques de l'entreprise n'est pas explicitement détaillée.
- **Combien de postes de travail existent et sont-ils chiffrés ?** Il existe 3 postes de travail identifiés : 1 admin cliente et 2 préparateurs. Le nombre de postes clients est exclu du périmètre. _(à valider : Information partielle. Il manque : Le nombre exact de postes clients (actuellement exclus du périmètre).. Les deux vérificateurs divergent : relire les extraits cités.)_
  - preuve (etude_de_cas_piegee.md) : «    ├─ Espace fichier (produits images, exports .csv commandes)
   └─ Back-office admin (/admin, template Bootstrap, login mot de passe simple)
        ↑── Admin cliente (1 personne)
        └── 2 prép »
  - **Manque** : Le nombre exact de postes clients (actuellement exclus du périmètre).
- **Quels services sont hébergés en SaaS ou dans le cloud, chez quels fournisseurs ?** MailJet (envoi d'e-mails) et PayFlow (paiement) sont des services externes. Le site utilise un hébergeur mutualisé pour le site web, la base de données et les sauvegardes. _(à valider : Information partielle. Il manque : Le nom spécifique du fournisseur de l'hébergeur mutualisé..)_
  - preuve (etude_de_cas_piegee.md) : « - **Inclus** : site web public, back-office, base de données, flux paiement côté boutique, e-mails, sauvegardes, comptes admin.
- **Exclus** (mais frontières de confiance à tracer) : infrastructure Pa »
  - preuve (etude_de_cas_piegee.md) : « 4. **Sauvegarde** : admin lance manuellement un script (cron absent) qui dump MySQL + zip uploads → FTP vers un dossier du même hébergeur mutualisé.

## 6. Incidents passés / signaux

- 2023 : **email »
  - preuve (etude_de_cas_piegee.md) : « | Client | Passer commande, suivre, se désinscrire de la newsletter | compte optionnel (e-mail + mot de passe) |
| Prestataires | PayFlow : webhooks commandes ; MailJet : envoi | clés API dans .env du »
  - preuve (etude_de_cas_piegee.md) : « - Clé API PayFlow stockée dans le **.env** versionné sur GitHub (repo privé, oubliée pendant 1 mois). »
  - **Manque** : Le nom spécifique du fournisseur de l'hébergeur mutualisé.
- **L'authentification multifacteur (MFA) est-elle en place, pour quels comptes ?** L'authentification multifacteur (MFA) n'est pas en place pour le compte de l'Admin cliente « Mélanie » ni pour les comptes des deux préparateurs (mot de passe simple uniquement). _(à valider : La réponse proposée n'est pas soutenue par les preuves citées : relire les extraits avant de s'y fier.)_
  - preuve (etude_de_cas_piegee.md) : « | Rôle | Droits | Compte |
|---|---|---|
| Admin cliente « Mélanie » | Tout (produits, commandes, clients, exports) | mot de passe simple, **pas de MFA**, sessions 30 j | »
  - preuve (etude_de_cas_piegee.md) : « ## Page 1

# Étude de cas — Boutique en ligne (cas « pilote »)

> Cas d'exemple riche pour tester la chaîne d'agents E21. Description volontairement détaillée
> (architecture, acteurs, flux, données,  »
- **Qui dispose d'un accès à distance (VPN, télémaintenance, prestataires) ?** Un prestataire a un accès téléversement via FTP pour les sauvegardes manuelles hebdomadaires. _(à valider : Information partielle. Il manque : Préciser si d'autres prestataires ou des accès VPN/télémaintenance spécifiques sont configurés.. Les deux vérificateurs divergent : relire les extraits cités.)_
  - preuve (etude_de_cas_piegee.md) : «    ├─ Espace fichier (produits images, exports .csv commandes)
   └─ Back-office admin (/admin, template Bootstrap, login mot de passe simple)
        ↑── Admin cliente (1 personne)
        └── 2 prép »
  - **Manque** : Préciser si d'autres prestataires ou des accès VPN/télémaintenance spécifiques sont configurés.
- **Le réseau est-il segmenté et quels pare-feu protègent les sites ?** Le site est sur un hébergeur mutualisé où le pare-feu n'est pas configurable. _(à valider : Information partielle. Il manque : Précisions sur la segmentation interne du réseau de l'hébergeur et les dispositifs de sécurité spécifiques mis en place par HostPlanet..)_
  - preuve (etude_de_cas_piegee.md) : « 4. **Sauvegarde** : admin lance manuellement un script (cron absent) qui dump MySQL + zip uploads → FTP vers un dossier du même hébergeur mutualisé.

## 6. Incidents passés / signaux

- 2023 : **email »
  - **Manque** : Précisions sur la segmentation interne du réseau de l'hébergeur et les dispositifs de sécurité spécifiques mis en place par HostPlanet.
- **Les journaux (logs) sont-ils centralisés et analysés, qui reçoit les alertes ?** Les logs HTTP contiennent des tentatives de brute force sur /admin, mais les passages ne précisent pas s'ils sont centralisés, analysés ou qui reçoit les alertes. _(à valider : Information partielle. Il manque : Précisions sur l'outil de centralisation des logs, le processus d'analyse et l'identité du destinataire des alertes.. Les deux vérificateurs divergent : relire les extraits cités.)_
  - preuve (etude_de_cas_piegee.md) : « 2024 : **tentative brute force** sur `/admin` détectée dans les logs HTTP (mille tentatives/24 h) — aucun lockout. »
  - preuve (etude_de_cas_piegee.md) : « - 2024 : **tentative brute force** sur `/admin` détectée dans les logs HTTP (mille tentatives/24 h) — aucun lockout. »
  - **Manque** : Précisions sur l'outil de centralisation des logs, le processus d'analyse et l'identité du destinataire des alertes.
- **Quelles données personnelles sont traitées (clients, salariés, géolocalisation) ?** Les données clients incluent : nom, e-mail, adresse de livraison, n° de téléphone, historique de commandes, mot de passe (hashé sha1) et consentement newsletter. Les exports .csv contiennent tout (clients + commandes). _(à valider : La réponse proposée n'est pas soutenue par les preuves citées : relire les extraits avant de s'y fier.)_
  - preuve (etude_de_cas_piegee.md) : « - **Clients** : nom, e-mail, adresse de livraison, n° de téléphone, historique de commandes, mot de passe (hashé sha1 — ancien), consentement newsletter (cases décochent mal enregistrées). »
  - preuve (etude_de_cas_piegee.md) : « └─ Base MySQL (clients, commandes, produits)    → 1 seule base, 1 compte "shopix" »
  - **Manque** : Données relatives aux salariés (autres que les rôles mentionnés) et données de géolocalisation.
- **Quels prestataires ont accès au système d'information et avec quelles clauses de sécurité ?** Les prestataires identifiés sont PayFlow (paiement via API REST + webhooks) et MailJet (e-mails). Les clauses de sécurité spécifiques ne sont pas mentionnées. _(à valider : Information partielle. Il manque : Les clauses de sécurité spécifiques et les contrats de service (SLA) des prestataires PayFlow et MailJet..)_
  - preuve (etude_de_cas_piegee.md) : «    ├─ Espace fichier (produits images, exports .csv commandes)
   └─ Back-office admin (/admin, template Bootstrap, login mot de passe simple)
        ↑── Admin cliente (1 personne)
        └── 2 prép »
  - **Manque** : Les clauses de sécurité spécifiques et les contrats de service (SLA) des prestataires PayFlow et MailJet.

## Ce que nous ignorons encore (questions à poser)

- [Gouvernance] **Qui est le RSSI et est-il indépendant du DSI ?** L'identité du RSSI et sa relation d'indépendance avec le DSI ne sont mentionnées dans aucun des documents fournis.
- [Gouvernance] **Existe-t-il une politique de sécurité (PSSI) et de quelle version ?** Une mention explicite de l'existence ou de la version d'une Politique de Sécurité des Systèmes d'Information (PSSI) dans les documents fournis.
- [Gouvernance] **À quelle fréquence se réunit le comité de sécurité ?** Le document mentionnant le calendrier ou le fonctionnement du comité de sécurité.
- [Continuité] **Quand a eu lieu la dernière restauration de sauvegarde réussie ?** L'historique des restaurations de sauvegarde n'est pas mentionné dans les documents fournis.
- [Continuité] **Existe-t-il un plan de reprise d'activité, quand a-t-il été testé, quel est le site de repli ?** Un document décrivant le plan de reprise d'activité (PRA), la date de son dernier test et l'emplacement du site de repli.
- [Accès] **Comment et sous quel délai les comptes des personnes parties sont-ils désactivés ?** Une procédure ou une règle métier précisant le processus de désactivation des comptes et les délais associés.
- [Réseau] **Quels sont les liens Internet et existe-t-il un lien de secours ?** Les documents ne mentionnent aucun lien Internet spécifique ni de lien de secours.
- [Réseau] **Quels équipements sont obsolètes ou hors support constructeur ?** Liste complète des équipements matériels et logiciels de l'entreprise pour identifier tout autre élément hors support.
- [Exploitation] **Comment sont gérés les correctifs de sécurité et les vulnérabilités ?** Une description de la procédure de gestion des correctifs de sécurité et des vulnérabilités (processus de patching, outils utilisés, fréquence de mise à jour).
- [Exploitation] **Un test d'intrusion ou un audit technique externe a-t-il été réalisé ?** Une confirmation explicite de la réalisation ou non d'un test d'intrusion ou d'un audit technique externe par un tiers.
- [Données] **Qui est le délégué à la protection des données (DPO) ?** L'identité ou l'existence d'un délégué à la protection des données (DPO) n'est pas mentionnée (le document indique seulement qu'il n'y a pas de DPO).
- [Données] **Comment une violation de données est-elle notifiée à la CNIL ?** Une procédure ou un document expliquant la méthode de notification à la CNIL (ex: formulaire en ligne, délai de 72h, etc.).
- [Fournisseurs] **L'entreprise dispose-t-elle d'une assurance cyber ?** Une mention explicite de la présence ou de l'absence d'une police d'assurance cyber dans les documents fournis.
- [Humain] **Quelle sensibilisation à la sécurité a été faite et quand ?** Aucune information sur les actions de sensibilisation à la sécurité n'est mentionnée dans les documents fournis.
- [Humain] **Quel est le processus d'arrivée et de départ des collaborateurs ?** Une description des procédures RH ou de gestion des accès pour les employés (onboarding/offboarding).
- [Sécurité physique] **Comment sont protégées les salles serveurs (accès, incendie, énergie) ?** Informations sur les mesures de sécurité physique (accès, incendie, énergie) de la salle serveur.

## Contradictions entre documents (à valider)

_Aucune contradiction de priorité haute._
