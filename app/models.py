from . import db
from datetime import datetime
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

# Pricing type enum
class PricingType(enum.Enum):
    kg = "kg"
    unit = "unit"
    piece = "piece"
    bale = "bale"

# Product model
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    pricing_type = db.Column(db.Enum(PricingType), nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)

    sales = db.relationship('Sale', back_populates='product', cascade='all, delete')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "pricing_type": self.pricing_type.value,
            "price_per_unit": self.price_per_unit
        }

# Sale model
class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    weight_per_unit = db.Column(db.Integer, nullable=True)  # nullable=True to support per unit pricing
    num_units = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    date_sold = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', back_populates='sales')

    def to_dict(self):
        return {
            "id": self.id,
            "product": self.product.to_dict(),
            "weight_per_unit": self.weight_per_unit,
            "num_units": self.num_units,
            "customer_name": self.customer_name,
            "total_price": self.total_price,
            "date_sold": self.date_sold.strftime("%Y-%m-%d %H:%M:%S")
        }
