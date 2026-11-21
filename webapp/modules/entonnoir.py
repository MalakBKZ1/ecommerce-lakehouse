from functools import lru_cache
import seaborn as sns
from matplotlib.ticker import PercentFormatter
from webapp.data import activite
from webapp.theme import *

META = {"titre": "Entonnoir", "slug": "entonnoir", "ordre": 1}

@lru_cache(maxsize=None)
def construire():
    f = activite()
    v, p, a, ca = f.nb_vues.sum(), f.nb_paniers.sum(), f.nb_achats.sum(), f.ca.sum()

    fig, ax = nouvelle_figure(7, 3.3)
    barres = ax.barh(["Vues", "Paniers", "Achats"], [v, p, a], color=[BLEU, TEAL, AMBRE], height=.6)
    ax.invert_yaxis(); grille(ax, "x"); ax.set_xlim(0, v * 1.2)
    ax.bar_label(barres, labels=[n(v), n(p), n(a)], padding=6)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x / 1e6:.0f} M")

    c = f.groupby("categorie_n1")[["nb_vues", "nb_achats"]].sum()
    c = c[c.nb_vues > 0].assign(taux=lambda d: d.nb_achats / d.nb_vues)
    c = c.sort_values("taux", ascending=False).reset_index()
    fig2, ax2 = nouvelle_figure(5, 3.3)
    sns.barplot(data=c, x="taux", y="categorie_n1", color=TEAL, ax=ax2)
    grille(ax2, "x"); ax2.set_xlabel(""); ax2.set_ylabel("")
    ax2.xaxis.set_major_formatter(PercentFormatter(1, decimals=1))

    kpis = [("Vues", n(v)), ("Paniers", n(p)), ("Achats", n(a)),
            ("Chiffre d'affaires", n(ca)), ("Conversion vues → achats", f"{a / v:.2%}")]
    phrase = f"Sur {n(v)} consultations, seulement {a / v:.2%} se terminent par un achat."
    return phrase, kpis, [
        graphique("Du produit consulté à l'achat", fig,
                  "Volumes d'événements : ce n'est pas un parcours client étape par étape.", 7, BLEU),
        graphique("Conversion par catégorie", fig2, "Achats divisés par vues, par catégorie.", 5, TEAL)]