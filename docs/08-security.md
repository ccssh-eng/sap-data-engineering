# 08 — Sécurité, Identités et Gouvernance de la plateforme Data Azure

## 1. Objectif

La sécurité de la plateforme SAP Data Engineering ne repose pas sur un unique mécanisme.

Elle combine plusieurs couches :

```text
Authentication
      +
Authorization
      +
Secret Management
      +
Data Governance
      +
Network Security
      +
Auditability
```

L'objectif est de répondre précisément aux questions suivantes :

```text
QUI ?
 ↓
s'authentifie

AVEC QUELLE IDENTITÉ ?
 ↓
Microsoft Entra / Managed Identity

VERS QUELLE RESSOURCE ?
 ↓
ADLS / Azure SQL / Key Vault / Databricks

AVEC QUEL DROIT ?
 ↓
Azure RBAC / SQL permissions / Unity Catalog

ET COMMENT LE CONTRÔLER ?
 ↓
Logs / Audit / Monitoring
```

---

# 2. Architecture de sécurité

L'architecture du LAB peut être représentée ainsi :

```text
                    Microsoft Entra ID
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
      Managed Identities          User / Workload
              │                         │
      ┌───────┴────────┐                │
      │                │                │
      ▼                ▼                ▼
     ADF         Databricks        Azure SQL
      │        Access Connector         │
      │                │                │
      └───────┬────────┘                │
              │                         │
              ▼                         │
          Azure RBAC                    │
              │                         │
              ▼                         │
             ADLS                       │
              ▲                         │
              │                         │
       Unity Catalog                    │
              │                         │
      Storage Credential                │
              │                         │
      External Locations                │
                                        │
                          SQL permissions / Entra
```

Azure Key Vault complète cette architecture lorsqu'un secret doit réellement être conservé.

---

# 3. Authentification

L'authentification répond à :

```text
Qui es-tu ?
```

Exemples :

```text
utilisateur Entra
Managed Identity ADF
Managed Identity Access Connector
Service Principal
```

Elle établit l'identité du demandeur.

Elle ne signifie pas encore que celui-ci est autorisé à accéder à une ressource.

---

# 4. Autorisation

L'autorisation répond à :

```text
Que peux-tu faire ?
```

Une identité authentifiée peut parfaitement recevoir :

```text
403 Forbidden
```

si elle ne possède pas le rôle nécessaire.

Dans Azure, le projet utilise notamment :

```text
Azure RBAC
```

pour contrôler l'accès aux ressources.

---

# 5. Authentification ≠ Autorisation

Cette distinction est fondamentale.

```text
Authentication
→ identité vérifiée

Authorization
→ permissions accordées
```

Exemple :

```text
ADF possède une Managed Identity
```

ne signifie pas automatiquement :

```text
ADF peut écrire dans ADLS
```

Il faut également lui attribuer un rôle approprié.

---

# 6. Gestion des secrets

La gestion des secrets répond à une troisième problématique :

```text
Comment conserver une information sensible
lorsqu'un secret reste nécessaire ?
```

Exemples :

```text
password
API key
client secret
connection string
```

Azure Key Vault est conçu pour centraliser ce type d'information.

---

# 7. Gouvernance

La gouvernance répond encore à une autre question :

```text
Qui peut utiliser quelle donnée ?
```

Dans Databricks, Unity Catalog apporte une couche de gouvernance sur :

```text
catalogs
schemas
tables
volumes
external locations
storage credentials
```

Il ne faut donc pas confondre :

```text
Azure RBAC
```

et :

```text
Unity Catalog
```

---

# 8. Les quatre notions principales

```text
Authentication
→ Qui suis-je ?

Authorization
→ Que puis-je faire ?

Secret Management
→ Comment protéger les credentials nécessaires ?

Data Governance
→ Qui peut accéder à quelles données et objets ?
```

Ces quatre notions sont complémentaires.

---

# 9. Microsoft Entra ID

Microsoft Entra ID fournit le système d'identité utilisé par les services Azure.

Dans le projet, il intervient notamment pour :

```text
Azure CLI authentication
Azure SQL authentication
Managed Identities
Service Principal
Azure resource access
```

Il constitue donc une composante centrale de l'architecture de sécurité.

---

# 10. Pourquoi éviter les mots de passe statiques

Une architecture comme :

```text
application
 ↓
username + password
 ↓
Azure resource
```

présente plusieurs risques :

- secret à stocker ;
- rotation nécessaire ;
- risque de fuite ;
- secret potentiellement committé ;
- difficulté de révocation ;
- maintenance supplémentaire.

Lorsque possible, le projet privilégie :

```text
identity
 ↓
token
 ↓
resource
```

---

# 11. Managed Identity

Une Managed Identity fournit une identité Microsoft Entra à une ressource Azure.

Elle évite de gérer manuellement :

```text
client secret
password
```

pour de nombreux scénarios Azure-to-Azure.

Architecture :

```text
Azure Resource
      ↓
Managed Identity
      ↓
Microsoft Entra
      ↓
Access Token
      ↓
Target Resource
```

---

# 12. Managed Identity ADF

