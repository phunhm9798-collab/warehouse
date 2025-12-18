from flask import Blueprint, render_template, request, jsonify
from models import db
from models.product import Product
from models.transaction import Transaction
from models.order import ShipmentOrder, ShipmentOrderItem
from datetime import datetime, date

shipping_bp = Blueprint('shipping', __name__, url_prefix='/shipping')

@shipping_bp.route('/')
def index():
    return render_template('shipping.html')

@shipping_bp.route('/api/orders')
def get_orders():
    status = request.args.get('status', '')
    query = ShipmentOrder.query.order_by(ShipmentOrder.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    orders = query.all()
    return jsonify([o.to_dict() for o in orders])

@shipping_bp.route('/api/orders/<int:order_id>')
def get_order(order_id):
    order = ShipmentOrder.query.get_or_404(order_id)
    return jsonify(order.to_dict())

@shipping_bp.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    
    today = date.today()
    count = ShipmentOrder.query.filter(db.func.date(ShipmentOrder.created_at) == today).count()
    so_number = f"SO-{today.strftime('%Y%m%d')}-{count + 1:03d}"
    
    order = ShipmentOrder(
        so_number=so_number,
        customer=data.get('customer', ''),
        status='draft',
        ship_date=datetime.strptime(data['ship_date'], '%Y-%m-%d').date() if data.get('ship_date') else None,
        shipping_address=data.get('shipping_address', ''),
        notes=data.get('notes', '')
    )
    db.session.add(order)
    db.session.flush()
    
    for item_data in data.get('items', []):
        product = Product.query.get(item_data['product_id'])
        item = ShipmentOrderItem(
            order_id=order.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_price=item_data.get('unit_price', product.unit_price if product else 0)
        )
        db.session.add(item)
    
    db.session.commit()
    return jsonify(order.to_dict()), 201

@shipping_bp.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    order = ShipmentOrder.query.get_or_404(order_id)
    data = request.get_json()
    order.customer = data.get('customer', order.customer)
    if data.get('ship_date'):
        order.ship_date = datetime.strptime(data['ship_date'], '%Y-%m-%d').date()
    order.shipping_address = data.get('shipping_address', order.shipping_address)
    order.notes = data.get('notes', order.notes)
    if 'status' in data:
        order.status = data['status']
    db.session.commit()
    return jsonify(order.to_dict())

@shipping_bp.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = ShipmentOrder.query.get(order_id)
    if order and order.status in ['draft', 'cancelled']:
        db.session.delete(order)
        db.session.commit()
        return jsonify({'message': 'Deleted'})
    return jsonify({'error': 'Cannot delete'}), 400

@shipping_bp.route('/api/orders/<int:order_id>/pick', methods=['POST'])
def pick_order(order_id):
    order = ShipmentOrder.query.get_or_404(order_id)
    if order.status not in ['draft', 'picking']:
        return jsonify({'error': 'Invalid status'}), 400
    
    for item in order.items:
        product = Product.query.get(item.product_id)
        if product and product.quantity < item.quantity:
            return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
    
    order.status = 'picking'
    db.session.commit()
    return jsonify(order.to_dict())

@shipping_bp.route('/api/orders/<int:order_id>/confirm-pick', methods=['POST'])
def confirm_pick(order_id):
    order = ShipmentOrder.query.get_or_404(order_id)
    data = request.get_json()
    
    for pick in data.get('items', []):
        item = ShipmentOrderItem.query.get(pick['item_id'])
        if not item or item.order_id != order.id:
            continue
        
        pick_qty = pick.get('quantity', 0)
        if pick_qty <= 0:
            continue
        
        item.picked_quantity += pick_qty
        
        product = Product.query.get(item.product_id)
        if product:
            old_qty = product.quantity
            product.quantity = max(0, product.quantity - pick_qty)
            
            trans = Transaction(
                product_id=product.id,
                transaction_type='OUT',
                quantity=-pick_qty,
                quantity_before=old_qty,
                quantity_after=product.quantity,
                reference_type='shipment_order',
                reference_id=order.id,
                reason='Picked for shipment',
                notes=f'SO {order.so_number}'
            )
            db.session.add(trans)
    
    if order.total_picked >= order.total_items:
        order.status = 'packed'
    
    db.session.commit()
    return jsonify(order.to_dict())

@shipping_bp.route('/api/orders/<int:order_id>/ship', methods=['POST'])
def ship_order(order_id):
    order = ShipmentOrder.query.get_or_404(order_id)
    if order.status != 'packed':
        return jsonify({'error': 'Must be packed'}), 400
    order.status = 'shipped'
    order.ship_date = date.today()
    db.session.commit()
    return jsonify(order.to_dict())

@shipping_bp.route('/api/orders/<int:order_id>/deliver', methods=['POST'])
def deliver_order(order_id):
    order = ShipmentOrder.query.get_or_404(order_id)
    if order.status != 'shipped':
        return jsonify({'error': 'Must be shipped'}), 400
    order.status = 'delivered'
    order.delivery_date = date.today()
    db.session.commit()
    return jsonify(order.to_dict())

@shipping_bp.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    order = ShipmentOrder.query.get_or_404(order_id)
    if order.status in ['shipped', 'delivered']:
        return jsonify({'error': 'Cannot cancel'}), 400
    
    # Restore stock
    for item in order.items:
        if item.picked_quantity > 0:
            product = Product.query.get(item.product_id)
            if product:
                old_qty = product.quantity
                product.quantity += item.picked_quantity
                
                trans = Transaction(
                    product_id=product.id,
                    transaction_type='IN',
                    quantity=item.picked_quantity,
                    quantity_before=old_qty,
                    quantity_after=product.quantity,
                    reference_type='shipment_order',
                    reference_id=order.id,
                    reason='Order cancelled - stock restored'
                )
                db.session.add(trans)
            item.picked_quantity = 0
    
    order.status = 'cancelled'
    db.session.commit()
    return jsonify(order.to_dict())
