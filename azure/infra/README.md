# Terraform — SAP Data Engineering Platform

Infrastructure as Code du projet **SAP S/4HANA → Azure Data Engineering**.

## Objectif

Ce dossier décrit avec Terraform les principales ressources Azure utilisées par la plateforme :

SAP/OData → Azure Data Factory → ADLS Gen2 → Azure Databricks → Delta Lake Bronze/Silver/Gold → Serving → Azure SQL → Power BI.

L'infrastructure a initialement été créée pendant le LAB, puis reprise selon une approche **Terraform Brownfield** :

1. inventaire des ressources Azure existantes ;
2. écriture des ressources HCL ;
3. import des ressources dans le Terraform State ;
4. comparaison avec `terraform plan` ;
5. alignement contrôlé du HCL avec l'infrastructure réelle.

## Ressources gérées

Le state Terraform contient notamment :

- Resource Group `rg-sap-data-platform`
- ADLS Gen2 `stsapdata778c25`
- filesystems `bronze`, `silver`, `gold`
- Azure Data Factory `adf-sap-data-778c25`
- Self-Hosted Integration Runtime `shir-sap-local`
- Azure Databricks Workspace `dbw-sap-data`
- Databricks Access Connector `ac-dbw-sap-data`
- Azure Key Vault `kv-sap-data-7cc1d2`
- RBAC ADF → ADLS
- RBAC Databricks Access Connector → ADLS

## Structure

infra/
├── README.md
├── versions.tf
├── provider.tf
├── variables.tf
├── main.tf
├── storage.tf
├── adf.tf
├── databricks.tf
├── keyvault.tf
├── rbac.tf
└── .terraform.lock.hcl

## Initialisation :

La subscription Azure n'est pas stockée dans le dépôt.

export TF_VAR_subscription_id="$(az account show --query id -o tsv)"

terraform init
terraform validate
terraform plan

## Sécurité :

Les éléments suivants ne doivent jamais être versionnés :

terraform.tfstate
terraform.tfstate.backup
.terraform/
fichiers .tfvars contenant des secrets
mots de passe
tokens OAuth
secrets Azure Key Vault

Les secrets applicatifs sont gérés séparément de ce dépôt.

## Azure Key Vault :

Utilisation de,

- SKU Standard
- Soft Delete : 90 jours
- Purge Protection : désactivée
- Access Policy model (enable_rbac_authorization = false)

Cette configuration reproduit l'environnement existant.

Pour une architecture de production, Purge Protection et une stratégie RBAC/Private Endpoint doivent être étudiées
et activées selon les exigences de sécurité et de récupération.

## Azure SQL :

Azure SQL a été utilisé comme couche de serving du projet, mais n'est pas actuellement géré par ce state Terraform.

Le provider AzureRM impose une configuration d'authentification administrateur pour azurerm_mssql_server. 
Autorisant simultanément Microsoft Entra ID et SQL Authentication, aucun mot de passe administrateur n'est stocké 
dans le dépôt Terraform.

Une implémentation production doit utiliser une stratégie explicite de gestion des identités et secrets.

## Remarque Databricks

La configuration Terraform correspond à l'état actuel du projet.

Elle ne représente pas à elle seule l'architecture réseau recommandée pour une plateforme de production.

Une architecture production devrait notamment étudier :

- réseau privé ;
- Private Endpoints ;
- Private DNS ;
- stratégie d'egress/NAT ;
- diagnostics et monitoring ;
- séparation dev/staging/prod.

## Destruction

Ne jamais exécuter terraform destroy sans :

- vérifier le plan ;
- sauvegarder les données nécessaires ;
- vérifier les protections Azure ;
- confirmer les ressources hors Terraform ;
- contrôler les dépendances Databricks et Azure SQL.

Auteur : Cédric SSH - SAP data engineer 
