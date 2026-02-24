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
        user = account.create(
            user_id=ID.unique(),
            email=data["email"],
            password=data["password"],
            name=data.get("name", "")
        )
        return jsonify(user), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@main.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        session = account.create_email_password_session(
            email=data["email"],
            password=data["password"]
        )
        return jsonify(session), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ======================== PRODUCT ROUTES ========================

@main.route("/products", methods=["POST"])
def add_product():
    try:
        data = request.json
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        # Extract fields - reverted 'price_per_unit' back to 'rate'
        name = data.get("name")
        unit_type = data.get("unit_type")
        rate = data.get("rate") 
        stock_quantity = data.get("stock_quantity")
        low_stock_threshold = data.get("low_stock_threshold")

        # Explicitly check for None so that '0' remains a valid input
        required_values = [name, unit_type, rate, stock_quantity, low_stock_threshold]
        if any(v is None for v in required_values):
            return jsonify({"error": "Missing required product fields: stock_quantity and low_stock_threshold must be included"}), 400

        # Type conversion & rounding
        try:
            stock_int = int(float(stock_quantity))
            low_stock_int = int(float(low_stock_threshold))
            rate_float = float(rate)
        except (ValueError, TypeError):
            return jsonify({"error": "Rate, Stock, and Threshold must be valid numbers"}), 400

        if stock_int < 0 or low_stock_int < 0:
            return jsonify({"error": "Stock values cannot be negative"}), 400

        product = db.create_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID,
            document_id=ID.unique(),
            data={
                "user_id": user_id,
                "name": name,
                "unit_type": unit_type,
                "rate": rate_float,
                "stock_quantity": stock_int,
                "low_stock_threshold": low_stock_int,
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
        return jsonify({"error": str(e)}), 400


@main.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    try:
        data = request.json
        update_data = {}
        allowed_fields = ["name", "unit_type", "rate", "stock_quantity", "low_stock_threshold"]

        for field in allowed_fields:
            if field in data:
                if field in ["stock_quantity", "low_stock_threshold"]:
                    update_data[field] = int(float(data[field]))
                elif field == "rate":
                    update_data[field] = float(data[field])
                else:
                    update_data[field] = data[field]

        updated = db.update_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION_ID,
            document_id=product_id,
            data=update_data
        )
        return jsonify(updated), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@main.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    try:
        db.delete_document(DATABASE_ID, PRODUCTS_COLLECTION_ID, product_id)
        return jsonify({"message": "Product deleted"}), 200
    except Exception as e:
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

        product = db.get_document(DATABASE_ID, PRODUCTS_COLLECTION_ID, product_id)
        current_stock = float(product.get("stock_quantity", 0))
        
        # Pull quantity from whichever field the frontend sends
        quantity_sold = float(data.get("num_units") or data.get("weight_per_unit") or 0)

        if current_stock < quantity_sold:
            return jsonify({"error": "Insufficient stock", "available": current_stock}), 400

        # Update Stock in Products Collection
        new_stock = int(current_stock - quantity_sold)
        db.update_document(DATABASE_ID, PRODUCTS_COLLECTION_ID, product_id, data={"stock_quantity": new_stock})

        # Record Sale in Sales Collection
        sale = db.create_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION_ID,
            document_id=ID.unique(),
            data={
                "user_id": user_id,
                "product_id": product_id,
                "product_name": product.get("name"),
                "unit_type": product.get("unit_type"),
                "customer_name": data.get("customer_name"),
                "total_price": float(data.get("total_price", 0)),
                "date_sold": datetime.utcnow().isoformat()
            }
        )
        return jsonify(sale), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@main.route("/sales", methods=["GET"])
def get_sales():
    try:
        user_id = request.args.get("user_id")
        sales = db.list_documents(DATABASE_ID, SALES_COLLECTION_ID, queries=[Query.equal("user_id", user_id)])
        return jsonify(sales['documents']), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ======================== RAFIKI (Gemini AI) ROUTE ========================
@main.route("/rafiki", methods=["POST"])
def chat_with_rafiki():
    try:
        data = request.json
        answer = ask_rafiki(data.get("prompt"))
        return jsonify({"response": answer}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500