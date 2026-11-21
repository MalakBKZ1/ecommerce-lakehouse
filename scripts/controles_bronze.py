from session import get_spark
from pyspark.sql import functions as F

spark = get_spark()
brut = spark.read.parquet("data/bronze_parquet/ecommerce")
print(f"{brut.count():,} lignes")
brut.printSchema()
brut.groupBy("jour").count().orderBy("jour").show(40)
brut.groupBy("event_type").count().show()
brut.select(F.sum(F.col("brand").isNull().cast("int")).alias("marque_vide"),
            F.sum(F.col("category_code").isNull().cast("int")).alias("categorie_vide"),
            F.sum((F.col("price") <= 0).cast("int")).alias("prix_nul_ou_negatif")).show()
brut.select("category_code").distinct().limit(40).show(40, truncate=False)