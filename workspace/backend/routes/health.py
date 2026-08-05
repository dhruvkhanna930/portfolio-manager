from flask.views import MethodView
from flask_smorest import Blueprint

blp = Blueprint("health", __name__, url_prefix="/api", description="Health check")


@blp.route("/health")
class Health(MethodView):
    def get(self):
        return {"status": "ok"}
