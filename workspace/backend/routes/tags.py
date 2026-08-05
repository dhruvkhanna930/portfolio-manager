from flask.views import MethodView
from flask_smorest import Blueprint

from schemas.tag import TagCreateSchema, TagSchema
from services import tag_service as svc

blp = Blueprint("tags", __name__, url_prefix="/api/tags", description="Holding tags")


@blp.route("")
class TagList(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self):
        return svc.list_tags()

    @blp.arguments(TagCreateSchema)
    @blp.response(201, TagSchema)
    def post(self, data):
        return svc.create_tag(data["name"])
