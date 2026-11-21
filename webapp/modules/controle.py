from functools import lru_cache
from webapp.data import activite, table
from webapp.theme import n

META = {"titre": "Contrôle des totaux", "slug": "controle", "ordre": 9}
CA = "Chiffre d'affaires"
ATTENDU = {"Événements": 42_418_542, "Achats": 742_773, CA: 229_933_212.63, "Sessions": 9_244_421}

@lru_cache(maxsize=None)
def construire():
    f = activite()
    obtenu = {"Événements": f[["nb_vues", "nb_paniers", "nb_retraits", "nb_achats"]].sum().sum(),
              "Achats": f.nb_achats.sum(), CA: f.ca.sum(),
              "Sessions": table("fact_sessions_jour").nb_sessions.sum()}
    kpis, ok = [], True
    for nom, att in ATTENDU.items():
        d = 2 if nom == CA else 0
        bon = abs(obtenu[nom] - att) < (0.05 if nom == CA else 0.5)
        ok &= bon
        kpis.append((f"{nom} (attendu : {n(att, d)})", n(obtenu[nom], d), "ok" if bon else "ko"))
    phrase = ("Tous les totaux affichés concordent avec ceux du Gold." if ok
              else "Un ou plusieurs totaux ne concordent pas avec le Gold.")
    return phrase, kpis, []