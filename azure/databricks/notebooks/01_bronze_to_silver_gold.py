# Databricks notebook source
bronze_path = (
    "abfss://bronze@stsapdata778c25.dfs.core.windows.net/"
    "sap/sales_orders/sales_orders.json"
)

print(bronze_path)

# COMMAND ----------

df_bronze = spark.read.json(bronze_path)

print("Nombre de lignes :", df_bronze.count())

df_bronze.printSchema()

# COMMAND ----------

df_bronze = (
    spark.read
         .option("multiLine", "true")
         .json(bronze_path)
)

print("Nombre de documents JSON :", df_bronze.count())

df_bronze.printSchema()

# COMMAND ----------

from pyspark.sql.functions import explode, col

df_orders = (
    df_bronze
    .select(explode(col("value")).alias("order"))
    .select("order.*")
)

print("Nombre de commandes SAP :", df_orders.count())

display(df_orders)

# COMMAND ----------

# DBTITLE 1,Profile SAP sales orders
print("=== PROFILING SAP SALES ORDERS ===")

if "bronze_path" not in globals():
    bronze_path = (
        "abfss://bronze@stsapdata778c25.dfs.core.windows.net/"
        "sap/sales_orders/sales_orders.json"
    )

if "df_bronze" not in globals():
    df_bronze = (
        spark.read
             .option("multiLine", "true")
             .json(bronze_path)
    )

if "df_orders" not in globals():
    from pyspark.sql.functions import explode, col

    df_orders = (
        df_bronze
        .select(explode(col("value")).alias("order"))
        .select("order.*")
    )

print("Nombre de lignes :", df_orders.count())
print("Nombre de colonnes :", len(df_orders.columns))

print("\nColonnes :")
print(df_orders.columns)

print("\nSchéma :")
df_orders.printSchema()

# COMMAND ----------

from pyspark.sql.functions import col, sum as spark_sum

df_orders.select([
    spark_sum(col(c).isNull().cast("int")).alias(c)
    for c in df_orders.columns
]).show()

# COMMAND ----------

total_rows = df_orders.count()
distinct_orders = df_orders.select("SalesOrder").distinct().count()

print("Lignes totales       :", total_rows)
print("SalesOrder distincts :", distinct_orders)
print("Doublons             :", total_rows - distinct_orders)

# COMMAND ----------

from pyspark.sql.functions import (
    col,
    to_date,
    to_timestamp
)

dq_results = {
    "SalesOrder NULL":
        df_orders.filter(col("SalesOrder").isNull()).count(),

    "SoldToParty NULL":
        df_orders.filter(col("SoldToParty").isNull()).count(),

    "Montant négatif":
        df_orders.filter(col("TotalNetAmount") < 0).count(),

    "Devise NULL":
        df_orders.filter(col("TransactionCurrency").isNull()).count(),

    "CreationDate invalide":
        df_orders.filter(
            to_date(col("CreationDate"), "yyyy-MM-dd").isNull()
        ).count(),

    "LastChangeDateTime invalide":
        df_orders.filter(
            to_timestamp(
                col("LastChangeDateTime"),
                "yyyy-MM-dd'T'HH:mm:ss"
            ).isNull()
        ).count(),

    "SalesOrder en doublon":
        df_orders.count()
        - df_orders.select("SalesOrder").distinct().count()
}

print("=== DATA QUALITY REPORT ===")

for rule, errors in dq_results.items():
    status = "PASS" if errors == 0 else "FAIL"
    print(f"{status:4} | {rule:30} | erreurs = {errors}")

# COMMAND ----------

from pyspark.sql.functions import col, to_date, to_timestamp

df_silver = (
    df_orders
    .withColumn(
        "CreationDate",
        to_date(col("CreationDate"), "yyyy-MM-dd")
    )
    .withColumn(
        "LastChangeDateTime",
        to_timestamp(
            col("LastChangeDateTime"),
            "yyyy-MM-dd'T'HH:mm:ss"
        )
    )
    .withColumn(
        "TotalNetAmount",
        col("TotalNetAmount").cast("decimal(18,2)")
    )
    .dropDuplicates(["SalesOrder"])
)

print("=== SILVER DATASET ===")
print("Nombre de commandes :", df_silver.count())

df_silver.printSchema()

# COMMAND ----------

silver_path = (
    "abfss://silver@stsapdata778c25.dfs.core.windows.net/"
    "sap/sales_orders"
)

(
    df_silver.write
    .format("delta")
    .mode("overwrite")
    .save(silver_path)
)

print("Écriture Delta Silver terminée")
print(silver_path)

# COMMAND ----------

df_silver_check = (
    spark.read
    .format("delta")
    .load(silver_path)
)

print("=== VALIDATION DELTA SILVER ===")
print("Nombre de lignes :", df_silver_check.count())

df_silver_check.printSchema()

# COMMAND ----------

display(
    df_silver_check
    .orderBy("SalesOrder")
)

# COMMAND ----------

from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, silver_path)

print("Delta Table détectée :", DeltaTable.isDeltaTable(spark, silver_path))

delta_table.history().select(
    "version",
    "timestamp",
    "operation",
    "operationParameters"
).show(truncate=False)

# COMMAND ----------

from pyspark.sql import Row
from pyspark.sql.types import DecimalType
from pyspark.sql.functions import col, to_date, to_timestamp

