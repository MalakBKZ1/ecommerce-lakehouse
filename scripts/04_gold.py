"""
Phase 4 : modèle Gold (Silver -> dimensions, faits, sessions, RFM, exports CSV).

Usage (depuis la racine du projet, .venv activé) :
    python scripts/04_gold.py --jour 2019-10-01   # TEST sur un seul jour
    python scripts/04_gold.py                      # exécution complète (octobre)

Le mode test écrit dans data/gold_test/ et docs/gold_controls_test.json,
pour ne jamais mélanger test et résultat final.
"""
import argparse
import json
import os
from pathlib import Path

from pyspark.sql import functions as F

from session import get_spark

parser = argparse.ArgumentParser()
parser.add_argument("--jour", default=None, help="AAAA-MM-JJ : ne traiter que ce jour (test)")
args = parser.parse_args()

SILVER = "data/silver/ecommerce"
GOLD = "data/gold_test" if args.jour else "data/gold"
RAPPORT = "docs/gold_controls_test.json" if args.jour else "docs/gold_controls.json"

spark = get_spark("gold")

silver = spark.read.parquet(SILVER)
if args.jour:
    silver = silver.filter(F.col("jour") == F.lit(args.jour).cast("date"))

# ----- expressions communes
est = lambda t: (F.col("type_evenement") == t).cast("int")
achat = F.col("type_evenement") == "purchase"
achat_prix = F.when(achat & F.col("prix").isNotNull(), F.col("prix")).otherwise(0.0)

# NB : remove_from_cart est absent d'octobre 2019 : nb_retraits vaudra 0 (colonne gardée pour novembre)
mesures = [F.sum(est("view")).alias("nb_vues"),
           F.sum(est("cart")).alias("nb_paniers"),
           F.sum(est("remove_from_cart")).alias("nb_retraits"),
           F.sum(est("purchase")).alias("nb_achats"),
           F.sum((achat & F.col("prix").isNotNull()).cast("int")).alias("nb_achats_prix_valide"),
           F.sum(achat_prix).alias("ca")]

s = silver.withColumn("date_key", F.date_format("jour", "yyyyMMdd").cast("int"))

# ----- Dimensions
debut, fin = silver.agg(F.min("jour"), F.max("jour")).first()
dim_date = (spark.sql(f"SELECT explode(sequence(to_date('{debut}'), to_date('{fin}'), interval 1 day)) AS date")
            .withColumn("date_key", F.date_format("date", "yyyyMMdd").cast("int"))
            .withColumn("annee", F.year("date"))
            .withColumn("mois", F.month("date"))
            .withColumn("semaine", F.weekofyear("date"))
            .withColumn("jour_semaine", F.dayofweek("date"))  # 1 = dimanche
            .withColumn("est_weekend", F.col("jour_semaine").isin(1, 7).cast("int"))
            .withColumn("evenement", F.when(F.col("date") == F.lit("2019-11-29").cast("date"),
                                            "Black Friday").otherwise("Aucun")))

dim_heure = (spark.range(24).withColumnRenamed("id", "heure")
             .withColumn("tranche", F.when(F.col("heure") < 6, "Nuit").when(F.col("heure") < 12, "Matin")
                         .when(F.col("heure") < 18, "Après-midi").otherwise("Soir")))

dim_categorie = silver.select("categorie_n1").distinct()
dim_marque = silver.select("marque").distinct()

# ----- Faits d'activité
fact_activite_heure = s.groupBy("date_key", "heure", "categorie_n1").agg(*mesures)
fact_marque_jour = s.groupBy("date_key", "marque", "categorie_n1").agg(*mesures)

# ----- Table des sessions (intermédiaire), puis fait sessions par jour
sessions = (s.groupBy("session_id").agg(
    F.min("date_key").alias("date_key"),  # jour du premier événement
    F.max(est("cart")).alias("a_panier"),
    F.max(est("purchase")).alias("a_achete"),
    F.sum(achat_prix).alias("ca_session"),
    F.count("*").alias("nb_evenements")))
sessions.write.mode("overwrite").parquet(f"{GOLD}/sessions")
sessions = spark.read.parquet(f"{GOLD}/sessions")
print("sessions écrites")

fact_sessions_jour = sessions.groupBy("date_key").agg(
    F.count("*").alias("nb_sessions"),
    F.sum("a_panier").alias("nb_sessions_panier"),
    F.sum("a_achete").alias("nb_sessions_achat"),
    F.sum(((F.col("a_panier") == 1) & (F.col("a_achete") == 0)).cast("int")).alias("nb_sessions_abandon"),
    F.sum("ca_session").alias("ca_sessions"))