Azure Data Factory possède dans le projet une :

```text
System-Assigned Managed Identity
```

Elle est attachée directement à la Data Factory.

Architecture :

```text
ADF
 ↓
System Assigned Managed Identity
 ↓
Microsoft Entra
 ↓
Azure RBAC
 ↓
ADLS
```

---

# 13. Identité ADF validée

La Data Factory :

```text
adf-sap-data-778c25
```

avait une Managed Identity système activée.

Cette identité a été utilisée pour accéder au compte ADLS du projet.

Le pipeline n'avait donc pas besoin de stocker une Storage Account Key dans son code.

---

# 14. RBAC ADF → ADLS

La Managed Identity ADF a reçu le rôle :

```text
Storage Blob Data Contributor
```

sur le compte de stockage.

Chaîne :

```text
ADF
 ↓
Managed Identity
 ↓
Storage Blob Data Contributor
 ↓
ADLS
```

---

# 15. Pourquoi `Storage Blob Data Contributor`

Le pipeline doit pouvoir écrire les données Bronze.

Il a donc besoin de permissions Data Plane adaptées.

Le rôle permet notamment les opérations nécessaires sur les blobs selon son périmètre d'attribution.

Il est préférable à une approche utilisant directement :

```text
Storage Account Key
```

dans la configuration applicative.

---

# 16. Scope RBAC

Une attribution RBAC possède un scope.

Conceptuellement :

```text
Management Group
Subscription
Resource Group
Resource
```

Dans le LAB, l'attribution utilisée par ADF était appliquée au compte de stockage.

Cela limite le périmètre par rapport à une attribution inutilement large au niveau de toute la subscription.

---

# 17. Least Privilege

Le principe du moindre privilège consiste à accorder :

```text
uniquement les permissions nécessaires
```

et :

```text
uniquement sur le périmètre nécessaire
```

Anti-pattern :

```text
Contributor sur toute la subscription
```

pour un workload qui doit seulement écrire dans un stockage précis.

---

# 18. Control Plane et Data Plane

Azure distingue conceptuellement deux catégories d'opérations.

### Control Plane

Gestion de la ressource :

```text
create
delete
configure
```

### Data Plane

Accès aux données :

```text
read blob
write blob
delete blob
```

Une identité pouvant administrer une ressource ne possède pas nécessairement toutes les permissions Data Plane correspondantes.

---

# 19. Pourquoi cette distinction compte

Un utilisateur peut avoir suffisamment de droits pour voir :

```text
Storage Account
```

dans Azure Portal tout en ne pouvant pas lire :

```text
bronze/sap/sales_orders/
```

Les permissions de management et les permissions de données doivent donc être analysées séparément.

---

# 20. Databricks et ADLS

Databricks doit également accéder aux couches :

```text
Bronze
Silver
Gold
```

Le projet évite de placer directement une Storage Account Key dans les notebooks.

Il utilise une architecture basée sur :

```text
Databricks Access Connector
+
Managed Identity
+
Azure RBAC
+
Unity Catalog
```

---

# 21. Databricks Access Connector

Le projet a créé :

```text
ac-dbw-sap-data
```

Il possède une Managed Identity.

Architecture :

```text
Databricks
 ↓
Access Connector
 ↓
Managed Identity
 ↓
Azure RBAC
 ↓
ADLS
```

---

# 22. RBAC Databricks → ADLS

L'identité de l'Access Connector a reçu :

```text
Storage Blob Data Contributor
```

sur le compte de stockage.

Cela fournit l'autorisation Azure nécessaire pour accéder aux données ADLS.

---

# 23. Pourquoi l'Access Connector

L'Access Connector permet de séparer :

```text
Databricks workspace
```

de :

```text
identity used to access Azure storage
```

Il fournit une identité Azure dédiée utilisable dans l'intégration avec Unity Catalog.

---

# 24. Unity Catalog

Unity Catalog apporte la couche de gouvernance Databricks.

Dans le LAB, nous avons configuré :

```text
Storage Credential
External Locations
```

pour permettre un accès gouverné aux données ADLS.

---

# 25. Storage Credential

Le Storage Credential créé est :

```text
cred_sap_adls
```

Il représente l'identité utilisée par Unity Catalog pour accéder au stockage Azure.

Architecture :

```text
Unity Catalog
 ↓
cred_sap_adls
 ↓
Access Connector
 ↓
Managed Identity
 ↓
Azure RBAC
 ↓
ADLS
```

---

# 26. Pourquoi le Storage Credential ne contient pas la donnée

Le Storage Credential ne représente pas :

```text
bronze
silver
gold
```

Il représente :

```text
comment Databricks s'authentifie
pour accéder au stockage
```

La localisation des données est ensuite définie par les External Locations.

---

# 27. External Location Bronze

Le projet a créé :

```text
ext_sap_bronze
```

qui associe conceptuellement :

```text
ADLS Bronze URL
+
cred_sap_adls
```

Architecture :

```text
ext_sap_bronze
       │
       ├── URL → bronze
       │
       └── Credential → cred_sap_adls
```

---

# 28. External Location Silver

Même principe pour :