incremental_data = [
    Row(
        CreationDate="2026-09-01",
        LastChangeDateTime="2026-09-08T10:30:00",
        SalesOrder="50000002",
        SoldToParty="BP002",
        TotalNetAmount="2800.00",
        TransactionCurrency="EUR"
    ),
    Row(
        CreationDate="2026-09-08",
        LastChangeDateTime="2026-09-08T10:45:00",
        SalesOrder="50000006",
        SoldToParty="BP005",
        TotalNetAmount="4200.00",
        TransactionCurrency="EUR"
    )
]

df_incremental = spark.createDataFrame(incremental_data)

df_incremental = (
    df_incremental
    .withColumn("CreationDate", to_date(col("CreationDate")))
    .withColumn(
        "LastChangeDateTime",
        to_timestamp(col("LastChangeDateTime"))
    )
    .withColumn(
        "TotalNetAmount",
        col("TotalNetAmount").cast(DecimalType(18, 2))
    )
)
print("=== AVANT MERGE ===")

print("Nombre de lignes :", delta_table.toDF().count())

display(
    delta_table.toDF()
    .filter(col("SalesOrder").isin("50000002", "50000006"))
    .orderBy("SalesOrder")
)
display(df_incremental)

# COMMAND ----------

(
    delta_table.alias("target")
    .merge(
        df_incremental.alias("source"),
        "target.SalesOrder = source.SalesOrder"
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

print("MERGE Delta terminé")

# COMMAND ----------

df_after_merge = (
    spark.read
    .format("delta")
    .load(silver_path)
)

print("=== APRÈS MERGE ===")
print("Nombre de lignes :", df_after_merge.count())

display(
    df_after_merge
    .filter(col("SalesOrder").isin("50000002", "50000006"))
    .orderBy("SalesOrder")
)
delta_table.history().select(
    "version",
    "timestamp",
    "operation"
).show(truncate=False)
print("=== TEST IDEMPOTENCE ===")

count_before = delta_table.toDF().count()

(
    delta_table.alias("target")
    .merge(
        df_incremental.alias("source"),
        "target.SalesOrder = source.SalesOrder"
    )
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

count_after = delta_table.toDF().count()

print("Lignes avant replay :", count_before)
print("Lignes après replay :", count_after)

duplicate_count = (
    delta_table.toDF()
    .groupBy("SalesOrder")
    .count()
    .filter(col("count") > 1)
    .count()
)

print("Doublons SalesOrder :", duplicate_count)

if count_before == count_after and duplicate_count == 0:
    print("PASS | Traitement idempotent")
else:
    print("FAIL | Idempotence non respectée")

# COMMAND ----------

silver_path = (
    "abfss://silver@stsapdata778c25.dfs.core.windows.net/"
    "sap/sales_orders"
)

df_silver_gold = (
    spark.read
    .format("delta")
    .load(silver_path)
)

print("=== SOURCE SILVER POUR GOLD ===")
print("Nombre de commandes :", df_silver_gold.count())

df_silver_gold.printSchema()

# COMMAND ----------

from pyspark.sql.functions import (
    col,
    sum as spark_sum,
    count,
    avg,
    round as spark_round
)

df_gold_customer = (
    df_silver_gold
    .groupBy(
        "SoldToParty",
        "TransactionCurrency"
    )
    .agg(
        spark_sum("TotalNetAmount").alias("TotalRevenue"),
        count("SalesOrder").alias("OrderCount"),
        spark_round(
            avg("TotalNetAmount"), 2
        ).alias("AverageOrderValue")
    )
    .orderBy(col("TotalRevenue").desc())
)

display(df_gold_customer)

# COMMAND ----------

df_gold_currency = (
    df_silver_gold
    .groupBy("TransactionCurrency")
    .agg(
        spark_sum("TotalNetAmount").alias("TotalRevenue"),
        count("SalesOrder").alias("OrderCount"),
        spark_round(
            avg("TotalNetAmount"), 2
        ).alias("AverageOrderValue")
    )
    .orderBy(col("TotalRevenue").desc())
)

display(df_gold_currency)

# COMMAND ----------

df_gold_daily = (
    df_silver_gold
    .groupBy(
        "CreationDate",
        "TransactionCurrency"
    )
    .agg(
        spark_sum("TotalNetAmount").alias("DailyRevenue"),
        count("SalesOrder").alias("OrderCount")
    )
    .orderBy(
        "CreationDate",
        "TransactionCurrency"
    )
)

display(df_gold_daily)

# COMMAND ----------

gold_base_path = (
    "abfss://gold@stsapdata778c25.dfs.core.windows.net/"
    "sap/sales_orders/"
)

gold_customer_path = gold_base_path + "customer_kpi"
gold_currency_path = gold_base_path + "currency_kpi"
gold_daily_path = gold_base_path + "daily_kpi"

(
    df_gold_customer.write
    .format("delta")
    .mode("overwrite")
    .save(gold_customer_path)
)

(
    df_gold_currency.write
    .format("delta")
    .mode("overwrite")
    .save(gold_currency_path)
)

(
    df_gold_daily.write
    .format("delta")
    .mode("overwrite")
    .save(gold_daily_path)
)

print("=== GOLD DELTA WRITE ===")
print("PASS | customer_kpi")
print("PASS | currency_kpi")
print("PASS | daily_kpi")
df_customer_check = (
    spark.read.format("delta").load(gold_customer_path)
)

df_currency_check = (
    spark.read.format("delta").load(gold_currency_path)
)

df_daily_check = (
    spark.read.format("delta").load(gold_daily_path)
)

print("=== VALIDATION GOLD ===")
print("customer_kpi :", df_customer_check.count(), "lignes")
print("currency_kpi :", df_currency_check.count(), "lignes")
print("daily_kpi    :", df_daily_check.count(), "lignes")

display(df_customer_check)
