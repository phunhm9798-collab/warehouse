"""
Seed Historical Transaction Data
Generates realistic historical transaction data for the past 90 days
to demonstrate the demand forecasting functionality.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db
from models.product import Product
from models.transaction import Transaction
from datetime import datetime, timedelta
import random

def seed_historical_transactions():
    """Generate 90 days of historical transaction data for all products."""
    
    products = Product.query.all()
    if not products:
        print("No products found. Please seed product data first.")
        return
    
    print(f"Generating historical transactions for {len(products)} products...")
    
    # Define demand patterns for different product categories
    # Higher demand = more transactions
    demand_profiles = {
        'Electronics': {'base_demand': 3, 'variance': 2, 'weekend_factor': 1.5},
        'Office Supplies': {'base_demand': 5, 'variance': 3, 'weekend_factor': 0.3},
        'Packaging': {'base_demand': 8, 'variance': 4, 'weekend_factor': 0.5},
        'Tools': {'base_demand': 2, 'variance': 1, 'weekend_factor': 0.8},
        'Safety': {'base_demand': 2, 'variance': 1, 'weekend_factor': 0.2},
    }
    default_profile = {'base_demand': 3, 'variance': 2, 'weekend_factor': 0.5}
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)
    
    transaction_count = 0
    
    for product in products:
        category_name = product.category.name if product.category else 'Unknown'
        profile = demand_profiles.get(category_name, default_profile)
        
        # Add some product-specific variation
        product_factor = random.uniform(0.5, 1.5)
        
        current_date = start_date
        while current_date <= end_date:
            # Determine daily demand based on profile
            base = profile['base_demand'] * product_factor
            variance = profile['variance']
            
            # Weekend adjustment
            is_weekend = current_date.weekday() >= 5
            if is_weekend:
                base *= profile['weekend_factor']
            
            # Add some randomness - some days have 0 demand
            if random.random() < 0.3:  # 30% chance of no demand
                daily_demand = 0
            else:
                daily_demand = max(0, int(random.gauss(base, variance)))
            
            # Add seasonal variation (slight increase in recent weeks)
            days_ago = (end_date - current_date).days
            recency_factor = 1 + (90 - days_ago) / 300  # Up to 30% increase for recent days
            daily_demand = int(daily_demand * recency_factor)
            
            if daily_demand > 0:
                # Create an OUT transaction (sales/demand)
                # Spread transactions throughout the day
                hour = random.randint(8, 18)
                minute = random.randint(0, 59)
                transaction_time = current_date.replace(hour=hour, minute=minute)
                
                trans = Transaction(
                    product_id=product.id,
                    transaction_type='OUT',
                    quantity=-daily_demand,
                    quantity_before=product.quantity + daily_demand,  # Simulated
                    quantity_after=product.quantity,
                    reference_type='historical_seed',
                    reason='Historical demand (seeded)',
                    notes=f'Auto-generated for forecasting demo',
                    created_by='System',
                    created_at=transaction_time
                )
                db.session.add(trans)
                transaction_count += 1
            
            current_date += timedelta(days=1)
        
        # Also add some IN transactions (restocking) - about every 2 weeks
        restock_date = start_date + timedelta(days=random.randint(1, 14))
        while restock_date <= end_date:
            restock_qty = random.randint(20, 100)
            transaction_time = restock_date.replace(hour=9, minute=0)
            
            trans = Transaction(
                product_id=product.id,
                transaction_type='IN',
                quantity=restock_qty,
                quantity_before=product.quantity - restock_qty,
                quantity_after=product.quantity,
                reference_type='historical_seed',
                reason='Restocking (seeded)',
                notes='Auto-generated for forecasting demo',
                created_by='System',
                created_at=transaction_time
            )
            db.session.add(trans)
            transaction_count += 1
            
            restock_date += timedelta(days=random.randint(10, 20))
    
    db.session.commit()
    print(f"Created {transaction_count} historical transactions!")
    print("You can now refresh the forecast dashboard to see meaningful predictions.")


if __name__ == '__main__':
    with app.app_context():
        # Check if historical data already exists
        existing = Transaction.query.filter_by(reference_type='historical_seed').count()
        if existing > 0:
            print(f"Found {existing} existing seeded transactions.")
            response = input("Delete existing and regenerate? (y/n): ")
            if response.lower() == 'y':
                Transaction.query.filter_by(reference_type='historical_seed').delete()
                db.session.commit()
                print("Deleted existing seeded transactions.")
                seed_historical_transactions()
            else:
                print("Keeping existing data.")
        else:
            seed_historical_transactions()
