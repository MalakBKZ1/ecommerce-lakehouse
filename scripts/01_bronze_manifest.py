import hashlib, json
from datetime import datetime
from pathlib import Path

DOSSIER = Path("data/bronze/ecommerce")  # 2019-Oct.csv (et 2019-Nov.csv en mode standard)


def sha256(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()


def nb_lignes(chemin):
    with open(chemin, "rb") as f:  # pas de texte multi-lignes : 1 ligne = 1 événement
        return sum(bloc.count(b"\n") for bloc in iter(lambda: f.read(8 * 1024 * 1024), b"")) - 1


fichiers = {}
for csv in sorted(DOSSIER.glob("*.csv")):
    with open(csv, encoding="utf-8") as f:
        entete = f.readline().strip().split(",")
    fichiers[csv.name] = {"taille_go": round(csv.stat().st_size / 1e9, 3),
                          "nb_lignes": nb_lignes(csv),
                          "sha256": sha256(csv),
                          "entete": entete}
    print(csv.name, fichiers[csv.name]["taille_go"], "Go,", fichiers[csv.name]["nb_lignes"], "lignes")

manifeste = {"source": "Kaggle : mkechinov/ecommerce-behavior-data-from-multi-category-store",
             "date_manifeste": datetime.now().isoformat(timespec="seconds"),
             "fichiers": fichiers}
Path("docs").mkdir(exist_ok=True)
Path("docs/bronze_manifest.json").write_text(
    json.dumps(manifeste, indent=2, ensure_ascii=False), encoding="utf-8")
print("manifeste écrit : docs/bronze_manifest.json")