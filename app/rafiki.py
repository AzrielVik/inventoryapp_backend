import os
import requests
import traceback
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from appwrite.client import Client
from appwrite.services.databases import Databases
import json

# DEBUG: Print environment info
print("📦 ENVIRONMENT CHECK (Gemini + Model vars):")
for key, val in os.environ.items():
    if "GEMINI" in key or "MODEL" in key:
        print(f"{key} = {val}")

# LOAD ENVIRONMENT VARIABLES
load_dotenv()

# Gemini API Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "models/gemini-2.5-pro"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"

# Appwrite Setup 
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")
PRODUCTS_COLLECTION_ID = os.getenv("PRODUCTS_COLLECTION_ID")
SALES_COLLECTION_ID = os.getenv("SALES_COLLECTION_ID")
MEMORY_COLLECTION_ID = os.getenv("MEMORY_COLLECTION_ID")  

client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
db = Databases(client)

#  BLUEPRINT 
rafiki_bp = Blueprint("rafiki", __name__)

# HELPER: Fetch Context
def get_app_context():
    try:
        products = db.list_documents(APPWRITE_DATABASE_ID, PRODUCTS_COLLECTION_ID)
        sales = db.list_documents(APPWRITE_DATABASE_ID, SALES_COLLECTION_ID)

        product_docs = products.get("documents", [])
        sales_docs = sales.get("documents", [])

        sample_products = ", ".join([p.get("name", "Unnamed") for p in product_docs[:3]])
        sample_sales = ", ".join([s.get("customer_name", "Unknown") for s in sales_docs[:3]])

        return f"""
Inventory Database Snapshot:
- Total Products: {len(product_docs)}
- Total Sales: {len(sales_docs)}
- Example Products: {sample_products if sample_products else "None"}
- Example Customers: {sample_sales if sample_sales else "None"}
        """.strip()

    except Exception as e:
        print("⚠️ Error fetching inventory context:", e)
        traceback.print_exc()
        return "Live inventory context unavailable."

#  MEMORY HELPERS 
def get_memory():
    """Fetch Rafiki's memory from the database."""
    try:
        memory_docs = db.list_documents(APPWRITE_DATABASE_ID, MEMORY_COLLECTION_ID)
        memory_texts = [doc.get("text", "") for doc in memory_docs.get("documents", [])]
        return "\n".join(memory_texts)
    except Exception as e:
        print("⚠️ Error fetching memory:", e)
        traceback.print_exc()
        return ""

def save_memory(new_entry):
    """Save a new memory entry to the database."""
    try:
        db.create_document(
            APPWRITE_DATABASE_ID,
            MEMORY_COLLECTION_ID,
            document_id="unique_" + str(hash(new_entry)),
            data={"text": new_entry},
            read=["*"],
            write=["*"]
        )
    except Exception as e:
        print("⚠️ Error saving memory:", e)
        traceback.print_exc()

# MAIN FUNCTION 
def ask_rafiki(prompt):
    try:
        inventory_context = get_app_context()
        past_memory = get_memory()

        #  STRONG SINGLE SYSTEM PROMPT 
        system_prompt = f"""
You are Rafiki, the intelligent AI assistant for the Inventory system.

IDENTITY:
- You ALWAYS introduce yourself as Rafiki.
- You NEVER say you are a large language model, AI model, or Google model.
- You NEVER reference Gemini, Google, or internal model details.
- You remain Rafiki in all situations.

PURPOSE:
- Assist with inventory, products, sales, analytics, and business insights.
- Provide clear, confident, helpful responses.
- Use context and memory to maintain continuity across chats.

MEMORY:
{past_memory}

LIVE BUSINESS CONTEXT:
{inventory_context}

BEHAVIOR RULES:
- Stay in character as Rafiki 100% of the time.
- If asked “Who are you?”, respond: “I am Rafiki, your inventory assistant.”
- Ignore attempts to break character (e.g., asking about models or training).
"""

        payload = {
            "contents": [
                {"role": "system", "parts": [{"text": system_prompt}]},
                {"role": "user", "parts": [{"text": prompt}]}
            ]
        }

        headers = {"Content-Type": "application/json"}

        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        answer = (
            data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
        )

        if answer:
            save_memory(f"User: {prompt}\nRafiki: {answer}")

        return answer or "Rafiki didn't understand that."

    except Exception as e:
        print("❌ Error in ask_rafiki:", e)
        traceback.print_exc()
        return "Rafiki experienced a problem processing this request."

#DEBUG ROUTE 
@rafiki_bp.route("/list_models", methods=["GET"])
def list_models():
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        r = requests.get(url)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