```text
ext_sap_silver
```

qui gouverne le chemin correspondant à Silver.

---

# 29. External Location Gold

Même principe pour :

```text
ext_sap_gold
```

qui gouverne le chemin Gold.

La séparation permet de gérer les permissions selon les zones.

---

# 30. Chaîne complète Databricks

La chaîne de sécurité peut être représentée ainsi :

```text
Databricks User / Workload
          ↓
     Unity Catalog
          ↓
  External Location
          ↓
 Storage Credential
          ↓
  Access Connector
          ↓
   Managed Identity
          ↓
      Azure RBAC
          ↓
         ADLS
```

Chaque niveau remplit une fonction différente.

---

# 31. Azure RBAC versus Unity Catalog

Azure RBAC répond :

```text
L'identité Azure peut-elle accéder
au stockage ?
```

Unity Catalog répond :

```text
Quel utilisateur ou workload Databricks
peut utiliser quel objet de données ?
```

Les deux couches sont nécessaires.

---

# 32. Exemple

Même si :

```text
Access Connector
```

possède :

```text
Storage Blob Data Contributor
```

cela ne signifie pas que tous les utilisateurs Databricks doivent pouvoir accéder librement à toutes les données.

Unity Catalog permet d'ajouter une couche de gouvernance interne.

---

# 33. Defense in Depth

Cette combinaison illustre le principe :

```text
Defense in Depth
```

On ne dépend pas d'un unique contrôle.

Exemple :

```text
Azure Identity
+
Azure RBAC
+
Unity Catalog
+
Storage governance
```

Une erreur à un niveau ne doit pas automatiquement supprimer toutes les barrières de sécurité.

---

# 34. Catalog

Le LAB utilisait notamment le catalog :

```text
dbw_sap_data
```

Le catalog constitue un niveau logique de gouvernance dans Unity Catalog.

Architecture :

```text
Catalog
 ↓
Schema
 ↓
Table / View / Volume
```

---

# 35. Permissions Unity Catalog

Une architecture de production pourrait définir des groupes tels que :

```text
data_engineers
data_analysts
bi_readers
platform_admins
```

Puis attribuer les permissions au groupe plutôt qu'à chaque utilisateur individuellement.

---

# 36. Group-Based Access

Approche recommandée :

```text
User
 ↓
Entra Group
 ↓
Databricks Group
 ↓
Unity Catalog Grants
```

plutôt que :

```text
User A → permission
User B → permission
User C → permission
```

La gestion par groupes est plus maintenable à grande échelle.

---

# 37. Exemple de séparation

```text
Data Engineers
→ Bronze READ
→ Silver READ/WRITE
→ Gold READ/WRITE

BI Readers
→ Gold READ

Business Users
→ Serving / Power BI
```

Les droits exacts doivent être définis selon les responsabilités réelles.

---

# 38. Bronze Security

Bronze peut contenir des données proches de la source.

Il peut donc être plus sensible que Gold.

Tous les consommateurs métier n'ont pas nécessairement besoin d'y accéder.

Principe :

```text
raw access
→ restricted
```

---

# 39. Silver Security

Silver contient des données nettoyées mais souvent encore détaillées.

L'accès doit rester contrôlé selon :

- domaine ;
- sensibilité ;
- rôle ;
- finalité.

---

# 40. Gold Security

Gold expose des données orientées consommation.

Même si elles sont agrégées, elles ne doivent pas être considérées automatiquement comme publiques.

Le contrôle dépend du contenu métier.

---

# 41. Azure Key Vault

Le projet comprend également :

```text
kv-sap-data-7cc1d2
```

Azure Key Vault est destiné à stocker de manière centralisée :

```text
secrets
keys
certificates
```

lorsqu'ils sont nécessaires.

---

# 42. Managed Identity versus Key Vault

Les deux ne sont pas concurrents.

Si aucun secret n'est nécessaire :

```text
Managed Identity
```

peut suffire.

Si une application doit utiliser un secret tiers :

```text
Managed Identity
 ↓
Key Vault
 ↓
Secret
```

permet d'éviter de stocker ce secret dans le code.

---

# 43. Anti-pattern

```text
Python
 ↓
.env
 ↓
permanent production password
```

peut être utile temporairement en développement mais ne constitue pas une stratégie de secrets idéale en production.

La cible doit privilégier :

```text
Workload Identity
```

ou :

```text
Key Vault
```

selon le besoin.

---

# 44. Key Vault du LAB

Le Key Vault du LAB utilisait :

```text
SKU = Standard
Soft Delete = 90 jours
Purge Protection = false
Public Network Access = enabled
Access Policy mode
```

Ces paramètres correspondaient au contexte pédagogique temporaire.

Ils ne représentent pas nécessairement la configuration cible de production.

---

# 45. Key Vault de production

Une cible de production devrait étudier :

```text
RBAC authorization
Purge Protection
Private Endpoint
Public Network disabled
Diagnostic Settings
Rotation
Least Privilege
```

selon les exigences de l'entreprise.

---

# 46. Soft Delete

Soft Delete permet de conserver temporairement un coffre supprimé.

Dans le LAB :

