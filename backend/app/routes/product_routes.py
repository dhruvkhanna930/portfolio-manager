from flask import Blueprint, jsonify

product_bp = Blueprint("products", __name__)


@product_bp.route("/products", methods=["GET"])
def list_products():
    return jsonify({"message": "Products route placeholder"})
