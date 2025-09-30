from flask import Blueprint, request, jsonify
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.account import Account
from appwrite.id import ID
import os
import traceback

# ✅ Use "main" so __init__.py can import it
main = Blueprint("main", __name__)

# ----------------------
# 🔧 Appwrite Client Setup
# ----------------------
client = Client()
client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
client.set_key(os.getenv("APPWRITE_API_KEY"))

db = Databases(client)
account = Account(client)

DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")
PRODUCTS_COLLECTION_ID = os.getenv("PRODUCTS_COLLECTION_ID")
SALES_COLLECTION_ID = os.getenv("SALES_COLLECTION_ID")

# ----------------------
# 🔐 AUTH ROUTES
# ----------------------
@main.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.json
        print("📩 Signup request data:", data)

        user = account.create(
            user_id=ID.unique(),
            email=data["email"],
            password=data["password"],
            name=data.get("name", "")
        )
        print("✅ Signup success:", user)
        return jsonify(user), 201
    except Exception as e:
        print("❌ Error during signup:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        print("📩 Login request data:", data)

        session = account.create_email_password_session(
            email=data["email"],
            password=data["password"]
        )
        print("✅ Login success:", session)
        return jsonify(session), 200
    except Exception as e:
        print("❌ Error during login:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


# ----------------------
# 📦 PRODUCT ROUTES
# ----------------------
@main.route("/products", methods=["POST"])
def add_product():
    try:
        data = request.json
        print("📦 Add product request:", data)

        product = db.create_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID,
            document_id=ID.unique(),
            data=data
        )
        print("✅ Product added:", product)
        return jsonify(product), 201
    except Exception as e:
        print("❌ Error adding product:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/products", methods=["GET"])
def get_products():
    try:
        print("📦 Fetching all products...")
        products = db.list_documents(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID
        )
        print("✅ Products fetched:", products)
        return jsonify(products), 200
    except Exception as e:
        print("❌ Error fetching products:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    try:
        data = request.json
        print(f"📦 Update product {product_id} with:", data)

        updated = db.update_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID,
            document_id=product_id,
            data=data
        )
        print("✅ Product updated:", updated)
        return jsonify(updated), 200
    except Exception as e:
        print("❌ Error updating product:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    try:
        print(f"🗑️ Delete product {product_id}")
        db.delete_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID,
            document_id=product_id
        )
        print("✅ Product deleted:", product_id)
        return jsonify({"message": "Product deleted successfully"}), 200
    except Exception as e:
        print("❌ Error deleting product:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


# ----------------------
# 💰 SALES ROUTES
# ----------------------
@main.route("/sales", methods=["POST"])
def add_sale():
    try:
        data = request.json
        print("💰 Add sale request:", data)

        sale = db.create_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION_ID,
            document_id=ID.unique(),
            data=data
        )
        print("✅ Sale added:", sale)
        return jsonify(sale), 201
    except Exception as e:
        print("❌ Error adding sale:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/sales", methods=["GET"])
def get_sales():
    try:
        print("💰 Fetching all sales...")
        sales = db.list_documents(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION_ID
        )
        print("✅ Sales fetched:", sales)
        return jsonify(sales), 200
    except Exception as e:
        print("❌ Error fetching sales:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/sales/<sale_id>", methods=["PUT"])
def update_sale(sale_id):
    try:
        data = request.json
        print(f"💰 Update sale {sale_id} with:", data)

        updated = db.update_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION_ID,
            document_id=sale_id,
            data=data
        )
        print("✅ Sale updated:", updated)
        return jsonify(updated), 200
    except Exception as e:
        print("❌ Error updating sale:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/sales/<sale_id>", methods=["DELETE"])
def delete_sale(sale_id):
    try:
        print(f"🗑️ Delete sale {sale_id}")
        db.delete_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION_ID,
            document_id=sale_id
        )
        print("✅ Sale deleted:", sale_id)
        return jsonify({"message": "Sale deleted successfully"}), 200
    except Exception as e:
        print("❌ Error deleting sale:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400