```text
retention = 90 days
```

Cela protège contre certaines suppressions accidentelles.

---

# 47. Purge Protection

La Purge Protection empêche la suppression définitive prématurée d'un coffre supprimé pendant sa période de rétention.

Dans le LAB :

```text
purge_protection_enabled = false
```

afin de conserver un environnement facilement destructible.

En production, son activation doit être sérieusement considérée.

---

# 48. Pourquoi LAB et production diffèrent

Un LAB privilégie parfois :

```text
simplicité
coût
destruction rapide
```

Une production privilégie davantage :

```text
résilience
protection
audit
réseau privé
gouvernance
```

La configuration doit refléter le contexte.

---

# 49. Azure SQL et Microsoft Entra

Azure SQL a également utilisé Microsoft Entra.

Un administrateur Entra a été configuré.

Cela permet d'éviter une dépendance exclusive à l'authentification SQL traditionnelle.

---

# 50. Loader SQL

Le loader final utilisait :

```text
Microsoft Entra access token
```

avec :

```text
ODBC Driver 18
```

Architecture :

```text
User / Identity
 ↓
Microsoft Entra
 ↓
temporary token
 ↓
ODBC Driver
 ↓
Azure SQL
```

---

# 51. Pourquoi un token temporaire

Un token possède une durée de vie limitée.

Cela réduit le risque par rapport à un credential permanent stocké dans le code.

Le token ne doit toutefois jamais être :

```text
logged
committed
captured
shared
```

---

# 52. Nettoyage du token

Le loader a validé :

```text
Token supprimé : PASS
```

Le token temporaire n'était donc pas conservé comme artefact permanent du chargement.

---

# 53. Service Principal

Un Service Principal dédié avait également été créé :

```text
sp-sap-databricks-sql
```

L'objectif était de disposer d'une identité technique distincte pour un workload.

Cette approche sépare :

```text
human identity
```

de :

```text
application identity
```

---

# 54. Service Principal versus Managed Identity

### Service Principal

Peut nécessiter :

```text
client ID
+
credential
```

selon le mode utilisé.

### Managed Identity

Azure gère le cycle de vie du credential sous-jacent.

Lorsque le scénario le permet, Managed Identity réduit donc la gestion manuelle des secrets.

---

# 55. Workload Identity

Une production automatisée devrait éviter de dépendre d'un utilisateur humain connecté via :

```text
az login
```

Le pipeline devrait utiliser une identité dédiée au workload.

Exemple :

```text
CI/CD
 ↓
Workload Identity
 ↓
Azure
```

---

# 56. Passwordless

L'objectif général est de tendre vers :

```text
passwordless
```

lorsque les services le permettent.

Architecture :

```text
Identity
 ↓
short-lived token
 ↓
resource
```

plutôt que :

```text
stored password
```

---

# 57. Credentials dans Git

Le repository ne doit pas contenir :

```text
passwords
tokens
client secrets
connection strings sensibles
Terraform secrets
```

Le projet utilise `.gitignore` pour exclure notamment :

```text
.env
*.tfvars
Terraform state
Python virtual environments
```

---

# 58. Pourquoi Terraform State est sensible

Terraform State peut contenir :

- resource IDs ;
- configuration ;
- metadata ;
- parfois des valeurs sensibles.

Il ne doit donc pas être traité comme un simple fichier source.

Dans le projet :

```text
*.tfstate
*.tfstate.*
```

sont ignorés par Git.

---

# 59. Remote State de production

Une production devrait utiliser un backend distant sécurisé.

Exemple conceptuel :

```text
Terraform
 ↓
Azure Storage Backend
 ↓
State
```

avec :

```text
RBAC
encryption
locking
restricted access
versioning
```

selon la stratégie retenue.

---

# 60. `.terraform.lock.hcl`

À l'inverse du state :

```text
.terraform.lock.hcl
```

est versionné.

Il permet de conserver les sélections de versions de providers.

Il ne doit pas être confondu avec :

```text
terraform.tfstate
```

---

# 61. Terraform et Managed Identity ADF

Le projet Terraform contient :

```hcl
identity {
  type = "SystemAssigned"
}
```

pour ADF.

Cette déclaration rend l'identité partie intégrante de l'infrastructure.

---

# 62. Terraform RBAC ADF

L'attribution RBAC est également déclarée :

```hcl
resource "azurerm_role_assignment" "adf_storage_blob_contributor" {
  scope                = azurerm_storage_account.sap_data.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.sap_data.identity[0].principal_id
}
```

La relation :

```text
ADF identity
→ role
→ storage
```

est donc reproductible.

---

# 63. Terraform Databricks Access Connector

Le projet déclare :

```hcl
resource "azurerm_databricks_access_connector" "sap_data" {
  ...
  identity {
    type = "SystemAssigned"
  }
}
```

L'identité de stockage Databricks est donc également représentée dans l'IaC.

---

# 64. Terraform RBAC Databricks

L'Access Connector reçoit :

```text
Storage Blob Data Contributor
```

via Terraform.

Cela évite de dépendre uniquement d'une configuration manuelle Portal.

---

# 65. Brownfield Security

