from . import db
from datetime import datetime

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_type = db.Column(db.String(100), nullable=False)
    weight_per_unit = db.Column(db.Integer, nullable=False)
    num_units=db.Column(db.Integer, nullable=False)
    rate_per_kg = db.Column(db.Float, nullable=False)
    customer_name =db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    date_sold = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "product_type": self.product_type,
            "weight_per_unit": self.weight_per_unit,
            "num_units": self.num_units,
            "rate_per_kg": self.rate_per_kg,
            "customer_name": self.customer_name,
            "total_price": self.total_price,
            "date_sold": self.date_sold.strftime("%Y-%m-%d %H:%M:%S")
        }

    