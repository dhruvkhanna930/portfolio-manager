from flask import jsonify
from werkzeug.exceptions import HTTPException

ERROR_CODE_MAP = {
    400: "BAD_REQUEST",
    404: "NOT_FOUND",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
}


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        data = getattr(err, "data", None) or {}
        message = data.get("message")

        if not message and "messages" in data:
            parts = []
            for location_errors in data["messages"].values():
                for field, msgs in location_errors.items():
                    for msg in msgs:
                        parts.append(f"{field}: {msg}")
            message = "; ".join(parts) if parts else None

        if not message:
            message = err.description or str(err)

        code = ERROR_CODE_MAP.get(err.code, "ERROR")
        return jsonify({"error": {"code": code, "message": message}}), err.code
