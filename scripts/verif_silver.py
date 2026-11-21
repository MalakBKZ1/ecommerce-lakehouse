"""
Vérifications du Silver (section 3.4 de la documentation).

Usage :
    python scripts/verif_silver.py data/silver_test/ecommerce   # après le test
    python scripts/verif_silver.py                               # Silver complet
"""
import sys
from pyspark.sql import functions as F
from session import get_spark

chemin = sys.argv[1] if len(sys.argv) > 1 else "data/silver/ecommerce"
spark = get_spark("verif_silver")
s = spark.read.parquet(chemin)

n = s.count()
print(f"\n=== {chemin} : {n:,} lignes ===")
s.printSchema()

print("--- événements par jour")
s.groupBy("jour").count().orderBy("jour").show(40)

print("--- types d'événements (4 attendus)")
s.groupBy("type_evenement").count().show()

print("--- catégories niveau 1")
s.groupBy("categorie_n1").count().orderBy(F.desc("count")).show(30, truncate=False)

print("--- première et dernière date (doivent être dans la période)")
s.select(F.min("evt_ts"), F.max("evt_ts")).show(truncate=False)

print("--- achats : somme des prix valides et nombre")
s.filter(F.col("type_evenement") == "purchase").agg(F.sum("prix"), F.count("*")).show()

print("--- valeurs nulles dans les colonnes clés (0 attendu partout)")
cles = ["evt_ts", "type_evenement", "produit_id", "client_id", "session_id",
        "marque", "categorie_n1", "jour", "heure"]
s.select([F.sum(F.col(c).isNull().cast("int")).alias(c) for c in cles]).show()

if n < 5_000_000:  # contrôle coûteux : seulement sur un petit volume (test)
    print("--- doublons restants (0 attendu) :", n - s.dropDuplicates().count())