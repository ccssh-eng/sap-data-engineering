# SAP Data Engineering Platform on Azure

End-to-end Data Engineering project simulating the ingestion and processing of SAP S/4HANA business data using Azure Data Factory,

ADLS Gen2, Azure Databricks, PySpark, Delta Lake, Azure SQL, Power BI and Terraform.

The objective is not only to move SAP data to Azure, but to build a pipeline that addresses core enterprise Data Engineering

concerns: incremental processing, data quality, idempotence, security, observability, serving and Infrastructure as Code.

---

## 1. Business Context

SAP systems contain critical enterprise data such as customers, sales orders, materials and transactional records.

The objective of this project was to design a cloud Data Engineering platform capable of:

- extracting SAP-like data through an OData API;
- ingesting raw data into Azure;
- implementing a Bronze / Silver / Gold Lakehouse architecture;
- validating data quality before downstream consumption;
- processing incremental changes;
- preventing duplicate processing;
- exposing business KPIs through a serving layer;
- securing access using Azure identities and secrets;
- managing the main Azure infrastructure with Terraform.

The SAP source is simulated locally so that the complete integration architecture can be demonstrated without requiring access 
to a commercial SAP S/4HANA environment.

---

## 2. End-to-End Architecture

```text
SAP S/4HANA
     │
     │ CDS / OData API
     ▼
Local SAP OData Simulator
     │
     │ HTTP
     ▼
Self-Hosted Integration Runtime
     │
     ▼
Azure Data Factory
     │
     │ Copy Activity
     ▼
ADLS Gen2
┌─────────────────────────────┐
│ Bronze                      │
│ Raw SAP/OData JSON          │
└──────────────┬──────────────┘
               │
               ▼
        Azure Databricks
           + PySpark
               │
       Schema / Cleaning
       Data Quality Rules
               │
               ▼
┌─────────────────────────────┐
│ Silver — Delta Lake         │
│ Clean and typed data        │
│ Incremental MERGE           │
│ Idempotent processing       │
└──────────────┬──────────────┘
               │
               ▼
        Business Aggregations
               │
               ▼
┌─────────────────────────────┐
│ Gold — Delta Lake           │
│ customer_kpi                │
│ currency_kpi                │
│ daily_kpi                   │
└──────────────┬──────────────┘
               │
               ▼
          Serving Layer
               │
               ▼
           Azure SQL
               │
               ▼
            Power BI
```

Infrastructure and security:

```text
Terraform
   │
   ├── Resource Group
   ├── ADLS Gen2
   ├── Azure Data Factory
   ├── Self-Hosted IR
   ├── Azure Databricks
   ├── Access Connector
   ├── Azure Key Vault
   └── RBAC

ADF Managed Identity ─────────────► ADLS Gen2
Databricks Access Connector ──────► ADLS Gen2
Databricks ─► Key Vault ─► OAuth ─► Azure SQL
```

---

## 3. Why Each Component Exists

| Component          | Role in the platform             | Why it is used                                            |
|--------------------|-----------------------------|-----------------------------------------------------------|
| SAP / OData        | Enterprise data source      | Represents a standard API-based SAP extraction pattern |

| Self-Hosted IR     | Connectivity bridge         | Allows Azure Data Factory to reach a source running outside Azure |

| Azure Data Factory | Ingestion and orchestration | Controls movement of SAP/OData data into the Data Lake            |

| ADLS Gen2          | Cloud Data Lake             | Provides scalable storage for Bronze, Silver and Gold layers      |

| Azure Databricks   | Distributed processing      | Executes PySpark transformations and Delta Lake workloads         |

| PySpark            | Transformation engine       | Cleans, types, validates and aggregates datasets                   |

| Delta Lake         | Reliable Lakehouse storage  | Provides ACID transactions and `MERGE` for incremental processing   |

| Azure Key Vault    | Secret management            | Prevents application credentials from being hardcoded               |

| Managed Identity/RBAC | Azure authorization       | Reduces dependency on static credentials                            |

| Azure SQL          | Serving layer                | Exposes curated datasets to analytical consumers                    |

| Power BI            | Business analytics          | Visualizes Gold KPIs for end users                                  |

| Terraform           | Infrastructure as Code      | Makes cloud infrastructure reproducible, reviewable and version-controlled |

---

## 4. Project Implementation — 12 Steps

### Step 1 — SAP Data Modeling

A local SAP-like dataset was created around typical SAP business objects.

The project explored concepts such as:

- sales order headers and items;
- business partners;
- materials;
- business and composite keys;
- SAP-style identifiers such as `VBELN`, `POSNR` and `MATNR`.

