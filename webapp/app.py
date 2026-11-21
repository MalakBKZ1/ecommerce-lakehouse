from flask import Flask, redirect, url_for
from webapp.theme import appliquer_theme
from webapp.registry import enregistrer

def create_app():
    app = Flask(__name__)
    appliquer_theme()
    enregistrer(app)

    @app.route("/")
    def accueil():
        return redirect(url_for(f"{app.config['MODULES'][0]['slug']}.index"))

    @app.errorhandler(FileNotFoundError)
    def fichier_absent(e):
        return (f"Fichier Gold introuvable : {e.filename}. Lance l'application depuis la racine "
                "du projet, après avoir exécuté 04_gold.py.", 500)
    return app