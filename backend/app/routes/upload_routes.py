from flask import Blueprint, jsonify

upload_bp = Blueprint("uploads", __name__)


@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    return jsonify({"message": "Upload route placeholder"})