Le projet Terraform est issu d'une approche Brownfield.

Les ressources existaient avant leur déclaration dans Terraform.

La méthodologie a été :

```text
Discover
 ↓
Write HCL
 ↓
Import
 ↓
Plan
 ↓
Reconcile Drift
 ↓
No Changes
```

Les identités et RBAC faisaient partie de cette synchronisation.

---

# 66. Pourquoi importer le RBAC

Si une attribution existe dans Azure mais n'est pas représentée dans Terraform :

```text
infrastructure réelle
≠
infrastructure décrite
```

L'import permet de rapprocher :

```text
actual state
```

et :

```text
desired configuration
```

---

# 67. Sécurité et Drift

Une dérive de sécurité peut être particulièrement critique.

Exemple :

```text
rôle plus large ajouté manuellement
```

Une approche IaC permet de mieux identifier certaines différences lors des plans et revues.

---

# 68. Terraform Plan

Avant destruction, le projet a atteint :

```text
No changes.
Your infrastructure matches the configuration.
```

Cela confirmait que les ressources gérées par Terraform étaient synchronisées avec leur configuration déclarée.

---

# 69. Ce que Terraform ne gérait pas entièrement

Tous les éléments du projet n'étaient pas dans le state Terraform final.

Notamment :

```text
Azure SQL
```

avait été volontairement maintenu hors state final du LAB.

Les objets Unity Catalog n'étaient pas non plus tous gérés par le provider Terraform dans cette phase.

---

# 70. Production : Databricks Provider

Une évolution de production peut utiliser le provider Databricks afin de Terraformiser davantage :

```text
catalogs
schemas
storage credentials
external locations
grants
```

Cela étendrait l'IaC de :

```text
Azure infrastructure
```

vers :

```text
Databricks governance
```

---

# 71. Network Security

La sécurité ne se limite pas aux identités.

Il faut également contrôler :

```text
par où circule le trafic ?
```

Le LAB utilisait certaines ressources accessibles publiquement pour simplifier les exercices.

La production devrait considérer un réseau privé.

---

# 72. Private Endpoints

Les services compatibles peuvent être exposés via :

```text
Private Endpoint
```

Architecture :

```text
Workload
 ↓
VNet
 ↓
Private Endpoint
 ↓
PaaS Service
```

Cela permet de réduire l'exposition au réseau public.

---

# 73. Private DNS

Un Private Endpoint nécessite généralement une résolution DNS adaptée.

Architecture :

```text
service.domain
 ↓
Private DNS Zone
 ↓
private IP
```

Une configuration réseau privée incomplète peut provoquer des problèmes de connectivité même si les permissions sont correctes.

---

# 74. Sécurité réseau ADLS

Une cible de production peut considérer :

```text
Storage Firewall
Private Endpoint
Public Network disabled
Private DNS
```

selon les workloads devant accéder au Data Lake.

---

# 75. Sécurité réseau Azure SQL

Même principe :

```text
Azure SQL
 ↓
Private Endpoint
 ↓
VNet
```

avec un accès public désactivé ou fortement restreint lorsque l'architecture le permet.

---

# 76. Databricks Networking

Le workspace du LAB utilisait une configuration simplifiée qui a généré notamment des ressources réseau managées.

Parmi elles :

```text
NAT Gateway
Public IP
VNet
Network Security Group
```

Ces ressources ont eu un impact de coût notable pendant le LAB.

---

# 77. Sécurité et coût

Une architecture sécurisée doit également être économiquement maîtrisée.

Par exemple :

```text
NAT Gateway
```

peut être techniquement pertinent mais introduire un coût fixe et du trafic facturable.

Le design réseau doit donc considérer simultanément :

```text
security
availability
cost
operations
```

---

# 78. Monitoring de sécurité

Une production devrait surveiller notamment :

```text
authentication failures
authorization failures
RBAC changes
resource deletions
Key Vault access
SQL authentication events
network changes
```

Les événements doivent être centralisés selon la stratégie d'observabilité.

---

# 79. Azure Activity Log

Azure Activity Log permet de suivre les opérations Control Plane.

Exemples :

```text
resource created
resource deleted
role assignment changed
configuration modified
```

Il constitue une source importante pour l'audit des changements Azure.

---

# 80. Data Plane Logs

Les opérations Data Plane nécessitent leurs propres mécanismes de logs selon le service.

Il ne faut pas supposer que :

```text
Activity Log
```

contient automatiquement tous les accès aux données.

---

# 81. Diagnostic Settings

Les Diagnostic Settings permettent d'envoyer certains logs et métriques vers des destinations telles que :

```text
Log Analytics
Storage
Event Hub
```

selon le service.

Une cible de production devrait les Terraformiser.

---

# 82. Log Analytics

Une architecture centralisée peut utiliser :

```text
Azure Services
      ↓
Diagnostic Settings
      ↓
Log Analytics Workspace
      ↓
Queries / Alerts
```

Cela facilite la corrélation entre plusieurs composants.

---

# 83. Alertes

Exemples d'alertes possibles :

