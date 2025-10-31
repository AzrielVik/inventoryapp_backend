# app/rafiki.py

import os
import requests
import traceback
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases

# ==================== LOAD ENVIRONMENT VARIABLES ====================
load_dotenv()

# ---------------------- Gemini API Setup ----------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-pro:generateContent?key={GEMINI_API_KEY}"
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

        # Build a small summary of top few items (optional)
        sample_products = ", ".join(
            [p["name"] for p in product_docs[:3] if "name" in p]
        )
        sample_sales = ", ".join(
            [s["customer_name"] for s in sales_docs[:3] if "customer_name" in s]
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
    """Send a user prompt (plus live context) to the Gemini model and return the response with Rafiki personality."""
    try:
        context = get_app_context()
        full_prompt = f"{context}\n\nUser asked: {prompt}"

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": full_prompt}]}
            ]
        }

        response = requests.post(GEMINI_API_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        # Parse Gemini response text safely
        answer = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "Rafiki has no response right now.")
        )

        # Add Rafiki personality / flavor here
        final_answer = f"📊 Rafiki here! Based on your inventory data: {answer}"

        print("🧠 Rafiki Response:", final_answer)
        return final_answer

    except Exception as e:
        print("❌ Error in ask_rafiki:", str(e))
        traceback.print_exc()
        return "I encountered an error trying to respond. Please try again later."
