from flask import Flask

from config import DevelopmentConfig
from app.routes import auth_routes, user_routes, product_routes, upload_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    app.register_blueprint(auth_routes.auth_bp)
    app.register_blueprint(user_routes.user_bp)
    app.register_blueprint(product_routes.product_bp)
    app.register_blueprint(upload_routes.upload_bp)

    return app