Data quality controls were introduced early to detect duplicate keys, orphan records, unknown materials, invalid quantities and 

invalid monetary values.

### Step 2 — SAP OData API

A Flask API was implemented to simulate an SAP OData service.

The API supports concepts including:

- `$select`
- `$filter`
- `$expand`
- `$top`
- `$skip`
- `@odata.nextLink`

HTTP failure simulation was also introduced to validate retry and resilience mechanisms.

### Step 3 — Incremental Extraction

Incremental extraction was implemented using a watermark based on `LastChangeDateTime`.

```text
Initial load
    ↓
Maximum LastChangeDateTime
    ↓
Watermark
    ↓
Next extraction:
LastChangeDateTime > watermark
```

A local SQLite implementation was first used to validate the incremental pattern and UPSERT/idempotence behavior before moving 
to Azure.

### Step 4 — Azure Data Factory Ingestion

Azure Data Factory was configured to ingest the simulated SAP/OData source.

Because the API was hosted locally, a Self-Hosted Integration Runtime provided connectivity between Azure Data Factory and 
the local environment.

```text
SAP/OData HTTP
      ↓
Self-Hosted IR
      ↓
ADF Copy Activity
      ↓
ADLS Gen2 Bronze
```

The pipeline successfully copied the SAP sales order payload to the Bronze layer.

### Step 5 — Bronze Layer

Raw OData JSON is stored in ADLS Gen2 without applying business transformations.

Purpose:

- preserve source fidelity;
- support replay;
- provide traceability;
- decouple ingestion from transformation.

### Step 6 — Silver Transformation with PySpark

Databricks and PySpark transform the Bronze dataset into a typed and validated Silver representation.

Processing includes:

- JSON parsing;
- schema enforcement;
- type conversion;
- null validation;
- business-rule validation;
- duplicate detection.

Silver data is persisted using Delta Lake.

### Step 7 — Data Quality

Seven Data Quality checks were executed successfully in the Databricks pipeline.

The broader project also validates:

- primary/business key uniqueness;
- composite keys;
- duplicate records;
- orphan records;
- unknown references;
- negative quantities;
- invalid amounts;
- null values;
- schema consistency.

```text
Data Quality Result
7 / 7 checks PASS
```

### Step 8 — Incremental Delta MERGE

Incremental changes were processed using Delta Lake `MERGE`.

Test scenario:

```text
Existing order:
50000002 → amount updated

New order:
50000006 → inserted

Delta MERGE
     ↓
UPDATE existing record
INSERT new record
```

This demonstrates an enterprise-oriented incremental ingestion pattern rather than repeatedly rebuilding the entire dataset.

### Step 9 — Idempotence

The same incremental batch was replayed to verify that processing it multiple times does not create duplicates.

Validation result:

```text
Rows before replay : 6
Rows after replay  : 6
Duplicates         : 0

PASS
```

This property is important for pipelines that may retry messages or batches after transient failures.

### Step 10 — Gold Business Layer

Validated Silver data is aggregated into business-oriented Gold datasets.

Implemented datasets:

```text
customer_kpi
currency_kpi
daily_kpi
```

A key financial rule is respected: monetary amounts denominated in different currencies are not aggregated together without 
an explicit FX conversion.

### Step 11 — Azure SQL and Power BI Serving

Gold datasets are exposed through an Azure SQL serving layer and consumed by Power BI.

I encountered limitations when attempting direct writes from Databricks Serverless to Azure SQL.

The validated fallback architecture was:

```text
Gold Delta
    ↓
Databricks / PySpark
    ↓
Serving CSV
    ↓
Python Loader
    ↓
ODBC Driver 18
    ↓
Microsoft Entra OAuth Token
    ↓
Azure SQL
    ↓
Power BI
```

The final Azure SQL validation contained:

```text
customer_kpi : 5 rows
currency_kpi : 2 rows
daily_kpi    : 4 rows
```

### Step 12 — Infrastructure as Code

The existing Azure project infrastructure was progressively brought under Terraform management using a brownfield approach.

```text
Existing Azure Infrastructure
          ↓
Resource Inventory
          ↓
Terraform HCL
          ↓
terraform import
          ↓
terraform plan
          ↓
No changes
```

The final Terraform checkpoint managed 12 resources with zero detected drift before the whole structure was destroyed.

Terraform state files, secrets and local provider directories are excluded from Git.

---

## 5. Incremental and Idempotent Processing

The pipeline was designed around two important Data Engineering properties.

### Incremental processing

Only records newer than the previously processed watermark need to be extracted or merged.

This reduces unnecessary processing and provides a foundation for scalable ingestion.

