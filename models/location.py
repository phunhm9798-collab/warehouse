from models import db
from datetime import datetime

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    zone = db.Column(db.String(10), nullable=False)
    aisle = db.Column(db.String(10), nullable=False)
    rack = db.Column(db.String(10), nullable=False)
    shelf = db.Column(db.String(10), nullable=False)
    bin = db.Column(db.String(10), default='01')
    max_capacity = db.Column(db.Integer, default=100)
    current_capacity = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    zone_type = db.Column(db.String(20), default='storage')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def full_code(self):
        return f"{self.zone}-{self.aisle}-{self.rack}-{self.shelf}-{self.bin}"
    
    @property
    def short_code(self):
        return f"{self.zone}{self.aisle}{self.rack}{self.shelf}"
    
    @property
    def utilization(self):
        if self.max_capacity == 0:
            return 0
        return round((self.current_capacity / self.max_capacity) * 100, 1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'zone': self.zone,
            'aisle': self.aisle,
            'rack': self.rack,
            'shelf': self.shelf,
            'bin': self.bin,
            'full_code': self.full_code,
            'short_code': self.short_code,
            'max_capacity': self.max_capacity,
            'current_capacity': self.current_capacity,
            'utilization': self.utilization,
            'is_active': self.is_active,
            'zone_type': self.zone_type,
            'product_count': len(self.products) if self.products else 0
        }