# ----- Clients acheteurs : segments RFM simplifiés
achats = s.filter(achat)
fin_ref = silver.agg(F.max("jour")).first()[0]
rfm = achats.groupBy("client_id").agg(
    F.datediff(F.lit(fin_ref), F.max("jour")).alias("recence_jours"),
    F.countDistinct("session_id").alias("frequence"),
    F.sum(achat_prix).alias("montant")).cache()
q1, q2 = rfm.approxQuantile("montant", [0.33, 0.66], 0.01)

dim_client_rfm = (rfm
    .withColumn("score_r", F.when(F.col("recence_jours") <= 7, 3).when(F.col("recence_jours") <= 21, 2).otherwise(1))
    .withColumn("score_f", F.when(F.col("frequence") >= 3, 3).when(F.col("frequence") == 2, 2).otherwise(1))
    .withColumn("score_m", F.when(F.col("montant") > q2, 3).when(F.col("montant") > q1, 2).otherwise(1))
    .withColumn("score", F.col("score_r") + F.col("score_f") + F.col("score_m"))
    .withColumn("segment", F.when(F.col("score") >= 8, "Meilleurs clients")
                .when(F.col("score") >= 6, "Clients réguliers")
                .when(F.col("score") >= 4, "À réactiver").otherwise("Occasionnels")))

# ----- Écriture + exports CSV pour Power BI
os.makedirs(f"{GOLD}/export", exist_ok=True)
tables = {"dim_date": dim_date, "dim_heure": dim_heure, "dim_categorie": dim_categorie,
          "dim_marque": dim_marque, "dim_client_rfm": dim_client_rfm,
          "fact_activite_heure": fact_activite_heure, "fact_marque_jour": fact_marque_jour,
          "fact_sessions_jour": fact_sessions_jour}
lire = spark.read.parquet
nb_lignes = {}
for nom, df in tables.items():
    df.write.mode("overwrite").parquet(f"{GOLD}/{nom}")
    ecrit = lire(f"{GOLD}/{nom}")
    nb_lignes[nom] = ecrit.count()
    # utf-8-sig : Power BI reconnaît bien l'encodage (accents de "Après-midi", "À réactiver")
    ecrit.toPandas().to_csv(f"{GOLD}/export/{nom}.csv", index=False, encoding="utf-8-sig")
    print(nom, "écrit :", f"{nb_lignes[nom]:,}", "lignes")

# ----- Contrôles de cohérence
evts = F.col("nb_vues") + F.col("nb_paniers") + F.col("nb_retraits") + F.col("nb_achats")
total = lambda table, expr: lire(f"{GOLD}/{table}").agg(F.sum(expr)).first()[0]

n_silver = silver.count()
ev_h, ev_m = total("fact_activite_heure", evts), total("fact_marque_jour", evts)
ca_h, ca_m = total("fact_activite_heure", F.col("ca")), total("fact_marque_jour", F.col("ca"))
ca_s = total("fact_sessions_jour", F.col("ca_sessions"))
n_sess_fait = total("fact_sessions_jour", F.col("nb_sessions"))
n_sess_silver = silver.select("session_id").distinct().count()
achats_h = total("fact_activite_heure", F.col("nb_achats"))
achats_silver = silver.filter(achat).count()
retraits = total("fact_activite_heure", F.col("nb_retraits"))
segments = {r["segment"]: r["count"] for r in lire(f"{GOLD}/dim_client_rfm").groupBy("segment").count().collect()}

controles = {
    "mode": f"test {args.jour}" if args.jour else "complet",
    "evenements": {"silver": n_silver, "fait_heure": ev_h, "fait_marque": ev_m,
                   "ok": n_silver == ev_h == ev_m},
    "achats": {"silver": achats_silver, "fait_heure": achats_h, "ok": achats_silver == achats_h},
    "ca": {"fait_heure": round(ca_h, 2), "fait_marque": round(ca_m, 2), "fait_sessions": round(ca_s, 2),
           "ok": max(ca_h, ca_m, ca_s) - min(ca_h, ca_m, ca_s) < 1.0},  # tolérance : arrondis des décimaux
    "sessions": {"fait_sessions": n_sess_fait, "silver_distinct": n_sess_silver,
                 "ok": n_sess_fait == n_sess_silver},
    "nb_retraits_total": retraits,
    "segments_rfm": segments,
    "nb_lignes_tables": nb_lignes,
}
Path("docs").mkdir(exist_ok=True)
Path(RAPPORT).write_text(json.dumps(controles, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(controles, indent=2, ensure_ascii=False))
tout_ok = all(controles[k]["ok"] for k in ["evenements", "achats", "ca", "sessions"])
print("CONTROLES :", "TOUS OK" if tout_ok else "ECART DETECTE (voir ci-dessus)")
print("rapport écrit :", RAPPORT)