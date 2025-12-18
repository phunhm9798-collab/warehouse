from models import db
from datetime import datetime, date

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier = db.Column(db.String(200))
    status = db.Column(db.String(20), default='draft')  # draft, pending, partial, received, cancelled
    expected_date = db.Column(db.Date)
    received_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('PurchaseOrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items)
    
    @property
    def total_received(self):
        return sum(item.received_quantity for item in self.items)
    
    @property
    def total_value(self):
        return sum(item.line_total for item in self.items)
    
    def to_dict(self):
        return {
            'id': self.id,
            'po_number': self.po_number,
            'supplier': self.supplier,
            'status': self.status,
            'expected_date': self.expected_date.isoformat() if self.expected_date else None,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'notes': self.notes,
            'total_items': self.total_items,
            'total_received': self.total_received,
            'total_value': self.total_value,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    received_quantity = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, default=0)
    
    product = db.relationship('Product')
    
    @property
    def line_total(self):
        return self.quantity * self.unit_price
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'quantity': self.quantity,
            'received_quantity': self.received_quantity,
            'unit_price': self.unit_price,
            'line_total': self.line_total
        }


class ShipmentOrder(db.Model):
    __tablename__ = 'shipment_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    so_number = db.Column(db.String(50), unique=True, nullable=False)
    customer = db.Column(db.String(200))
    status = db.Column(db.String(20), default='draft')  # draft, picking, packed, shipped, delivered, cancelled
    ship_date = db.Column(db.Date)
    delivery_date = db.Column(db.Date)
    shipping_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('ShipmentOrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items)
    
    @property
    def total_picked(self):
        return sum(item.picked_quantity for item in self.items)
    
    @property
    def total_value(self):
        return sum(item.line_total for item in self.items)
    
    def to_dict(self):
        return {
            'id': self.id,
            'so_number': self.so_number,
            'customer': self.customer,
            'status': self.status,
            'ship_date': self.ship_date.isoformat() if self.ship_date else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'shipping_address': self.shipping_address,
            'notes': self.notes,
            'total_items': self.total_items,
            'total_picked': self.total_picked,
            'total_value': self.total_value,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ShipmentOrderItem(db.Model):
    __tablename__ = 'shipment_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('shipment_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    picked_quantity = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, default=0)
    
    product = db.relationship('Product')
    
    @property
    def line_total(self):
        return self.quantity * self.unit_price
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'quantity': self.quantity,
            'picked_quantity': self.picked_quantity,
            'unit_price': self.unit_price,
            'line_total': self.line_total
        }
