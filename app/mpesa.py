from flask import Blueprint, request, jsonify
import requests
import base64
from datetime import datetime
import os

from . import db, SALES_COLLECTION_ID  # Appwrite db + collection

# -----------------------------
# M-Pesa Blueprint
# -----------------------------
mpesa_bp = Blueprint('mpesa', __name__)

# -----------------------------
# Sandbox credentials
# -----------------------------
MPESA_SHORTCODE = "174379"  # Sandbox test paybill
MPESA_CONSUMER_KEY = "eIxJFtzOvbkWyFWNaMIXsUZfMXXErMAKn2BeXevwjUEGvTAu"
MPESA_CONSUMER_SECRET = "35VMRxTzfncv8A9c6v7AttuBABW7XK8RVrE7Gy83YOClqVzdTttUcty9olY4YggX"
MPESA_PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
MPESA_API_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
CALLBACK_URL = "https://your-public-url.com/api/mpesa/callback"  # Must be accessible!

# -----------------------------
# Helper functions
# -----------------------------
def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Failed to get access token: {response.text}")

def generate_password(shortcode, passkey, timestamp):
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode("utf-8")

# -----------------------------
# Routes
# -----------------------------
@mpesa_bp.route("/prompt-mpesa", methods=["POST"])
def prompt_mpesa():
    """
    Trigger an M-Pesa STK Push to a customer.
    Expected JSON: { "amount": 1000, "mpesaNumber": "2547XXXXXXXX", "reference": "OptionalReference" }
    """
    data = request.json
    amount = data.get("amount")
    phone = data.get("mpesaNumber")
    reference = data.get("reference", "SalePayment")

    if not amount or not phone:
        return jsonify({"error": "amount and mpesaNumber are required"}), 400

    try:
        # Step 1: Get OAuth token
        token = get_access_token()

        # Step 2: Generate timestamp & password
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = generate_password(MPESA_SHORTCODE, MPESA_PASSKEY, timestamp)

        # Step 3: Prepare STK Push payload
        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": CALLBACK_URL,
            "AccountReference": reference,
            "TransactionDesc": "Sale Payment"
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(MPESA_API_URL, json=payload, headers=headers)
        res_json = response.json()
        print("🔵 M-Pesa API Response:", res_json)

        # Step 4: Store the CheckoutRequestID in Appwrite
        checkout_id = res_json.get("CheckoutRequestID")
        if checkout_id:
            db.create_document(
                collection_id=SALES_COLLECTION_ID,
                data={
                    "amount": amount,
                    "mpesaNumber": phone,
                    "reference": reference,
                    "paymentStatus": "pending",
                    "checkoutId": checkout_id,
                    "timestamp": timestamp
                },
                read=["*"],
                write=["*"]
            )

        return jsonify(res_json)

    except Exception as e:
        print("🔴 Error in /prompt-mpesa:", str(e))
        return jsonify({"error": str(e)}), 500


@mpesa_bp.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    """
    Safaricom will POST here after customer completes payment.
    Updates the corresponding sale in Appwrite using CheckoutRequestID.
    """
    data = request.json
    print("🔵 Callback received:", data)

    try:
        result = data.get("Body", {}).get("stkCallback", {})
        checkout_id = result.get("CheckoutRequestID")
        status_code = result.get("ResultCode")

        payment_status = "paid" if status_code == 0 else "failed"

        # Find the sale in Appwrite with matching checkoutId
        sales = db.list_documents(
            collection_id=SALES_COLLECTION_ID,
            filters=[f'checkoutId="{checkout_id}"']
        )

        if sales['total'] > 0:
            sale_id = sales['documents'][0]['$id']
            db.update_document(
                collection_id=SALES_COLLECTION_ID,
                document_id=sale_id,
                data={"paymentStatus": payment_status}
            )

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("🔴 Error in /mpesa/callback:", str(e))
        return jsonify({"error": str(e)}), 500
