import os

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_smorest import Api

from config import Config
from errors import register_error_handlers
from models import db

migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    api = Api(app)
    register_error_handlers(app)

    from routes.assets import blp as assets_blp
    from routes.calculators import blp as calculators_blp
    from routes.health import blp as health_blp
    from routes.portfolio import blp as portfolio_blp
    from routes.prices import blp as prices_blp
    from routes.sips import blp as sips_blp
    from routes.transactions import blp as transactions_blp
    from routes.wallet import blp as wallet_blp
    from routes.watchlist import blp as watchlist_blp

    api.register_blueprint(health_blp)
    api.register_blueprint(portfolio_blp)
    api.register_blueprint(assets_blp)
    api.register_blueprint(prices_blp)
    api.register_blueprint(wallet_blp)
    api.register_blueprint(transactions_blp)
    api.register_blueprint(sips_blp)
    api.register_blueprint(watchlist_blp)
    api.register_blueprint(calculators_blp)

    if not app.config.get("TESTING") and (not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
        from jobs.price_sync import start_price_sync_job

        start_price_sync_job(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
