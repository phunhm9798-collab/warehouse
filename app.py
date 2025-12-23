from flask import Flask
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Register blueprints
    from routes.dashboard import dashboard_bp
    from routes.inventory import inventory_bp
    from routes.locations import locations_bp
    from routes.receiving import receiving_bp
    from routes.shipping import shipping_bp
    from routes.reports import reports_bp
    from routes.forecast import forecast_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(receiving_bp)
    app.register_blueprint(shipping_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(forecast_bp)
    
    with app.app_context():
        db.create_all()
    
    return app

def seed_sample_data():
    """Seed sample data"""
    from models.category import Category
    from models.product import Product
    from models.location import Location
    
    if Category.query.count() > 0:
        print("Data already exists")
        return
    
    print("Seeding sample data...")
    
    # Categories
    categories = [
        Category(name='Electronics', description='Electronic devices', color='#3b82f6'),
        Category(name='Office Supplies', description='Office items', color='#10b981'),
        Category(name='Packaging', description='Packaging materials', color='#f59e0b'),
        Category(name='Tools', description='Hand tools', color='#ef4444'),
        Category(name='Safety', description='Safety equipment', color='#8b5cf6'),
    ]
    for cat in categories:
        db.session.add(cat)
    db.session.commit()
    
    # Get category IDs
    cats = {c.name: c.id for c in Category.query.all()}
    
    # Locations
    for zone, zone_type in [('A', 'storage'), ('B', 'storage'), ('R', 'receiving'), ('S', 'shipping')]:
        for aisle in range(1, 3):
            for rack in range(1, 3):
                for shelf in ['A', 'B', 'C']:
                    loc = Location(zone=zone, aisle=f'{aisle:02d}', rack=f'{rack:02d}', 
                                   shelf=shelf, bin='01', zone_type=zone_type)
                    db.session.add(loc)
    db.session.commit()
    
    # Products
    products = [
        ('SKU-000001', 'Wireless Mouse', 'Electronics', 150, 29.99),
        ('SKU-000002', 'USB-C Hub', 'Electronics', 75, 49.99),
        ('SKU-000003', 'Mechanical Keyboard', 'Electronics', 45, 89.99),
        ('SKU-000004', 'Monitor Stand', 'Electronics', 8, 39.99),
        ('SKU-000005', 'Webcam HD', 'Electronics', 0, 59.99),
        ('SKU-000006', 'A4 Paper Box', 'Office Supplies', 500, 24.99),
        ('SKU-000007', 'Ballpoint Pens', 'Office Supplies', 200, 9.99),
        ('SKU-000008', 'Sticky Notes', 'Office Supplies', 15, 5.99),
        ('SKU-000009', 'Cardboard Box S', 'Packaging', 1000, 1.50),
        ('SKU-000010', 'Cardboard Box M', 'Packaging', 750, 2.50),
        ('SKU-000011', 'Packing Tape', 'Packaging', 5, 4.99),
        ('SKU-000012', 'Screwdriver Set', 'Tools', 30, 34.99),
        ('SKU-000013', 'Tape Measure', 'Tools', 50, 12.99),
        ('SKU-000014', 'Safety Glasses', 'Safety', 100, 14.99),
        ('SKU-000015', 'Work Gloves', 'Safety', 75, 11.99),
    ]
    
    for sku, name, cat_name, qty, price in products:
        p = Product(sku=sku, name=name, category_id=cats.get(cat_name), 
                    quantity=qty, min_stock=10, max_stock=500, 
                    unit_price=price, cost_price=price * 0.5)
        db.session.add(p)
    db.session.commit()
    
    print("Sample data seeded!")

app = create_app()

if __name__ == '__main__':
    import os
    if os.environ.get('SEED_DATA', 'false').lower() == 'true':
        with app.app_context():
            seed_sample_data()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
