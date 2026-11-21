from functools import lru_cache
import pandas as pd
import seaborn as sns
from webapp.data import activite, table
from webapp.theme import *

META = {"titre": "Catégories et marques", "slug": "categories-marques", "ordre": 3}

@lru_cache(maxsize=None)
def construire():
    m, f = table("fact_marque_jour"), activite()
    b = m[m.marque != "inconnue"].groupby("marque").ca.sum().nlargest(10).reset_index()
    fig, ax = nouvelle_figure(7, 3.8)
    sns.barplot(data=b, x="ca", y="marque", color=BLEU, ax=ax)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x / 1e6:.0f} M")
    grille(ax, "x"); ax.set_xlabel(""); ax.set_ylabel("")

    c = f.groupby("categorie_n1").agg(ca=("ca", "sum"), n=("nb_achats_prix_valide", "sum"))
    c = c[c.n > 0].assign(prix=lambda d: d.ca / d.n).sort_values("ca", ascending=False).reset_index()
    fig2, ax2 = nouvelle_figure(5, 3.8)
    sns.barplot(data=c, x="ca", y="categorie_n1", color=TEAL, ax=ax2)
    ax2.xaxis.set_major_formatter(lambda x, _: f"{x / 1e6:.0f} M")
    grille(ax2, "x"); ax2.set_xlabel(""); ax2.set_ylabel("")

    fig3, ax3 = nouvelle_figure(12, 3.2)
    sns.barplot(data=c.sort_values("prix", ascending=False), x="categorie_n1", y="prix", color=AMBRE, ax=ax3)
    ax3.bar_label(ax3.containers[0], fmt="%.0f", padding=3)
    grille(ax3, "y"); ax3.set_xlabel(""); ax3.set_ylabel("")
    ax3.tick_params(axis="x", rotation=25)

    part = b.ca.sum() / m.ca.sum()
    kpis = [("Marques actives", n(m.marque.nunique())), ("Catégories", n(c.shape[0])),
            ("Prix moyen d'un article acheté", n(c.ca.sum() / c.n.sum())),
            ("Part du CA des 10 premières marques", f"{part:.0%}")]
    phrase = f"{b.marque[0].capitalize()} arrive en tête, et dix marques font {part:.0%} du chiffre d'affaires."
    return phrase, kpis, [
        graphique("Dix marques qui rapportent le plus", fig, "Les achats sans marque connue sont exclus du classement.", 7, BLEU),
        graphique("Chiffre d'affaires par catégorie", fig2, "", 5, TEAL),
        graphique("Prix moyen d'un article acheté, par catégorie", fig3,
                  "Prix catalogue : sans remise ni quantité.", 12, AMBRE)]