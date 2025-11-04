import os
import requests
import traceback
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from appwrite.client import Client
from appwrite.services.databases import Databases

# ==================== LOAD ENVIRONMENT VARIABLES ====================
load_dotenv()

# ---------------------- Gemini API Setup ----------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ Use a supported model (2.5 Flash is the newest and fast)
MODEL_NAME = "models/gemini-2.5-pro"

# ✅ Correct endpoint for Gemini v1beta
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
)

# ---------------------- Appwrite Setup ----------------------
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")
PRODUCTS_COLLECTION_ID = os.getenv("PRODUCTS_COLLECTION_ID")
SALES_COLLECTION_ID = os.getenv("SALES_COLLECTION_ID")

# Initialize Appwrite client
client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
db = Databases(client)

# ==================== BLUEPRINT ====================
rafiki_bp = Blueprint("rafiki", __name__)

# ==================== HELPER: Fetch Context from DB ====================
def get_app_context():
    """Fetch summarized product and sales info for Rafiki context."""
    try:
        products = db.list_documents(APPWRITE_DATABASE_ID, PRODUCTS_COLLECTION_ID)
        sales = db.list_documents(APPWRITE_DATABASE_ID, SALES_COLLECTION_ID)

        product_docs = products.get("documents", [])
        sales_docs = sales.get("documents", [])

        product_count = len(product_docs)
        sales_count = len(sales_docs)

        # Create short samples for flavor
        sample_products = ", ".join(
            [p.get("name", "Unnamed") for p in product_docs[:3]]
        )
        sample_sales = ", ".join(
            [s.get("customer_name", "Unknown") for s in sales_docs[:3]]
        )

        context_summary = f"""
You are Rafiki, the AI assistant for an inventory management system called 'Inventory'.
- Products in database: {product_count}
- Sales recorded: {sales_count}
- Example products: {sample_products if sample_products else "N/A"}
- Example customers: {sample_sales if sample_sales else "N/A"}
You help users understand sales trends, manage inventory, and provide smart insights.
"""

        return context_summary.strip()

    except Exception as e:
        print("⚠️ Error fetching Appwrite context:", str(e))
        traceback.print_exc()
        return "Unable to fetch live inventory context right now."

# ==================== MAIN FUNCTION: Ask Rafiki ====================
def ask_rafiki(prompt):
    """Send a user prompt (plus live context) to the Gemini model and return the response."""
    try:
        context = get_app_context()
        full_prompt = f"{context}\n\nUser asked: {prompt}"

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": full_prompt}]}
            ]
        }

        headers = {"Content-Type": "application/json"}

        print("📦 Payload:", payload)
        print("📡 Sending request to:", GEMINI_API_URL)

        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        print("📡 Status Code:", response.status_code)
        print("🧾 Raw API Response:", response.text)

        response.raise_for_status()
        data = response.json()

        # Safely parse the Gemini output
        answer = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "Rafiki has no response right now.")
        )

        final_answer = f"📊 Rafiki here! Based on your inventory data: {answer}"

        print("🧠 Rafiki Response:", final_answer)
        return final_answer

    except requests.exceptions.RequestException as api_err:
        print("❌ API Request Error in ask_rafiki:", str(api_err))
        traceback.print_exc()
        return "Rafiki ran into a connection issue while talking to Gemini."

    except Exception as e:
        print("❌ General Error in ask_rafiki:", str(e))
        traceback.print_exc()
        return "I encountered an error trying to respond. Please try again later."

# ==================== DEBUG ROUTE: List Models ====================
@rafiki_bp.route("/list_models", methods=["GET"])
def list_models():
    """
    Temporary route to check available Gemini models for this API key.
    Visit this URL in your browser to see model names.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"error": "Missing GEMINI_API_KEY in environment variables"}), 400

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        print("📡 Fetching models from:", url)

        response = requests.get(url)
        print("🧾 Raw response:", response.text)

        return jsonify(response.json()), response.status_code

    except Exception as e:
        print("❌ Error fetching model list:", str(e))
        return jsonify({"error": str(e)}), 500