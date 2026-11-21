import io
import matplotlib as mpl
mpl.use("Agg")                       # rendu sans fenêtre
import seaborn as sns
from flask import render_template
from matplotlib.figure import Figure

INK, GRID, MUTE = "#14213D", "#E3E7EF", "#5B667A"
BLEU, TEAL, AMBRE, ROSE, GRIS = "#3B3BDB", "#0FA3A3", "#F2A33A", "#D6336C", "#9AA4B8"
SEGMENTS = {"Meilleurs clients": BLEU, "Clients réguliers": TEAL,
            "À réactiver": AMBRE, "Occasionnels": GRIS}

def appliquer_theme():
    sns.set_theme(style="white", rc={
        "font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none",
        "text.color": INK, "axes.labelcolor": MUTE, "xtick.color": MUTE, "ytick.color": MUTE,
        "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.axisbelow": True, "axes.labelsize": 9})

def nouvelle_figure(largeur=7, hauteur=3.6):
    fig = Figure(figsize=(largeur, hauteur))      # Figure, pas pyplot : sûr en web
    return fig, fig.subplots()

def grille(ax, axe="y"):
    ax.grid(False)
    ax.grid(axis=axe)

def svg(fig):
    tampon = io.StringIO()
    fig.savefig(tampon, format="svg", bbox_inches="tight", transparent=True)
    texte = tampon.getvalue()
    return texte[texte.index("<svg"):]

def n(x, d=0):
    return f"{x:,.{d}f}".replace(",", "\u00a0")

def graphique(titre, fig, note="", span=6, couleur=BLEU):
    return {"titre": titre, "svg": svg(fig), "note": note, "span": span, "couleur": couleur}

def rendre(meta, phrase, kpis, graphiques):
    return render_template("module.html", meta=meta, phrase=phrase, kpis=kpis, graphiques=graphiques)