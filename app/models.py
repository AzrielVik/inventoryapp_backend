import os
from datetime import datetime
from . import db  # <- this is your Appwrite Databases service from __init__.py

# Load IDs from .env
DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")
PRODUCTS_COLLECTION = os.getenv("PRODUCTS_COLLECTION_ID")
SALES_COLLECTION = os.getenv("SALES_COLLECTION_ID")


class Product:
    @staticmethod
    def create(name, unit_type, rate, stock_quantity, low_stock_threshold=5):
        """
        Create a new product in the database.
        Now includes stock tracking.
        """
        return db.create_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION,
            document_id="unique()",
            data={
                "name": name,
                "unit_type": unit_type,
                "rate": float(rate),
                "stock_quantity": float(stock_quantity),
                "low_stock_threshold": float(low_stock_threshold),
                "created_at": datetime.utcnow().isoformat()
            }
        )

    @staticmethod
    def list():
        """
        List all products from the database.
        Returns clean dicts including stock info.
        """
        res = db.list_documents(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION
        )

        return [
            {
                "id": doc["$id"],
                "name": doc["name"],
                "unit_type": doc["unit_type"],
                "rate": doc["rate"],
                "stock_quantity": doc.get("stock_quantity", 0),
                "low_stock_threshold": doc.get("low_stock_threshold", 5),
                "is_low_stock": doc.get("stock_quantity", 0) <= doc.get("low_stock_threshold", 5),
                "created_at": doc.get("created_at")
            }
            for doc in res["documents"]
        ]

    @staticmethod
    def get(product_id):
        """
        Fetch a single product by its ID.
        """
        doc = db.get_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION,
            document_id=product_id
        )

        return {
            "id": doc["$id"],
            "name": doc["name"],
            "unit_type": doc["unit_type"],
            "rate": doc["rate"],
            "stock_quantity": doc.get("stock_quantity", 0),
            "low_stock_threshold": doc.get("low_stock_threshold", 5),
            "is_low_stock": doc.get("stock_quantity", 0) <= doc.get("low_stock_threshold", 5),
            "created_at": doc.get("created_at")
        }

    @staticmethod
    def update_stock(product_id, new_stock_quantity):
        """
        Update stock manually (restocking or corrections).
        """
        return db.update_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION,
            document_id=product_id,
            data={
                "stock_quantity": float(new_stock_quantity)
            }
        )

    @staticmethod
    def delete(product_id):
        """
        Delete a product by its ID.
        """
        return db.delete_document(
            database_id=DATABASE_ID,
            collection_id=PRODUCTS_COLLECTION,
            document_id=product_id
        )



class Sale:
    @staticmethod
    def create(product_id, weight_per_unit, num_units, customer_name, total_price):
        return db.create_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION,
            document_id="unique()",
            data={
                "product_id": product_id,
                "weight_per_unit": weight_per_unit,
                "num_units": num_units,
                "customer_name": customer_name,
                "total_price": total_price,
                "date_sold": datetime.utcnow().isoformat()
            }
        )

    @staticmethod
    def list():
        """
        List all sales from the database.
        Return clean list of dicts instead of raw Appwrite response.
        """
        res = db.list_documents(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION
        )
        return [
            {
                "id": doc["$id"],
                "product_id": doc["product_id"],
                "weight_per_unit": doc["weight_per_unit"],
                "num_units": doc["num_units"],
                "customer_name": doc["customer_name"],
                "total_price": doc["total_price"],
                "date_sold": doc.get("date_sold")
            }
            for doc in res["documents"]
        ]

    @staticmethod
    def get(sale_id):
        doc = db.get_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION,
            document_id=sale_id
        )
        return {
            "id": doc["$id"],
            "product_id": doc["product_id"],
            "weight_per_unit": doc["weight_per_unit"],
            "num_units": doc["num_units"],
            "customer_name": doc["customer_name"],
            "total_price": doc["total_price"],
            "date_sold": doc.get("date_sold")
        }

    @staticmethod
    def delete(sale_id):
        return db.delete_document(
            database_id=DATABASE_ID,
            collection_id=SALES_COLLECTION,
            document_id=sale_id
        )
