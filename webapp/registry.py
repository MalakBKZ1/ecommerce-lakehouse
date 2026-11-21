import importlib, pkgutil
from flask import Blueprint
from webapp import modules
from webapp.theme import rendre

def enregistrer(app):
    # Chaque fichier de webapp/modules/ définit META et construire() : il devient une page.
    metas = []
    for info in pkgutil.iter_modules(modules.__path__):
        mod = importlib.import_module(f"webapp.modules.{info.name}")
        slug = mod.META["slug"]
        bp = Blueprint(slug, __name__, url_prefix=f"/{slug}")
        bp.add_url_rule("/", "index", lambda mod=mod: rendre(mod.META, *mod.construire()))
        app.register_blueprint(bp)
        metas.append(mod.META)
    app.config["MODULES"] = sorted(metas, key=lambda m: m["ordre"])

    @app.context_processor
    def injecter():
        return {"modules": app.config["MODULES"]}