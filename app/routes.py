from flask import Blueprint, request, jsonify
from .models import Sale
from . import db
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/sales', methods=['POST'])
def add_sale():
    data = request.json
    try:
        weight = float(data['weight_per_unit'])
        units = int(data['num_units'])
        rate = float(data['rate_per_kg'])
        total_price = weight * units * rate

        sale = Sale(
            product_type=data['product_type'],
            weight_per_unit=weight,
            num_units=units,
            rate_per_kg=rate,
            customer_name=data.get('customer_name'),
            total_price=total_price
        )
        db.session.add(sale)
        db.session.commit()

        return jsonify(sale.to_dict()), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@main.route('/sales', methods=['GET'])
def get_sales():
    date_str = request.args.get('date')  # Optional filter by date
    try:
        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            sales = Sale.query.all()
            sales = [s for s in sales if s.date_sold.date() == date_obj]
        else:
            sales = Sale.query.all()

        return jsonify([s.to_dict() for s in sales]), 200

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

@main.route('/sales/<int:id>', methods=['GET'])
def get_sale(id):
    sale = Sale.query.get(id)
    if sale:
        return jsonify(sale.to_dict()), 200
    else:
        return jsonify({'error': 'Sale not found'}), 404

@main.route('/sales/<int:id>', methods=['PUT'])
def update_sale(id):
    sale = Sale.query.get(id)
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404

    data = request.json
    try:
        sale.product_type = data.get('product_type', sale.product_type)
        sale.weight_per_unit = float(data.get('weight_per_unit', sale.weight_per_unit))
        sale.num_units = int(data.get('num_units', sale.num_units))
        sale.rate_per_kg = float(data.get('rate_per_kg', sale.rate_per_kg))
        sale.customer_name = data.get('customer_name', sale.customer_name)
        sale.total_price = sale.weight_per_unit * sale.num_units * sale.rate_per_kg

        db.session.commit()
        return jsonify(sale.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@main.route('/sales/<int:id>', methods=['DELETE'])
def delete_sale(id):
    sale = Sale.query.get(id)
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404

    db.session.delete(sale)
    db.session.commit()
    return jsonify({'message': 'Sale deleted successfully'}), 200

# ✅ STOCK ENDPOINT (basic placeholder logic)
@main.route('/stock', methods=['GET'])
def get_stock():
    try:
        # Placeholder: Assume 100 units per product before any sale
        sales = Sale.query.all()
        stock_data = {}

        for sale in sales:
            prod = sale.product_type
            stock_data.setdefault(prod, 100)  # default starting point
            stock_data[prod] -= sale.num_units

        return jsonify(stock_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
