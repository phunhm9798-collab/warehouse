from models import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    quantity = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=10)
    max_stock = db.Column(db.Integer, default=1000)
    unit_price = db.Column(db.Float, default=0.0)
    cost_price = db.Column(db.Float, default=0.0)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    unit = db.Column(db.String(20), default='pcs')
    weight = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    location = db.relationship('Location', backref='products')
    transactions = db.relationship('Transaction', backref='product', lazy='dynamic')
    
    @property
    def stock_status(self):
        if self.quantity <= 0:
            return 'out_of_stock'
        elif self.quantity <= self.min_stock:
            return 'low_stock'
        elif self.quantity >= self.max_stock:
            return 'overstock'
        return 'normal'
    
    @property
    def stock_value(self):
        return self.quantity * self.unit_price
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'quantity': self.quantity,
            'min_stock': self.min_stock,
            'max_stock': self.max_stock,
            'unit_price': self.unit_price,
            'cost_price': self.cost_price,
            'location_id': self.location_id,
            'location_name': self.location.full_code if self.location else None,
            'unit': self.unit,
            'weight': self.weight,
            'stock_status': self.stock_status,
            'stock_value': self.stock_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
