from .auth_routes import auth_bp
from .user_routes import user_bp
from .product_routes import product_bp
from .upload_routes import upload_bp

__all__ = ["auth_bp", "user_bp", "product_bp", "upload_bp"]
