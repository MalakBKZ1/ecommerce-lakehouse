from functools import lru_cache
import numpy as np
import seaborn as sns
from webapp.data import table
from webapp.theme import *

META = {"titre": "Clients (RFM)", "slug": "clients-rfm", "ordre": 5}

def _barres(valeurs, fmt):
    fig, ax = nouvelle_figure(5, 3.3)
    b = ax.barh(valeurs.index, valeurs.values, color=list(SEGMENTS.values()), height=.6)
    ax.invert_yaxis(); grille(ax, "x"); ax.set_xlim(0, valeurs.max() * 1.22)
    ax.bar_label(b, labels=[fmt(x) for x in valeurs.values], padding=5)
    ax.set_xticklabels([])
    return fig

@lru_cache(maxsize=None)
def construire():
    r = table("dim_client_rfm")
    seg = r.groupby("segment").agg(clients=("client_id", "count"), ca=("montant", "sum")).reindex(list(SEGMENTS)).fillna(0)
    fig = _barres(seg.clients, n)
    fig2 = _barres(seg.ca, lambda x: f"{x / 1e6:.1f} M")

    ech = r[r.montant > 0].sample(min(4000, len(r)), random_state=42)
    ech = ech.assign(x=ech.recence_jours + np.random.default_rng(42).uniform(-.35, .35, len(ech)))
    fig3, ax3 = nouvelle_figure(12, 3.8)
    sns.scatterplot(data=ech, x="x", y="montant", hue="segment", hue_order=list(SEGMENTS), palette=SEGMENTS,
                    s=16, alpha=.6, linewidth=0, ax=ax3)
    ax3.set_yscale("log"); ax3.set_xlabel("Jours depuis le dernier achat"); ax3.set_ylabel("Montant dépensé (échelle log)")
    ax3.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(.5, 1.12)); grille(ax3, "y")

    part = seg.ca["Meilleurs clients"] / seg.ca.sum()
    kpis = [("Clients acheteurs", n(len(r))), ("Dépense moyenne par client", n(r.montant.mean())),
            ("Sessions d'achat moyennes", f"{r.frequence.mean():.1f}"), ("Part du CA des meilleurs clients", f"{part:.0%}")]
    phrase = f"{n(seg.clients['Meilleurs clients'])} meilleurs clients font {part:.0%} du chiffre d'affaires."
    return phrase, kpis, [
        graphique("Clients par segment", fig, "Segments à règles : récence, fréquence et montant.", 6, BLEU),
        graphique("Chiffre d'affaires par segment", fig2, "", 6, TEAL),
        graphique("Récence et montant d'un échantillon de clients", fig3,
                  "4 000 clients tirés au hasard ; un léger décalage horizontal évite que les points se superposent.", 12, AMBRE)]