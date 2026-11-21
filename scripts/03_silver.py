"""
Phase 3 : nettoyage Silver (Bronze staging Parquet -> Silver Parquet).

Usage (depuis la racine du projet, .venv activé) :
    python scripts/03_silver.py --jour 2019-10-01   # TEST sur un seul jour
    python scripts/03_silver.py                      # exécution complète (octobre)

Le mode test écrit dans data/silver_test/ et docs/silver_quality_report_test.json,
pour ne jamais mélanger test et résultat final.
"""
import argparse
import json
from pathlib import Path

from pyspark.sql import functions as F

from session import get_spark

parser = argparse.ArgumentParser()
parser.add_argument("--jour", default=None, help="AAAA-MM-JJ : ne traiter que ce jour (test)")
args = parser.parse_args()

SOURCE = "data/bronze_parquet/ecommerce"
DEBUT, FIN = "2019-10-01", "2019-11-01"  # FIN exclue ; "2019-12-01" si octobre + novembre
TYPES = ["view", "cart", "remove_from_cart", "purchase"]

if args.jour:
    SILVER = "data/silver_test/ecommerce"
    RAPPORT = "docs/silver_quality_report_test.json"
else:
    SILVER = "data/silver/ecommerce"
    RAPPORT = "docs/silver_quality_report.json"

spark = get_spark("silver")
brut = spark.read.parquet(SOURCE)
if args.jour:
    # filtre sur la partition : Spark ne lit que le dossier de ce jour
    brut = brut.filter(F.col("jour").cast("string") == args.jour)

# ----- typage et normalisation
ts = F.to_timestamp(F.regexp_replace("event_time", r" UTC$", ""), "yyyy-MM-dd HH:mm:ss")
cat = F.lower(F.trim(F.col("category_code")))
marque = F.lower(F.trim(F.col("brand")))
parties = F.split(F.col("categorie_code"), r"\.")  # appliqué après le select ci-dessous

df = (brut.select(
        ts.alias("evt_ts"),
        F.lower(F.trim("event_type")).alias("type_evenement"),
        F.col("product_id").alias("produit_id"),
        F.col("category_id").alias("categorie_id"),
        F.when(cat == "", None).otherwise(cat).alias("categorie_code"),
        F.when(marque.isNull() | (marque == ""), "inconnue").otherwise(marque).alias("marque"),
        F.when(F.col("price") > 0, F.col("price")).alias("prix"),  # prix <= 0 ou absent : NULL
        F.col("user_id").alias("client_id"),
        F.col("user_session").alias("session_id"))
      .withColumn("jour", F.to_date("evt_ts"))
      .withColumn("heure", F.hour("evt_ts"))
      .withColumn("categorie_n1", F.coalesce(parties.getItem(0), F.lit("inconnue")))
      .withColumn("categorie_n2", F.coalesce(parties.getItem(1), F.lit("inconnue"))))

# ----- règles de rejet (une seule cause par ligne : la première qui s'applique)
motif = (F.when(F.col("evt_ts").isNull(), "date_invalide")
         .when(F.col("type_evenement").isNull() | ~F.col("type_evenement").isin(TYPES), "type_inconnu")
         .when(F.col("client_id").isNull() | F.col("produit_id").isNull()
               | F.col("session_id").isNull(), "cle_manquante")
         .when((F.col("evt_ts") < F.lit(DEBUT).cast("timestamp"))
               | (F.col("evt_ts") >= F.lit(FIN).cast("timestamp")), "hors_periode"))
df = df.withColumn("motif_rejet", motif)

motifs = {(r["motif_rejet"] or "conservees"): r["count"]
          for r in df.groupBy("motif_rejet").count().collect()}
n_brut = sum(motifs.values())
n_conservees = motifs.get("conservees", 0)
n_rejetees = n_brut - n_conservees
print("lignes lues :", f"{n_brut:,}", "| motifs :", motifs)

# ----- doublons exacts (sur toutes les colonnes) puis écriture
valides = df.filter(F.col("motif_rejet").isNull()).drop("motif_rejet")
(valides.dropDuplicates()
        .repartition(8, "jour")
        .write.mode("overwrite").partitionBy("jour").parquet(SILVER))

# ----- rapport qualité
s = spark.read.parquet(SILVER)
stats = s.agg(
    F.count("*").alias("lignes_silver"),
    F.approx_count_distinct("client_id").alias("clients_distincts"),
    F.approx_count_distinct("session_id").alias("sessions_distinctes"),
    F.sum(F.col("prix").isNull().cast("int")).alias("prix_invalides"),
    F.sum((F.col("marque") == "inconnue").cast("int")).alias("marque_inconnue"),
    F.sum((F.col("categorie_n1") == "inconnue").cast("int")).alias("categorie_inconnue"),
).first().asDict()

stats["doublons_supprimes"] = n_conservees - stats["lignes_silver"]
# réconciliation : staging = silver + rejets + doublons
stats["reconciliation_ok"] = (n_brut == stats["lignes_silver"] + n_rejetees + stats["doublons_supprimes"])

rapport = {
    "mode": f"test {args.jour}" if args.jour else "complet",
    "lignes_staging": n_brut,
    "rejets_total": n_rejetees,
    "motifs": motifs,
    "stats": stats,
    "pourcentages": {
        "rejets": round(100 * n_rejetees / n_brut, 4) if n_brut else None,
        "doublons": round(100 * stats["doublons_supprimes"] / n_brut, 4) if n_brut else None,
        "marque_inconnue": round(100 * stats["marque_inconnue"] / stats["lignes_silver"], 2),
        "categorie_inconnue": round(100 * stats["categorie_inconnue"] / stats["lignes_silver"], 2),
        "prix_invalides": round(100 * stats["prix_invalides"] / stats["lignes_silver"], 2),
    },
    "periode": [DEBUT, FIN],
}
Path("docs").mkdir(exist_ok=True)
Path(RAPPORT).write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(rapport, indent=2, ensure_ascii=False))
print("rapport écrit :", RAPPORT)