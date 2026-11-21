from functools import lru_cache
import pandas as pd
import matplotlib.dates as mdates
import seaborn as sns
from matplotlib.ticker import PercentFormatter
from webapp.data import activite
from webapp.theme import *

META = {"titre": "Rythme des achats", "slug": "rythme", "ordre": 2}

@lru_cache(maxsize=None)
def construire():
    f = activite()
    j = f.groupby("date", as_index=False).agg(ca=("ca", "sum"), achats=("nb_achats", "sum"))

    fig, ax = nouvelle_figure(12, 3.4)
    for d in j.date[j.date.dt.weekday >= 5]:
        ax.axvspan(d - pd.Timedelta(hours=12), d + pd.Timedelta(hours=12), color=GRID, alpha=.7, lw=0)
    ax.plot(j.date, j.ca, color=BLEU, lw=2.2)
    ax.fill_between(j.date, j.ca, color=BLEU, alpha=.08)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.yaxis.set_major_formatter(lambda x, _: f"{x / 1e6:.1f} M"); grille(ax, "y")
    ax.margins(x=.01)

    h = f.groupby(["date", "jour_semaine", "heure"]).nb_achats.sum().reset_index()
    pt = (h.pivot_table(index="jour_semaine", columns="heure", values="nb_achats", aggfunc="mean")
          .reindex([2, 3, 4, 5, 6, 7, 1]))
    pt.index = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    fig2, ax2 = nouvelle_figure(8, 3.6)
    sns.heatmap(pt, cmap=sns.light_palette(BLEU, as_cmap=True), ax=ax2, linewidths=1.5,
                linecolor="white", cbar_kws={"shrink": .8})
    ax2.grid(False); ax2.set_xlabel("Heure (UTC)"); ax2.set_ylabel("")

    tr = (f.assign(tranche=pd.cut(f.heure, [-1, 5, 11, 17, 23], labels=["Nuit", "Matin", "Après-midi", "Soir"]))
          .groupby("tranche", observed=True).nb_achats.sum())
    fig3, ax3 = nouvelle_figure(4, 3.6)
    b = ax3.bar(tr.index.astype(str), tr / tr.sum(), color=[GRIS, TEAL, AMBRE, BLEU], width=.62)
    ax3.bar_label(b, labels=[f"{x:.0%}" for x in tr / tr.sum()], padding=4)
    ax3.yaxis.set_major_formatter(PercentFormatter(1, decimals=0)); grille(ax3, "y")
    ax3.set_ylim(0, (tr / tr.sum()).max() * 1.2)

    pic = j.loc[j.ca.idxmax()]
    hp = f.groupby("heure").nb_achats.sum().idxmax()
    we = f[f.jour_semaine.isin([1, 7])].ca.sum() / f.ca.sum()
    kpis = [("Meilleur jour", f"{pic.date:%d/%m}"), ("Heure de pointe (UTC)", f"{hp} h"),
            ("CA moyen par jour", n(j.ca.mean())), ("Part du week-end dans le CA", f"{we:.0%}")]
    phrase = f"Les achats culminent à {hp} h UTC ; le meilleur jour est le {pic.date:%d/%m}."
    return phrase, kpis, [
        graphique("Chiffre d'affaires par jour", fig, "Les bandes grises marquent les week-ends.", 12, BLEU),
        graphique("Achats moyens par jour de la semaine et par heure", fig2,
                  "Moyenne sur les jours du mois ; heures en UTC, pas en heure locale.", 8, TEAL),
        graphique("Achats par tranche horaire", fig3, "Part des achats du mois (heures UTC).", 4, AMBRE)]