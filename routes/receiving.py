from flask import Blueprint, render_template, request, jsonify
from models import db
from models.product import Product
from models.transaction import Transaction
from models.order import PurchaseOrder, PurchaseOrderItem
from datetime import datetime, date

receiving_bp = Blueprint('receiving', __name__, url_prefix='/receiving')

@receiving_bp.route('/')
def index():
    return render_template('receiving.html')

@receiving_bp.route('/api/orders')
def get_orders():
    status = request.args.get('status', '')
    query = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    orders = query.all()
    return jsonify([o.to_dict() for o in orders])

@receiving_bp.route('/api/orders/<int:order_id>')
def get_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    return jsonify(order.to_dict())

@receiving_bp.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    
    today = date.today()
    count = PurchaseOrder.query.filter(db.func.date(PurchaseOrder.created_at) == today).count()
    po_number = f"PO-{today.strftime('%Y%m%d')}-{count + 1:03d}"
    
    order = PurchaseOrder(
        po_number=po_number,
        supplier=data.get('supplier', ''),
        status='draft',
        expected_date=datetime.strptime(data['expected_date'], '%Y-%m-%d').date() if data.get('expected_date') else None,
        notes=data.get('notes', '')
    )
    db.session.add(order)
    db.session.flush()
    
    for item_data in data.get('items', []):
        product = Product.query.get(item_data['product_id'])
        item = PurchaseOrderItem(
            order_id=order.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_price=item_data.get('unit_price', product.cost_price if product else 0)
        )
        db.session.add(item)
    
    db.session.commit()
    return jsonify(order.to_dict()), 201

@receiving_bp.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    data = request.get_json()
    order.supplier = data.get('supplier', order.supplier)
    if data.get('expected_date'):
        order.expected_date = datetime.strptime(data['expected_date'], '%Y-%m-%d').date()
    order.notes = data.get('notes', order.notes)
    if 'status' in data:
        order.status = data['status']
    db.session.commit()
    return jsonify(order.to_dict())

@receiving_bp.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = PurchaseOrder.query.get(order_id)
    if order and order.status in ['draft', 'cancelled']:
        db.session.delete(order)
        db.session.commit()
        return jsonify({'message': 'Deleted'})
    return jsonify({'error': 'Cannot delete'}), 400

@receiving_bp.route('/api/orders/<int:order_id>/receive', methods=['POST'])
def receive_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    data = request.get_json()
    
    for recv in data.get('items', []):
        item = PurchaseOrderItem.query.get(recv['item_id'])
        if not item or item.order_id != order.id:
            continue
        
        recv_qty = recv.get('quantity', 0)
        if recv_qty <= 0:
            continue
        
        item.received_quantity += recv_qty
        
        product = Product.query.get(item.product_id)
        if product:
            old_qty = product.quantity
            product.quantity += recv_qty
            
            trans = Transaction(
                product_id=product.id,
                transaction_type='IN',
                quantity=recv_qty,
                quantity_before=old_qty,
                quantity_after=product.quantity,
                reference_type='purchase_order',
                reference_id=order.id,
                reason='Goods received',
                notes=f'PO {order.po_number}'
            )
            db.session.add(trans)
    
    if order.total_received >= order.total_items:
        order.status = 'received'
        order.received_date = date.today()
    elif order.total_received > 0:
        order.status = 'partial'
    else:
        order.status = 'pending'
    
    db.session.commit()
    return jsonify(order.to_dict())

@receiving_bp.route('/api/orders/<int:order_id>/submit', methods=['POST'])
def submit_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    if order.status != 'draft' or order.items.count() == 0:
        return jsonify({'error': 'Invalid or empty order'}), 400
    order.status = 'pending'
    db.session.commit()
    return jsonify(order.to_dict())

@receiving_bp.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    if order.status == 'received':
        return jsonify({'error': 'Cannot cancel received order'}), 400
    order.status = 'cancelled'
    db.session.commit()
    return jsonify(order.to_dict())
