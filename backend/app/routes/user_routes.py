from flask import Blueprint, jsonify

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
def list_users():
    return jsonify({"message": "Users route placeholder"})
