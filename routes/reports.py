from flask import Blueprint, render_template, request, jsonify, Response
from models import db
from models.product import Product
from models.category import Category
from models.location import Location
from models.transaction import Transaction
from models.order import PurchaseOrder, ShipmentOrder
from datetime import datetime
import csv
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
def index():
    return render_template('reports.html')

@reports_bp.route('/api/inventory-summary')
def inventory_summary():
    products = Product.query.all()
    
    summary = {
        'total_products': len(products),
        'total_quantity': sum(p.quantity for p in products),
        'total_value': sum(p.stock_value for p in products),
        'low_stock_count': sum(1 for p in products if p.stock_status == 'low_stock'),
        'out_of_stock_count': sum(1 for p in products if p.stock_status == 'out_of_stock'),
        'overstock_count': sum(1 for p in products if p.stock_status == 'overstock'),
        'products': [p.to_dict() for p in products]
    }
    
    return jsonify(summary)

@reports_bp.route('/api/stock-valuation')
def stock_valuation():
    categories = Category.query.all()
    
    result = []
    for cat in categories:
        products = cat.products.all()
        result.append({
            'name': cat.name,
            'color': cat.color,
            'product_count': len(products),
            'total_quantity': sum(p.quantity for p in products),
            'total_value': round(sum(p.stock_value for p in products), 2)
        })
    
    # Uncategorized
    uncat = Product.query.filter_by(category_id=None).all()
    if uncat:
        result.append({
            'name': 'Uncategorized',
            'color': '#9ca3af',
            'product_count': len(uncat),
            'total_quantity': sum(p.quantity for p in uncat),
            'total_value': round(sum(p.stock_value for p in uncat), 2)
        })
    
    return jsonify(result)

@reports_bp.route('/api/movement-history')
def movement_history():
    limit = request.args.get('limit', 100, type=int)
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(limit).all()
    
    by_date = {}
    for t in transactions:
        date_key = t.created_at.strftime('%Y-%m-%d') if t.created_at else 'unknown'
        if date_key not in by_date:
            by_date[date_key] = {'in': 0, 'out': 0, 'adjust': 0}
        
        if t.transaction_type == 'IN':
            by_date[date_key]['in'] += abs(t.quantity)
        elif t.transaction_type == 'OUT':
            by_date[date_key]['out'] += abs(t.quantity)
        else:
            by_date[date_key]['adjust'] += t.quantity
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions],
        'by_date': by_date
    })

@reports_bp.route('/api/low-stock-report')
def low_stock_report():
    products = Product.query.filter(Product.quantity <= Product.min_stock).order_by(Product.quantity).all()
    
    return jsonify({
        'count': len(products),
        'products': [{
            **p.to_dict(),
            'shortage': p.min_stock - p.quantity,
            'reorder_quantity': p.max_stock - p.quantity
        } for p in products]
    })

@reports_bp.route('/api/location-utilization')
def location_utilization():
    locations = Location.query.filter_by(is_active=True).all()
    
    by_zone = {}
    for loc in locations:
        if loc.zone not in by_zone:
            by_zone[loc.zone] = {
                'total_locations': 0,
                'total_capacity': 0,
                'used_capacity': 0,
                'product_count': 0
            }
        
        by_zone[loc.zone]['total_locations'] += 1
        by_zone[loc.zone]['total_capacity'] += loc.max_capacity
        by_zone[loc.zone]['used_capacity'] += loc.current_capacity
        by_zone[loc.zone]['product_count'] += len(loc.products)
    
    return jsonify({
        'total_locations': len(locations),
        'by_zone': by_zone
    })

@reports_bp.route('/api/order-summary')
def order_summary():
    po_stats = {}
    for po in PurchaseOrder.query.all():
        po_stats[po.status] = po_stats.get(po.status, 0) + 1
    
    so_stats = {}
    for so in ShipmentOrder.query.all():
        so_stats[so.status] = so_stats.get(so.status, 0) + 1
    
    return jsonify({
        'purchase_orders': po_stats,
        'shipment_orders': so_stats
    })

@reports_bp.route('/api/export/inventory')
def export_inventory():
    products = Product.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['SKU', 'Name', 'Category', 'Quantity', 'Unit', 'Unit Price', 'Stock Value', 'Status'])
    
    for p in products:
        writer.writerow([
            p.sku, p.name, p.category.name if p.category else '',
            p.quantity, p.unit, p.unit_price, p.stock_value, p.stock_status
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=inventory_{datetime.now().strftime("%Y%m%d")}.csv'}
    )

@reports_bp.route('/api/export/transactions')
def export_transactions():
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(500).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Product SKU', 'Product Name', 'Type', 'Quantity', 'Before', 'After', 'Reason'])
    
    for t in transactions:
        writer.writerow([
            t.created_at, t.product.sku if t.product else '', t.product.name if t.product else '',
            t.transaction_type, t.quantity, t.quantity_before, t.quantity_after, t.reason or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=transactions_{datetime.now().strftime("%Y%m%d")}.csv'}
    )
