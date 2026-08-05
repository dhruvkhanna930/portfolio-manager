"""Goals endpoints (CLAUDE.md §14.7)."""

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.advanced_analytics import GoalCreateSchema, GoalSchema
from services import goal_service
from services.goal_service import GoalNotFoundError

blp = Blueprint(
    "goals",
    __name__,
    url_prefix="/api/goals",
    description="Savings goals with progress against total portfolio value",
)


@blp.route("")
class GoalList(MethodView):
    @blp.response(200, GoalSchema(many=True))
    def get(self):
        return goal_service.list_goals()

    @blp.arguments(GoalCreateSchema)
    @blp.response(201, GoalSchema)
    def post(self, data):
        return goal_service.create_goal(
            name=data["name"],
            target_amount=data["target_amount"],
            target_date=data.get("target_date"),
        )


@blp.route("/<int:goal_id>")
class GoalDetail(MethodView):
    @blp.response(200, GoalSchema)
    def get(self, goal_id):
        try:
            return goal_service.get_goal(goal_id)
        except GoalNotFoundError:
            abort(404, message=f"Goal {goal_id} not found")

    @blp.response(204)
    def delete(self, goal_id):
        try:
            goal_service.delete_goal(goal_id)
        except GoalNotFoundError:
            abort(404, message=f"Goal {goal_id} not found")
