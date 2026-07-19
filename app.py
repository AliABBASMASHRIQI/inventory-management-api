from datetime import timedelta
from flasgger import Swagger
from flask import Flask
from flask_jwt_extended import JWTManager
from db import cursor,connection
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)

from routes.products import products_bp
from routes.users import user_bp
from routes.orders import orders_bp
app.register_blueprint(products_bp)
app.register_blueprint(user_bp)
app.register_blueprint(orders_bp)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)
jwt = JWTManager(app)
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Inventory Management API",
        "description": "Inventory Management REST API built with Flask",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter JWT token as: Bearer <your_token>"
        }
    }
}

Swagger(app, template=swagger_template)

if __name__ == '__main__':
    app.run(debug=True)
    print(app.url_map)