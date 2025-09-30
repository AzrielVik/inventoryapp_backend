from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

from appwrite.client import Client
from appwrite.services.databases import Databases

# ---------------------- Load Environment ----------------------
# Explicitly load .env from project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

# Fetch env variables
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")
PRODUCTS_COLLECTION_ID = os.getenv("PRODUCTS_COLLECTION_ID")
SALES_COLLECTION_ID = os.getenv("SALES_COLLECTION_ID")

# Sanity check
missing_vars = [
    name for name, value in [
        ("APPWRITE_PROJECT_ID", APPWRITE_PROJECT_ID),
        ("APPWRITE_API_KEY", APPWRITE_API_KEY),
        ("APPWRITE_DATABASE_ID", APPWRITE_DATABASE_ID),
        ("PRODUCTS_COLLECTION_ID", PRODUCTS_COLLECTION_ID),
        ("SALES_COLLECTION_ID", SALES_COLLECTION_ID)
    ] if not value
]

if missing_vars:
    raise Exception(f"❌ Missing environment variables: {', '.join(missing_vars)}")

# ---------------------- Initialize Appwrite ----------------------
client = Client()
client.set_endpoint("https://cloud.appwrite.io/v1")
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)

db = Databases(client)

# ---------------------- Flask App Factory ----------------------
def create_app():
    app = Flask(__name__)
    CORS(app)

    # Register existing routes
    from .routes import main
    app.register_blueprint(main)

    # ---------------------- Register M-Pesa Blueprint ----------------------
    from .mpesa import mpesa_bp
    app.register_blueprint(mpesa_bp, url_prefix="/api")  # /api/prompt-mpesa

    return app