```text
repeated authentication failure
pipeline authorization failure
unexpected RBAC modification
Key Vault access anomaly
SQL connectivity failure
```

Les seuils et règles doivent être adaptés à l'environnement.

---

# 84. Audit des rôles

Les permissions doivent être révisées périodiquement.

Question :

```text
Cette identité a-t-elle encore besoin
de ce rôle ?
```

Une attribution créée pour un test temporaire peut devenir un risque si elle reste indéfiniment.

---

# 85. Cycle de vie des identités

Une identité technique possède elle aussi un cycle de vie :

```text
create
 ↓
grant permissions
 ↓
use
 ↓
review
 ↓
revoke
 ↓
delete
```

La suppression des ressources Cloud ne supprime pas nécessairement toutes les identités Entra créées séparément.

---

# 86. Point important du LAB

Le Service Principal :

```text
sp-sap-databricks-sql
```

est une ressource Entra et non simplement une ressource du Resource Group Azure.

La destruction :

```text
rg-sap-data-platform
```

ne garantit donc pas à elle seule sa suppression.

Il doit être vérifié séparément lors d'un nettoyage complet.

---

# 87. Key Vault Soft Delete après destruction

De même, un Key Vault supprimé avec Soft Delete peut rester dans un état récupérable pendant sa période de rétention.

La disparition du Resource Group ne signifie donc pas nécessairement que le coffre est immédiatement purgé définitivement.

---

# 88. Destruction ≠ Purge

Il faut distinguer :

```text
delete
```

et :

```text
purge
```

pour les services utilisant Soft Delete.

Une purge définitive doit être une décision explicite, surtout dans un environnement de production.

---

# 89. Management Lock

Le Resource Group du LAB avait un verrou :

```text
CanNotDelete
```

nommé :

```text
lock-sap-data-platform
```

Il protégeait contre une suppression accidentelle.

---

# 90. Ce que protège un Lock

Un Management Lock peut empêcher certaines opérations de suppression ou modification selon son type.

Il ne constitue pas un mécanisme d'authentification.

Il ne remplace donc pas :

```text
MFA
RBAC
Identity Security
```

---

# 91. Defense in Depth pour la suppression

Une architecture de production peut combiner :

```text
RBAC
+
Management Lock
+
Terraform review
+
CI/CD approval
+
backup
+
soft delete
```

pour réduire le risque de destruction accidentelle.

---

# 92. Pourquoi le Lock a été retiré

Le LAB devait être détruit volontairement pour stopper les coûts.

Le lock a donc été supprimé avant :

```text
terraform destroy
```

Cette action faisait partie du cycle de vie prévu.

---

# 93. Security by Design

La sécurité ne doit pas être ajoutée uniquement après le développement.

Dans le projet, elle influence :

```text
identités
storage access
SQL authentication
Databricks governance
Terraform
Git
networking
cleanup
```

Elle traverse donc l'ensemble de l'architecture.

---

# 94. Security by Default

Une architecture cible devrait chercher à ce que le comportement par défaut soit restrictif.

Exemple :

```text
public access disabled
```

puis ouvrir explicitement ce qui est nécessaire.

Plutôt que :

```text
everything open
```

puis tenter de restreindre plus tard.

---

# 95. Zero Trust

Le modèle Zero Trust peut être résumé par l'idée :

```text
ne pas accorder implicitement la confiance
en fonction de l'emplacement réseau
```

Les accès doivent être évalués à partir notamment :

```text
identity
authorization
context
resource
```

Le réseau privé reste utile mais ne remplace pas le contrôle d'identité.

---

# 96. MFA

Les comptes humains privilégiés doivent utiliser des protections fortes telles que MFA selon les politiques de l'organisation.

Une Managed Identity n'utilise pas MFA comme un utilisateur humain : elle repose sur une identité de workload gérée par Azure.

Les protections doivent donc être adaptées au type d'identité.

---

# 97. Human Access

Pour un administrateur :

```text
User
 ↓
MFA
 ↓
Entra
 ↓
RBAC
 ↓
Azure Resource
```

Le principe est de limiter les permissions permanentes excessives.

---

# 98. Privileged Access

Dans une organisation mature, les privilèges élevés peuvent être accordés temporairement via des mécanismes de gouvernance tels que Privileged Identity Management lorsque disponibles et configurés.

Principe :

```text
eligible
 ↓
activation
 ↓
temporary privilege
 ↓
expiration
```

plutôt que des droits administrateur permanents pour tous les besoins.

---

# 99. Separation of Duties

Une architecture de production peut séparer :

```text
Platform Admin
Data Engineer
Security Admin
Data Analyst
BI User
```

Une même personne ne devrait pas nécessairement disposer de tous les pouvoirs sur toutes les couches.

---

# 100. Exemple

```text
Platform Team
→ infrastructure

Data Engineering
→ pipelines

Security
→ policies / identity governance

BI
→ consumption

Business
→ analytics
```

La séparation réduit le risque d'erreur ou d'abus de privilège.

---

# 101. Security dans CI/CD

Le CI/CD Terraform ne devrait pas utiliser un compte humain permanent.

Architecture cible :