### Idempotence

Reprocessing the same incremental input must leave the target in the same logical state.

Delta Lake `MERGE` provides the core mechanism used in the cloud implementation.

---

## 6. Medallion Architecture

### Bronze

Raw source representation.

```text
bronze/
└── sap/
    └── sales_orders/
```

### Silver

Clean, typed and validated Delta data.

Responsibilities:

- schema enforcement;
- normalization;
- Data Quality;
- deduplication;
- incremental MERGE.

### Gold

Business-ready aggregates.

```text
gold/
└── sap/
    └── sales_orders/
        ├── customer_kpi
        ├── currency_kpi
        └── daily_kpi
```

---

## 7. Security Architecture

Security was implemented without hardcoding application credentials.

Key mechanisms include:

- Azure Data Factory Managed Identity;
- Storage Blob Data Contributor RBAC;
- Databricks Access Connector;
- Managed Identity access to ADLS Gen2;
- Azure Key Vault;
- Databricks Key Vault-backed secret scope;
- dedicated service principal for Azure SQL;
- OAuth 2.0 client credentials;
- Microsoft Entra authentication;
- least-privilege SQL permissions.

Sensitive tokens and secrets are not committed to Git.

---

## 8. Infrastructure as Code

Terraform code is located in:

```text
azure/infra/
```

The infrastructure was managed as a brownfield migration because the Azure resources existed before Terraform was introduced.

Main resources included:

- Resource Group;
- ADLS Gen2;
- Bronze / Silver / Gold filesystems;
- Azure Data Factory;
- Self-Hosted Integration Runtime;
- Azure Databricks Workspace;
- Databricks Access Connector;
- Azure Key Vault;
- RBAC role assignments.

The final validation returned:

```text
No changes. Your infrastructure matches the configuration.
```

The Azure project structure was subsequently destroyed after the project evidence, code and portfolio material had been preserved.

---

## 9. Repository Structure

```text
sap-data-engineering/
├── README.md
├── azure/
│   ├── adf/
│   │   ├── dataset/
│   │   ├── linkedService/
│   │   └── pipeline/
│   ├── databricks/
│   │   └── notebooks/
│   ├── docs/
│   ├── infra/
│   ├── serving/
│   └── src/
└── local01/
    local02/
```

Local environments and sensitive runtime files are excluded from Git.

---

## 10. Technologies

**SAP / Integration**

- SAP S/4HANA concepts
- CDS / VDM concepts
- OData
- REST / HTTP
- Flask

**Data Engineering**

- Python
- pandas
- PySpark
- Delta Lake
- SQL
- SQLite

**Azure**

- Azure Data Factory
- Self-Hosted Integration Runtime
- Azure Data Lake Storage Gen2
- Azure Databricks
- Unity Catalog
- Azure Key Vault
- Azure SQL Database
- Microsoft Entra ID
- Managed Identities
- Azure RBAC

**Analytics**

- Power BI

**Infrastructure / DevOps**

- Terraform
- Azure CLI
- Git
- GitHub

---

## 11. Production Improvements

The project is a functional engineering LAB. A production implementation should additionally consider:

- private networking and Private Endpoints;
- Private DNS;
- controlled outbound connectivity;
- remote encrypted Terraform state;
- separate dev / staging / production environments;
- reusable Terraform modules;
- Key Vault Purge Protection;
- RBAC-oriented Key Vault authorization;
- centralized logging;
- Azure Monitor and alerting;
- automated Data Quality monitoring;
- CI/CD for ADF, Databricks and Terraform;
- workload-specific Databricks compute policies;
- production SAP authentication;
- formal schema evolution strategy;
- disaster recovery and backup policies.

A dedicated production Terraform design is documented separately in:

```text
docs/terraform-production.md
```

---

## 12. Key Engineering Outcomes

This project demonstrates the implementation of a complete SAP-oriented Data Engineering workflow:

- SAP/OData extraction;
- hybrid connectivity with Self-Hosted IR;
- cloud ingestion with Azure Data Factory;
- ADLS Gen2 Data Lake design;
- Bronze / Silver / Gold architecture;
- PySpark transformations;
- Delta Lake;
- Data Quality validation;
- incremental processing;
- Delta `MERGE`;
- idempotence;
- business KPI modeling;
- secure Azure authentication;
- Azure SQL serving;
- Power BI analytics;
- Terraform brownfield adoption;
- controlled cloud resource lifecycle.

The project focuses on the reliability, traceability and maintainability of the data pipeline 
rather than only demonstrating data movement.

Author : Cédric SSH - SAP data engineer.
