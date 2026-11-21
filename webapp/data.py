import os
from functools import lru_cache
from pathlib import Path
import pandas as pd

EXPORT = Path(os.environ.get("GOLD_EXPORT", "data/gold/export"))

@lru_cache(maxsize=None)
def table(nom):
    return pd.read_csv(EXPORT / f"{nom}.csv")

@lru_cache(maxsize=None)
def activite():
    # fact_activite_heure enrichi avec la date et le jour de la semaine
    d = table("dim_date")[["date_key", "date", "jour_semaine"]]
    f = table("fact_activite_heure").merge(d, on="date_key", how="left")
    f["date"] = pd.to_datetime(f["date"])
    return f