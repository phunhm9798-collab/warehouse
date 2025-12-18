from flask import Blueprint, render_template, jsonify
from models import db
from models.product import Product
from models.category import Category
from models.location import Location
from models.transaction import Transaction
from models.order import PurchaseOrder, ShipmentOrder

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    return render_template('dashboard.html')

@dashboard_bp.route('/api/dashboard/stats')
def get_stats():
    total_products = Product.query.count()
    total_quantity = db.session.query(db.func.sum(Product.quantity)).scalar() or 0
    total_value = db.session.query(db.func.sum(Product.quantity * Product.unit_price)).scalar() or 0
    low_stock_count = Product.query.filter(Product.quantity <= Product.min_stock, Product.quantity > 0).count()
    pending_po = PurchaseOrder.query.filter(PurchaseOrder.status.in_(['draft', 'pending'])).count()
    pending_so = ShipmentOrder.query.filter(ShipmentOrder.status.in_(['draft', 'picking', 'packed'])).count()
    total_locations = Location.query.filter_by(is_active=True).count()
    total_categories = Category.query.count()
    
    return jsonify({
        'total_products': total_products,
        'total_quantity': total_quantity,
        'total_value': round(float(total_value), 2),
        'low_stock_count': low_stock_count,
        'pending_purchase_orders': pending_po,
        'pending_shipment_orders': pending_so,
        'total_locations': total_locations,
        'total_categories': total_categories
    })

@dashboard_bp.route('/api/dashboard/recent-activity')
def get_recent_activity():
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    return jsonify([t.to_dict() for t in transactions])

@dashboard_bp.route('/api/dashboard/low-stock')
def get_low_stock():
    products = Product.query.filter(Product.quantity <= Product.min_stock).order_by(Product.quantity).limit(10).all()
    return jsonify([p.to_dict() for p in products])

@dashboard_bp.route('/api/dashboard/category-distribution')
def get_category_distribution():
    categories = Category.query.all()
    result = []
    for cat in categories:
        result.append({
            'name': cat.name,
            'color': cat.color,
            'count': cat.products.count()
        })
    return jsonify(result)