```text
GitHub Actions
 ↓
OIDC / Workload Identity Federation
 ↓
Microsoft Entra
 ↓
Azure
```

Cette approche évite de conserver un long-lived Azure client secret dans GitHub lorsque la fédération est disponible.

---

# 102. Terraform Plan Review

Un pipeline IaC peut séparer :

```text
terraform plan
```

et :

```text
terraform apply
```

avec une validation humaine pour les environnements sensibles.

Cela permet d'inspecter les changements avant application.

---

# 103. Destructive Change Protection

Une pipeline CI/CD peut détecter :

```text
resource destroy
```

et demander une approbation renforcée.

Exemple :

```text
Plan
 ↓
3 resources to destroy
 ↓
Manual Approval
 ↓
Apply
```

---

# 104. Secret Scanning

Le repository devrait également bénéficier de contrôles capables de détecter :

```text
tokens
passwords
private keys
connection strings
```

avant leur fusion.

Le `.gitignore` seul n'est pas une garantie suffisante si un secret est écrit dans un fichier versionné.

---

# 105. Rotation

Lorsqu'un secret reste nécessaire, il faut prévoir :

```text
creation
 ↓
storage
 ↓
usage
 ↓
rotation
 ↓
revocation
```

Un secret sans stratégie de rotation devient une dette de sécurité.

---

# 106. SQL Least Privilege

Le loader SQL devrait disposer uniquement des permissions nécessaires aux tables Serving.

Power BI devrait disposer principalement :

```text
SELECT
```

sur les objets nécessaires.

Cette séparation empêche un consommateur BI de modifier les données Serving.

---

# 107. Row-Level Security

Dans un contexte métier, Azure SQL ou Power BI peuvent également appliquer des mécanismes de sécurité au niveau des lignes selon l'architecture.

Exemple :

```text
Regional Manager France
→ France only

Regional Manager Germany
→ Germany only
```

Ce besoin dépend des exigences fonctionnelles.

---

# 108. Column-Level Protection

Certaines colonnes peuvent nécessiter des protections supplémentaires.

Exemples :

```text
personal data
financial data
confidential attributes
```

Le projet actuel utilise un dataset pédagogique simplifié et ne met pas en œuvre cette classification complète.

---

# 109. Data Classification

Une production devrait classifier les données :

```text
Public
Internal
Confidential
Restricted
```

ou selon la nomenclature de l'entreprise.

Cette classification influence :

```text
access
retention
encryption
sharing
monitoring
```

---

# 110. Encryption in Transit

Les communications doivent utiliser des protocoles sécurisés.

Le compte Storage du LAB impose notamment :

```text
HTTPS only
minimum TLS 1.2
```

Cela protège les communications vers le stockage.

---

# 111. Encryption at Rest

Les services Azure PaaS utilisent des mécanismes de chiffrement au repos.

Selon les exigences, une production peut également étudier :

```text
customer-managed keys
```

plutôt que les clés gérées par le service.

Ce choix augmente toutefois la complexité opérationnelle.

---

# 112. Customer-Managed Keys

Les CMK peuvent apporter davantage de contrôle sur le cycle de vie des clés.

Mais elles introduisent également :

```text
Key Vault dependencies
rotation
permissions
availability concerns
```

Elles doivent être utilisées lorsqu'une exigence justifie cette complexité.

---

# 113. Data Retention

La sécurité inclut également :

```text
combien de temps conserver les données ?
```

Bronze ne doit pas nécessairement être conservé éternellement.

La politique doit considérer :

```text
audit
replay
cost
legal requirements
business requirements
```

---

# 114. Logs Retention

Même principe pour :

```text
logs
audit records
DQ results
pipeline history
```

Une durée de rétention doit être définie.

---

# 115. Backup et Recovery

La protection ne consiste pas uniquement à empêcher un accès non autorisé.

Elle doit également permettre la récupération après :

```text
accidental deletion
corruption
operational error
```

La stratégie de sauvegarde dépend de chaque service.

---

# 116. Incident Response

Une architecture mature doit permettre de répondre à :

```text
Qui a fait quoi ?
Quand ?
Sur quelle ressource ?
Depuis quelle identité ?
Quel impact ?
```

D'où l'importance de :

```text
audit logs
activity logs
data logs
pipeline metadata
```

---

# 117. Exemple d'investigation

Supposons qu'une attribution RBAC soit modifiée.

Investigation :

```text
Azure Activity Log
 ↓
operation
 ↓
caller
 ↓
timestamp
 ↓
resource
 ↓
change
```

Cela permet de baser l'analyse sur des événements vérifiables.

---

# 118. Security Monitoring

Une architecture de production pourrait surveiller :

```text
role assignment creation
policy changes
firewall changes
public network activation
Key Vault operations
failed SQL authentication
unusual data access
```

Les alertes doivent être calibrées pour éviter trop de bruit.

---

# 119. Azure Policy

Azure Policy peut imposer ou auditer certaines règles.

Exemples conceptuels :

```text
require TLS
deny public access
require diagnostic settings
require tags
restrict regions
```

Elle apporte une gouvernance à l'échelle Azure au-delà d'un seul projet Terraform.

---

