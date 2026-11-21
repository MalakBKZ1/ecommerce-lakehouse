from functools import lru_cache
import pandas as pd
import matplotlib.dates as mdates
from matplotlib.ticker import PercentFormatter
from webapp.data import table
from webapp.theme import *

META = {"titre": "Sessions et abandon", "slug": "sessions-abandon", "ordre": 4}

def _courbe(ax, x, y, couleur, moyenne):
    ax.plot(x, y, color=couleur, lw=2.2)
    ax.axhline(moyenne, color=MUTE, lw=1, ls="--")
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m")); grille(ax, "y"); ax.margins(x=.01)

@lru_cache(maxsize=None)
def construire():
    s = table("fact_sessions_jour").merge(table("dim_date")[["date_key", "date"]], on="date_key")
    s["date"] = pd.to_datetime(s["date"]); s = s.sort_values("date")
    s["abandon"] = s.nb_sessions_abandon / s.nb_sessions_panier
    s["conv"] = s.nb_sessions_achat / s.nb_sessions
    tot = s[["nb_sessions", "nb_sessions_panier", "nb_sessions_achat", "nb_sessions_abandon", "ca_sessions"]].sum()
    ab, cv = tot.nb_sessions_abandon / tot.nb_sessions_panier, tot.nb_sessions_achat / tot.nb_sessions

    fig, ax = nouvelle_figure(7, 3.4); _courbe(ax, s.date, s.abandon, ROSE, ab)
    fig2, ax2 = nouvelle_figure(5, 3.4); _courbe(ax2, s.date, s.conv, TEAL, cv)

    fig3, ax3 = nouvelle_figure(12, 3.4)
    for col, nom, coul in [("nb_sessions", "Sessions", BLEU), ("nb_sessions_panier", "Avec panier", AMBRE),
                           ("nb_sessions_achat", "Avec achat", TEAL)]:
        ax3.plot(s.date, s[col], color=coul, lw=2.2, label=nom)
    ax3.yaxis.set_major_formatter(lambda x, _: f"{x / 1e3:.0f} k")
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m")); grille(ax3, "y")
    ax3.legend(frameon=False, ncol=3, loc="upper left"); ax3.margins(x=.01)

    kpis = [("Sessions", n(tot.nb_sessions)), ("Conversion des sessions", f"{cv:.2%}"),
            ("Abandon de panier", f"{ab:.1%}"), ("CA par session d'achat", n(tot.ca_sessions / tot.nb_sessions_achat))]
    phrase = f"{ab:.0%} des sessions avec un panier se terminent sans achat."
    return phrase, kpis, [
        graphique("Taux d'abandon de panier par jour", fig, "Tirets : moyenne du mois. C'est une borne haute : le client a pu acheter dans une autre session.", 7, ROSE),
        graphique("Conversion des sessions par jour", fig2, "Sessions avec achat divisées par sessions.", 5, TEAL),
        graphique("Sessions, paniers et achats par jour", fig3, "Une session est rattachée au jour de son premier événement.", 12, BLEU)]