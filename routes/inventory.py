from flask import Blueprint, render_template, request, jsonify
from models import db
from models.product import Product
from models.category import Category
from models.transaction import Transaction
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
def index():
    return render_template('inventory.html')

# ============ PRODUCT CRUD ============

@inventory_bp.route('/api/products')
def get_products():
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status', '')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    query = Product.query
    
    if search:
        query = query.filter(db.or_(
            Product.name.ilike(f'%{search}%'),
            Product.sku.ilike(f'%{search}%')
        ))
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if status == 'low_stock':
        query = query.filter(Product.quantity <= Product.min_stock, Product.quantity > 0)
    elif status == 'out_of_stock':
        query = query.filter(Product.quantity <= 0)
    elif status == 'overstock':
        query = query.filter(Product.quantity >= Product.max_stock)
    
    # Sorting
    sort_col = getattr(Product, sort_by, Product.name)
    if sort_order == 'desc':
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())
    
    products = query.all()
    return jsonify([p.to_dict() for p in products])

@inventory_bp.route('/api/products/<int:product_id>')
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@inventory_bp.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    
    sku = data.get('sku') or f'SKU-{Product.query.count() + 1:06d}'
    if Product.query.filter_by(sku=sku).first():
        return jsonify({'error': 'SKU already exists'}), 400
    
    product = Product(
        sku=sku,
        name=data['name'],
        description=data.get('description', ''),
        category_id=data.get('category_id'),
        quantity=data.get('quantity', 0),
        min_stock=data.get('min_stock', 10),
        max_stock=data.get('max_stock', 1000),
        unit_price=data.get('unit_price', 0),
        cost_price=data.get('cost_price', 0),
        location_id=data.get('location_id'),
        unit=data.get('unit', 'pcs'),
        weight=data.get('weight', 0)
    )
    db.session.add(product)
    db.session.commit()
    
    if product.quantity > 0:
        trans = Transaction(
            product_id=product.id,
            transaction_type='IN',
            quantity=product.quantity,
            quantity_before=0,
            quantity_after=product.quantity,
            reason='Initial stock'
        )
        db.session.add(trans)
        db.session.commit()
    
    return jsonify(product.to_dict()), 201

@inventory_bp.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    old_qty = product.quantity
    
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.category_id = data.get('category_id', product.category_id)
    product.min_stock = data.get('min_stock', product.min_stock)
    product.max_stock = data.get('max_stock', product.max_stock)
    product.unit_price = data.get('unit_price', product.unit_price)
    product.cost_price = data.get('cost_price', product.cost_price)
    product.location_id = data.get('location_id', product.location_id)
    product.unit = data.get('unit', product.unit)
    product.weight = data.get('weight', product.weight)
    
    new_qty = data.get('quantity')
    if new_qty is not None and new_qty != old_qty:
        product.quantity = new_qty
        trans = Transaction(
            product_id=product.id,
            transaction_type='ADJUST',
            quantity=new_qty - old_qty,
            quantity_before=old_qty,
            quantity_after=new_qty,
            reason=data.get('adjustment_reason', 'Manual adjustment')
        )
        db.session.add(trans)
    
    db.session.commit()
    return jsonify(product.to_dict())

@inventory_bp.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return jsonify({'message': 'Deleted'})

@inventory_bp.route('/api/products/<int:product_id>/adjust', methods=['POST'])
def adjust_stock(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    adj_type = data.get('type', 'add')
    quantity = data.get('quantity', 0)
    old_qty = product.quantity
    
    if adj_type == 'add':
        product.quantity += quantity
        trans_type = 'IN'
    else:
        product.quantity = max(0, product.quantity - quantity)
        quantity = -quantity
        trans_type = 'OUT'
    
    trans = Transaction(
        product_id=product.id,
        transaction_type=trans_type,
        quantity=quantity,
        quantity_before=old_qty,
        quantity_after=product.quantity,
        reference_type='adjustment',
        reason=data.get('reason', 'Manual adjustment'),
        notes=data.get('notes', '')
    )
    db.session.add(trans)
    db.session.commit()
    
    return jsonify(product.to_dict())

# ============ CATEGORIES ============

@inventory_bp.route('/api/categories')
def get_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify([c.to_dict() for c in categories])

@inventory_bp.route('/api/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    if Category.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Category exists'}), 400
    
    cat = Category(
        name=data['name'],
        description=data.get('description', ''),
        color=data.get('color', '#6366f1')
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201

@inventory_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    cat = Category.query.get_or_404(category_id)
    data = request.get_json()
    cat.name = data.get('name', cat.name)
    cat.description = data.get('description', cat.description)
    cat.color = data.get('color', cat.color)
    db.session.commit()
    return jsonify(cat.to_dict())

@inventory_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    cat = Category.query.get(category_id)
    if cat:
        db.session.delete(cat)
        db.session.commit()
    return jsonify({'message': 'Deleted'})

# ============ TRANSACTIONS ============

@inventory_bp.route('/api/transactions')
def get_transactions():
    product_id = request.args.get('product_id', type=int)
    trans_type = request.args.get('type', '')
    limit = request.args.get('limit', 50, type=int)
    
    query = Transaction.query.order_by(Transaction.created_at.desc())
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    if trans_type:
        query = query.filter_by(transaction_type=trans_type)
    
    transactions = query.limit(limit).all()
    return jsonify([t.to_dict() for t in transactions])
