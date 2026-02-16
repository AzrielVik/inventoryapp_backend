from flask import Blueprint, request, jsonify
import requests
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.account import Account
from appwrite.id import ID
from appwrite.query import Query
import os
import traceback
from datetime import datetime
from app.config import PRODUCTS_COLLECTION


# ======================== SETUP ========================

main = Blueprint("main", __name__)

# Appwrite Client Setup
client = Client()
client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
client.set_key(os.getenv("APPWRITE_API_KEY"))

db = Databases(client)
account = Account(client)

DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")
PRODUCTS_COLLECTION_ID = os.getenv("PRODUCTS_COLLECTION_ID")
SALES_COLLECTION_ID = os.getenv("SALES_COLLECTION_ID")

# Gemini API setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")


# ======================== HELPER ========================

def ask_rafiki(prompt):
    """Sends a user prompt to the Gemini API and returns the AI response."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        print("🚀 Sending POST to Gemini API...")
        response = requests.post(url, headers=headers, json=payload)
        print(f"📡 Status Code: {response.status_code}")
        print("🧾 Raw API Response:", response.text)

        if not response.ok:
            raise Exception(f"{response.status_code} - {response.text}")

        data = response.json()
        answer = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "No response text found.")
        )
        return answer

    except Exception as e:
        print("❌ Error in ask_rafiki:", str(e))
        traceback.print_exc()
        return "I encountered an error trying to respond. Please try again later."


# ======================== AUTH ROUTES ========================

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


# ======================== PRODUCT ROUTES ========================

@main.route("/products", methods=["POST"])
def add_product():
    try:
        data = request.json
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        name = data.get("name")
        unit_type = data.get("unit_type")
        rate = data.get("price_per_unit")
        stock_quantity = data.get("stock_quantity")
        low_stock_threshold = data.get("low_stock_threshold")

        # Basic validation
        if not all([name, unit_type, rate is not None,
                    stock_quantity is not None,
                    low_stock_threshold is not None]):
            return jsonify({"error": "Missing required product fields"}), 400

        stock_quantity = int(stock_quantity)
        low_stock_threshold = int(low_stock_threshold)

        if stock_quantity < 0 or low_stock_threshold < 0:
            return jsonify({"error": "Stock values cannot be negative"}), 400

        product = db.create_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID,
            document_id=ID.unique(),
            data={
                "user_id": user_id,
                "name": name,
                "unit_type": unit_type,
                "rate": float(rate),
                "stock_quantity": stock_quantity,
                "low_stock_threshold": low_stock_threshold,
            }
        )

        return jsonify(product), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/products", methods=["GET"])
def get_products():
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        response = db.list_documents(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID,
            queries=[Query.equal("user_id", user_id)]
        )

        return jsonify(response.get("documents", [])), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    try:
        data = request.json

        update_data = {}

        # Only allow safe fields to be updated
        allowed_fields = [
            "name",
            "unit_type",
            "rate",
            "stock_quantity",
            "low_stock_threshold"
        ]

        for field in allowed_fields:
            if field in data:
                if field in ["stock_quantity", "low_stock_threshold"]:
                    value = int(data[field])
                    if value < 0:
                        return jsonify({"error": f"{field} cannot be negative"}), 400
                    update_data[field] = value
                elif field == "rate":
                    update_data[field] = float(data[field])
                else:
                    update_data[field] = data[field]

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        updated = db.update_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID,
            document_id=product_id,
            data=update_data
        )

        return jsonify(updated), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    try:
        db.delete_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID,
            document_id=product_id
        )

        return jsonify({"message": "Product deleted successfully"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400



# ======================== SALES ROUTES ========================

@main.route("/sales", methods=["POST"])
def add_sale():
    try:
        data = request.json
        user_id = data.get("user_id")
        product_id = data.get("product_id")

        if not user_id or not product_id:
            return jsonify({"error": "Missing user_id or product_id"}), 400

        print("💰 Add sale request received:", data)

        # Fetch product
        product = db.get_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION,
            document_id=product_id
        )

        stock_quantity = float(product.get("stock_quantity", 0))
        unit_type = product.get("unit_type")

        weight_per_unit = data.get("weight_per_unit")
        num_units = data.get("num_units")
        price_per_unit = data.get("price_per_unit")
        total_price = data.get("total_price")

        # ================== Quantity Calculation ==================
        if unit_type == "kg":
            if not weight_per_unit:
                raise ValueError("Missing weight_per_unit for kg-based sale.")

            quantity_sold = float(weight_per_unit)

        else:
            if not num_units:
                raise ValueError("Missing num_units for unit-based sale.")

            quantity_sold = float(num_units)
            weight_per_unit = 0.0

        print(f"📦 Quantity being sold: {quantity_sold}")
        print(f"📦 Current stock: {stock_quantity}")

        # ================== STOCK VALIDATION ==================
        if stock_quantity < quantity_sold:
            return jsonify({
                "error": "Insufficient stock",
                "available_stock": stock_quantity
            }), 400

        # ================== SUBTRACT STOCK ==================
        new_stock = stock_quantity - quantity_sold

        db.update_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION,
            document_id=product_id,
            data={
                "stock_quantity": new_stock
            }
        )

        print(f"📉 Stock updated. New stock: {new_stock}")

        # ================== CREATE SALE ==================
        sale = db.create_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION_ID,
            document_id=ID.unique(),
            data={
                "user_id": user_id,
                "product_id": product_id,
                "product_name": product.get("name"),
                "unit_type": unit_type,
                "customer_name": data.get("customer_name"),
                "price_per_unit": price_per_unit,
                "total_price": total_price,
                "mpesaNumber": data.get("mpesaNumber"),
                "weight_per_unit": weight_per_unit,
                "num_units": num_units,
                "checkoutId": data.get("checkoutId"),
                "date_sold": data.get("date_sold") or datetime.utcnow().isoformat()
            }
        )

        print("✅ Sale added successfully:", sale)
        return jsonify(sale), 201

    except Exception as e:
        print("❌ Error adding sale:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/sales", methods=["GET"])
def get_sales():
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        sales = db.list_documents(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION_ID,
            queries=[Query.equal("user_id", user_id)]
        )

        return jsonify(sales['documents']), 200

    except Exception as e:
        print("❌ Error fetching sales:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


@main.route("/sales/<sale_id>", methods=["DELETE"])
def delete_sale(sale_id):
    try:
        print(f"🗑️ Delete sale {sale_id}")

        # Fetch sale first
        sale = db.get_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION_ID,
            document_id=sale_id
        )

        product_id = sale.get("product_id")
        unit_type = sale.get("unit_type")

        # Fetch product
        product = db.get_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION,
            document_id=product_id
        )

        stock_quantity = float(product.get("stock_quantity", 0))

        # Determine quantity to restore
        if unit_type == "kg":
            quantity_to_restore = float(sale.get("weight_per_unit", 0))
        else:
            quantity_to_restore = float(sale.get("num_units", 0))

        new_stock = stock_quantity + quantity_to_restore

        # Restore stock
        db.update_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION,
            document_id=product_id,
            data={
                "stock_quantity": new_stock
            }
        )

        # Delete sale
        db.delete_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION_ID,
            document_id=sale_id
        )

        print("✅ Sale deleted and stock restored.")
        return jsonify({"message": "Sale deleted and stock restored"}), 200

    except Exception as e:
        print("❌ Error deleting sale:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


# ======================== RAFIKI (Gemini AI) ROUTE ========================
@main.route("/rafiki", methods=["POST"])
def chat_with_rafiki():
    try:
        data = request.json
        if not data or "prompt" not in data:
            print("⚠️ Missing 'prompt' in request JSON.")
            return jsonify({"error": "Missing 'prompt' field."}), 400

        prompt = data["prompt"]
        print(f"🧠 Rafiki received prompt: {prompt}")

        answer = ask_rafiki(prompt)
        print(f"🤖 Rafiki's final response: {answer}")

        return jsonify({"response": answer}), 200

    except Exception as e:
        print("🔥 Unhandled error in /rafiki route:", str(e))
        traceback.print_exc()

        try:
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
            model_res = requests.get(list_url)
            print("📋 Available models:", model_res.text)
        except Exception as inner_e:
            print("⚠️ Couldn't fetch model list:", inner_e)

        return jsonify({"error": str(e)}), 500


# ==================== LIST MODELS (Debug Route) ====================
@main.route("/list_models", methods=["GET"])
def list_models():
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"error": "Missing GEMINI_API_KEY"}), 400

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        print("📡 Fetching models from:", url)

        response = requests.get(url)
        return jsonify(response.json()), response.status_code

    except Exception as e:
        print("❌ Error fetching model list:", str(e))
        return jsonify({"error": str(e)}), 500
