# Lakehouse e-commerce : comportement d'achat (REES46, octobre 2019)

Projet Big Data de bout en bout : une chaîne de traitement **Bronze / Silver / Gold** avec PySpark sur 42 millions d'événements d'une boutique en ligne, suivie d'une **application web modulaire** de tableaux de bord (Flask, seaborn, matplotlib).

## Objectif

Une boutique en ligne multi-catégories reçoit beaucoup de visites, mais peu aboutissent à un achat. Le projet aide le gérant à répondre à cinq questions :

1. Où perd-on les clients ? (entonnoir de conversion)
2. Quand achètent-ils ? (jours et heures)
3. Qu'est-ce qui rapporte ? (catégories et marques)
4. Combien de paniers sont abandonnés ? (sessions)
5. Qui sont les meilleurs clients ? (segmentation RFM)

## Architecture

```
CSV Kaggle -> Bronze (brut + manifeste SHA-256 + Parquet) -> Silver (nettoyé, dédoublonné)
           -> Gold (constellation Kimball, 8 tables) -> Application web
                                                     -> Db2 Lite (agrégat journalier)
```

| Couche | Rôle |
|---|---|
| Bronze | CSV d'origine jamais modifié, manifeste d'intégrité, staging Parquet partitionné par jour |
| Silver | Typage, rejets chiffrés, doublons exacts supprimés, prix invalides mis à NULL |
| Gold | 5 dimensions et 3 faits (activité par heure, marque par jour, sessions par jour), clients RFM |
| Application web | Un module par thème, lit uniquement les exports CSV du Gold |

## Application web : les modules

| Module | Contenu |
|---|---|
| Entonnoir | vues, paniers, achats ; conversion par catégorie |
| Rythme des achats | CA par jour, heatmap jour x heure (UTC), tranches horaires |
| Catégories et marques | top 10 des marques, CA et prix moyen par catégorie |
| Sessions et abandon | taux d'abandon, conversion des sessions |
| Clients (RFM) | segments, CA par segment, nuage récence / montant |
| Contrôle des totaux | compare les totaux affichés à ceux du Gold |

Pour ajouter un module, créer un fichier dans `webapp/modules/` avec `META` et `construire()` : la barre latérale se met à jour toute seule.

## Structure du dépôt

```
scripts/      pipeline Spark (session, manifeste, staging, silver, gold, chargement Db2)
sql/          création de la table Db2
docs/         manifeste Bronze, rapports qualité et contrôles
notebooks/    analyse avancée
webapp/       application web (app.py, data.py, theme.py, registry.py, modules/, templates/, static/)
data/         données locales (non versionnées)
```

## Prérequis

- Python 3.10 ou plus
- Java 17 ou plus et PySpark (uniquement pour reproduire le pipeline)
- Les données : télécharger `2019-Oct.csv` depuis Kaggle (« eCommerce behavior data from multi category store », REES46) dans `data/bronze/ecommerce/`. **Les données ne sont pas incluses dans ce dépôt.** Relire la licence sur la page Kaggle.

## Lancer l'application web

Prérequis : les exports du Gold doivent exister dans `data/gold/export/` (produits par `scripts/04_gold.py`).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-webapp.txt
python -m flask --app webapp.app run --debug
```

Ouvrir http://127.0.0.1:5000. L'application doit être lancée depuis la racine du projet.

## Reproduire le pipeline

```powershell
python scripts/01_bronze_manifest.py
python scripts/02_staging_parquet.py
python scripts/03_silver.py
python scripts/04_gold.py
python scripts/05_load_db2.py   # optionnel : nécessite config.env (non versionné)
```

## Règles du projet

1. Le fichier Bronze n'est jamais modifié.
2. Chaque ligne rejetée, supprimée ou corrigée est comptée.
3. Les totaux sont vérifiés à chaque étape : CSV, staging, Silver, Gold, Db2, application.

## Limites

- Le chiffre d'affaires est la somme des prix catalogue (ni quantité, ni remise, ni numéro de commande).
- L'abandon de panier est une borne haute : le client a pu acheter dans une autre session.
- Un seul mois de données : pas de saisonnalité annuelle.
- Les heures sont en UTC : le pays de la boutique n'est pas précisé.

## Technologies

PySpark, Parquet, pandas, Flask, seaborn, matplotlib, IBM Db2 (Lite), Git.

## Auteure

Malak, Master Data Science.

## Source des données

Kaggle, « eCommerce behavior data from multi category store » (Michael Kechinov, collecte REES46 / Open CDP).