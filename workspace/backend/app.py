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

    api = Api(app)
    CORS(app, origins='*', allow_headers='*', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    register_error_handlers(app)

    from routes.analytics import blp as analytics_blp
    from routes.assets import blp as assets_blp
    from routes.calculators import blp as calculators_blp
    from routes.goals import blp as goals_blp
    from routes.alerts import blp as alerts_blp
    from routes.health import blp as health_blp
    from routes.market import blp as market_blp
    from routes.news import blp as news_blp
    from routes.portfolio import blp as portfolio_blp
    from routes.prices import blp as prices_blp
    from routes.recommendations import blp as recommendations_blp
    from routes.ai import blp as ai_blp
    from routes.search import blp as search_blp
    from routes.sips import blp as sips_blp
    from routes.tags import blp as tags_blp
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
    api.register_blueprint(search_blp)
    api.register_blueprint(tags_blp)
    api.register_blueprint(news_blp)
    api.register_blueprint(market_blp)
    api.register_blueprint(analytics_blp)
    api.register_blueprint(goals_blp)
    api.register_blueprint(alerts_blp)
    api.register_blueprint(recommendations_blp)
    api.register_blueprint(ai_blp)

    # Both the Nifty50 seed and the scheduler should only fire when the server is
    # actually about to serve requests -- not on every `flask db` CLI invocation
    # (which also builds the app via create_app()) and not twice under the
    # debug reloader's parent+child process pair.
    if not app.config.get("TESTING") and (not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
        with app.app_context():
            import logging

            from sqlalchemy import inspect

            from services.market_service import seed_index_constituents

            logger = logging.getLogger(__name__)

            # A freshly cloned repo has no dev.db -- seed_demo.py is what creates
            # it. Querying here first raised "no such table" and dumped a
            # fatal-looking traceback on the documented first-run path, even
            # though the seed that follows succeeds normally. Check the table
            # exists before touching it, and say something useful if it doesn't.
            if inspect(db.engine).has_table("market_index_constituents"):
                try:
                    seed_index_constituents()
                except Exception:
                    logger.warning("Nifty50 constituent seed failed", exc_info=True)
            else:
                logger.warning(
                    "No database found -- skipping the Nifty50 constituent seed. "
                    "Run `python seed_demo.py` to create and populate it."
                )

        from jobs.price_sync import start_price_sync_job

        start_price_sync_job(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
