from flask import Blueprint, request, jsonify
from .models import Sale, Product
from . import db
from datetime import datetime

main = Blueprint('main', __name__)

ALLOWED_UNIT_TYPES = ['kg', 'unit', 'piece', 'bale']

# ---------------------- SALES ROUTES ----------------------

@main.route('/sales', methods=['POST'])
def add_sale():
    data = request.json
    try:
        print("🔵 Incoming sale data:", data)

        product_name = data['product_type']
        weight = float(data['weight_per_unit'])
        units = int(data['num_units'])

        product = Product.query.filter_by(name=product_name).first()
        if not product:
            return jsonify({'error': f'Product \"{product_name}\" not found. Please register it first.'}), 400

        rate = product.price_per_unit
        total_price = weight * units * rate if product.pricing_type.value == 'kg' else units * rate

        sale = Sale(
            product_id=product.id,
            weight_per_unit=weight,
            num_units=units,
            customer_name=data.get('customer_name'),
            total_price=total_price
        )
        db.session.add(sale)
        db.session.commit()

        return jsonify(sale.to_dict()), 201

    except Exception as e:
        print("❌ Error while adding sale:", str(e))
        return jsonify({'error': str(e)}), 400

@main.route('/sales', methods=['GET'])
def get_sales():
    date_str = request.args.get('date')
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
        print("🟡 Updating sale with data:", data)

        sale.weight_per_unit = float(data.get('weight_per_unit', sale.weight_per_unit))
        sale.num_units = int(data.get('num_units', sale.num_units))
        sale.customer_name = data.get('customer_name', sale.customer_name)
        sale.total_price = sale.weight_per_unit * sale.num_units * sale.product.price_per_unit

        db.session.commit()
        return jsonify(sale.to_dict()), 200

    except Exception as e:
        print("❌ Error while updating sale:", str(e))
        return jsonify({'error': str(e)}), 400

@main.route('/sales/<int:id>', methods=['DELETE'])
def delete_sale(id):
    sale = Sale.query.get(id)
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404

    db.session.delete(sale)
    db.session.commit()
    return jsonify({'message': 'Sale deleted successfully'}), 200

# ---------------------- STOCK ROUTE ----------------------

@main.route('/stock', methods=['GET'])
def get_stock():
    try:
        sales = Sale.query.all()
        stock_data = {}

        for sale in sales:
            prod = sale.product.name
            stock_data.setdefault(prod, 100)
            stock_data[prod] -= sale.num_units

        return jsonify(stock_data), 200
    except Exception as e:
        print("❌ Error while fetching stock:", str(e))
        return jsonify({'error': str(e)}), 500

# ---------------------- PRODUCT ROUTES ----------------------

@main.route('/products', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        print("🔵 Incoming product data:", data)

        name = data.get('name')
        pricing_type = data.get('unit_type')
        price_per_unit = data.get('rate')

        if not all([name, pricing_type, price_per_unit is not None]):
            return jsonify({'error': 'Missing required fields: name, unit_type or rate'}), 400

        if pricing_type not in ALLOWED_UNIT_TYPES:
            return jsonify({'error': f'Invalid unit_type: {pricing_type}. Must be one of {ALLOWED_UNIT_TYPES}'}), 400

        try:
            price_per_unit = float(price_per_unit)
        except (ValueError, TypeError):
            return jsonify({'error': 'Rate must be a valid number'}), 400

        existing = Product.query.filter_by(name=name).first()
        if existing:
            return jsonify({'error': 'Product already exists'}), 409

        new_product = Product(
            name=name,
            pricing_type=pricing_type,
            price_per_unit=price_per_unit
        )
        db.session.add(new_product)
        db.session.commit()

        return jsonify(new_product.to_dict()), 201

    except Exception as e:
        print("❌ Error while adding product:", str(e))
        return jsonify({'error': str(e)}), 400

@main.route('/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([p.to_dict() for p in products]), 200
    except Exception as e:
        print("❌ Error while fetching products:", str(e))
        return jsonify({'error': str(e)}), 500

@main.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()
    try:
        print("🟡 Updating product with data:", data)

        name = data.get('name', product.name)
        unit_type = data.get('unit_type', product.pricing_type)
        rate = data.get('rate', product.price_per_unit)

        if unit_type not in ALLOWED_UNIT_TYPES:
            return jsonify({'error': f'Invalid unit_type: {unit_type}'}), 400

        product.name = name
        product.pricing_type = unit_type
        product.price_per_unit = float(rate)

        db.session.commit()
        return jsonify(product.to_dict()), 200

    except Exception as e:
        print("❌ Error while updating product:", str(e))
        return jsonify({'error': str(e)}), 400

@main.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    try:
        # Delete all related sales first if needed to avoid constraint errors
        sales = Sale.query.filter_by(product_id=product.id).all()
        for sale in sales:
            db.session.delete(sale)

        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200

    except Exception as e:
        print("❌ Error while deleting product:", str(e))
        return jsonify({'error': str(e)}), 500
