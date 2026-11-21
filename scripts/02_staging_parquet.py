import shutil
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import (StructType, StructField, StringType, LongType, DoubleType)
from session import get_spark

CSV = "data/bronze/ecommerce/*.csv"        # un ou deux fichiers mensuels
SORTIE = "data/bronze_parquet/ecommerce"
MAX_LIGNES = None                       # None pour tout le fichier

spark = get_spark("staging")

schema = StructType([
    StructField("event_time", StringType()),
    StructField("event_type", StringType()),
    StructField("product_id", LongType()),
    StructField("category_id", LongType()),
    StructField("category_code", StringType()),
    StructField("brand", StringType()),
    StructField("price", DoubleType()),
    StructField("user_id", LongType()),
    StructField("user_session", StringType()),
])

df = spark.read.csv(CSV, header=True, schema=schema)   # schéma explicite : pas de passe d'inférence
if MAX_LIGNES:
    df = df.limit(MAX_LIGNES)

df = df.withColumn("jour", F.substring("event_time", 1, 10))  # texte AAAA-MM-JJ, sert au partitionnement

if Path(SORTIE).exists():
    shutil.rmtree(SORTIE)

df.write.partitionBy("jour").parquet(SORTIE)
print("terminé :", f"{spark.read.parquet(SORTIE).count():,}", "lignes")