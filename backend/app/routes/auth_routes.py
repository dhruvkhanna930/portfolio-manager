from flask import Blueprint, jsonify

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    return jsonify({"message": "Login route placeholder"})
