from models import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # IN, OUT, ADJUST
    quantity = db.Column(db.Integer, nullable=False)
    quantity_before = db.Column(db.Integer, default=0)
    quantity_after = db.Column(db.Integer, default=0)
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.Integer)
    reason = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(100), default='System')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'quantity_before': self.quantity_before,
            'quantity_after': self.quantity_after,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'reason': self.reason,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