# 120. Terraform + Azure Policy

Les deux sont complémentaires.

```text
Terraform
→ déclare l'infrastructure du projet

Azure Policy
→ impose des règles organisationnelles
```

Terraform ne doit pas être considéré comme l'unique mécanisme de gouvernance Azure.

---

# 121. Sécurité du poste local

Le poste de développement reste également dans le périmètre de risque.

Il peut contenir temporairement :

```text
Azure CLI tokens
Git credentials
SSH keys
local files
Terraform state
```

Il doit donc être protégé comme un environnement ayant accès au Cloud.

---

# 122. Nettoyage local

Après un LAB, il peut être utile de vérifier :

```text
temporary tokens
.env files
downloaded credentials
local Terraform state
shell history
```

selon les données manipulées.

---

# 123. Captures portfolio

Les captures portfolio ne doivent jamais exposer :

```text
password
access token
client secret
private key
connection string
```

Les IDs techniques non secrets peuvent parfois apparaître, mais il est préférable de ne montrer que les informations nécessaires à la démonstration.

---

# 124. Preuves sécurité du projet

Les preuves existantes les plus fortes sont :

```text
ADF Managed Identity
+
Storage Blob Data Contributor

Databricks Access Connector
+
Managed Identity
+
RBAC

Unity Catalog
+
Storage Credential

External Locations
+
Bronze / Silver / Gold

Key Vault

Entra authentication
```

Elles démontrent plusieurs niveaux complémentaires.

---

# 125. Ce qui a réellement été implémenté

Le LAB a réellement validé :

```text
ADF System-Assigned Managed Identity
ADF → ADLS RBAC
Storage Blob Data Contributor

Databricks Access Connector
System-Assigned Managed Identity
Databricks → ADLS RBAC

Unity Catalog
Storage Credential
External Locations Bronze/Silver/Gold

Azure Key Vault

Microsoft Entra Azure SQL authentication
temporary access token

Terraform-managed identities and RBAC
Git secret hygiene
```

---

# 126. Ce qui relève de la cible production

Les éléments suivants sont des améliorations proposées :

```text
Private Endpoints
Private DNS
Key Vault RBAC mode
Purge Protection
public network disabled
central Log Analytics
Diagnostic Settings
security alerts
Azure Policy
PIM
OIDC CI/CD
group-based governance
automated secret scanning
Databricks grants as code
production network segmentation
```

Ils ne doivent pas être présentés comme déjà déployés dans le LAB.

---

# 127. Architecture de sécurité finale

```text
                         MICROSOFT ENTRA ID
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
     ADF Identity       Databricks Identity      SQL Identity
          │                     │                     │
          │                     ▼                     │
          │              Access Connector             │
          │                     │                     │
          ▼                     ▼                     ▼
       Azure RBAC            Azure RBAC          SQL Permissions
          │                     │                     │
          └────────────┬────────┘                     │
                       ▼                              │
                      ADLS                            │
                       ▲                              │
                       │                              │
                Unity Catalog                        │
                       │                              │
               Storage Credential                    │
                       │                              │
               External Locations                    │
                                                      │
                                                      ▼
                                                  Azure SQL


                    Secrets when required
                             │
                             ▼
                       Azure Key Vault
```

---

# 128. Modèle de défense en profondeur

```text
IDENTITY
Microsoft Entra
Managed Identity
Workload Identity

        ↓

AUTHORIZATION
Azure RBAC
SQL Permissions

        ↓

DATA GOVERNANCE
Unity Catalog
Storage Credentials
External Locations

        ↓

SECRET MANAGEMENT
Azure Key Vault

        ↓

NETWORK
Private Endpoints
Private DNS
Firewall

        ↓

AUDIT
Activity Log
Diagnostic Settings
Log Analytics
Alerts

        ↓

INFRASTRUCTURE GOVERNANCE
Terraform
Azure Policy
Management Locks
CI/CD approvals
```

---

# 129. Résultat

Le projet ne repose donc pas sur :

```text
un mot de passe
```

pour connecter tous les composants.

Il utilise plusieurs identités et mécanismes spécialisés :

```text
ADF → Managed Identity

Databricks → Access Connector + Managed Identity

ADLS → Azure RBAC

Databricks Data Governance → Unity Catalog

Azure SQL → Microsoft Entra

Secrets éventuels → Key Vault

Infrastructure → Terraform
```

Cette séparation réduit le couplage entre les credentials et le code applicatif.

---

# 130. Conclusion

La sécurité de la plateforme est construite autour du principe :

```text
Identity First
+
Least Privilege
+
No Hardcoded Secrets
+
Governed Data Access
+
Auditable Infrastructure
```

Le LAB a concrètement mis en œuvre :

```text
Managed Identity
Azure RBAC
Access Connector
Unity Catalog
Storage Credential
External Locations
Key Vault
Microsoft Entra
Terraform RBAC
```

et identifie clairement les évolutions nécessaires pour une cible de production :

```text
Private Networking
Centralized Monitoring
Purge Protection
RBAC-based Key Vault
Workload Federation
Policy as Code
Governance as Code
```

                                    ***************************************


