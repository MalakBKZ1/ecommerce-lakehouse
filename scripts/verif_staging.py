import json
from session import get_spark

spark = get_spark("verif")
df = spark.read.parquet("data/bronze_parquet/ecommerce")
n = df.count()

manifeste = json.load(open("docs/bronze_manifest.json", encoding="utf-8"))
attendu = sum(f["nb_lignes"] for f in manifeste["fichiers"].values())

print("staging :", f"{n:,}", "| manifeste :", f"{attendu:,}", "| égal :", n == attendu)
print("jours :", df.select("jour").distinct().count())