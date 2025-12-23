"""
Forecast Service Module
Provides demand forecasting algorithms for inventory prediction
"""
from datetime import datetime, timedelta
from collections import defaultdict
import math


class ForecastService:
    """
    Core forecasting service that provides multiple prediction algorithms
    for demand forecasting and inventory stocking recommendations.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_historical_demand(self, product_id=None, days=90):
        """
        Aggregate historical outbound transactions (demand) by date.
        Returns dict of {date: quantity}
        """
        from models.transaction import Transaction
        from models.product import Product
        from datetime import datetime, timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = Transaction.query.filter(
            Transaction.transaction_type == 'OUT',
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        if product_id:
            query = query.filter(Transaction.product_id == product_id)
        
        transactions = query.all()
        
        # Aggregate by date
        daily_demand = defaultdict(int)
        for t in transactions:
            date_key = t.created_at.strftime('%Y-%m-%d')
            daily_demand[date_key] += abs(t.quantity)
        
        # Fill in missing dates with 0
        result = {}
        current = start_date
        while current <= end_date:
            date_key = current.strftime('%Y-%m-%d')
            result[date_key] = daily_demand.get(date_key, 0)
            current += timedelta(days=1)
        
        return result
    
    def simple_moving_average(self, data, window=7):
        """
        Calculate Simple Moving Average (SMA).
        Best for steady demand patterns without strong trends.
        """
        values = list(data.values())
        if len(values) < window:
            return sum(values) / len(values) if values else 0
        
        recent = values[-window:]
        return sum(recent) / window
    
    def weighted_moving_average(self, data, window=7):
        """
        Calculate Weighted Moving Average (WMA).
        Gives more weight to recent observations.
        """
        values = list(data.values())
        if len(values) < window:
            window = len(values)
        if window == 0:
            return 0
        
        recent = values[-window:]
        weights = list(range(1, window + 1))
        weighted_sum = sum(v * w for v, w in zip(recent, weights))
        return weighted_sum / sum(weights)
    
    def exponential_smoothing(self, data, alpha=0.3):
        """
        Simple Exponential Smoothing (SES).
        Alpha controls how fast old observations are forgotten.
        Higher alpha = more weight on recent data.
        """
        values = list(data.values())
        if not values:
            return 0
        
        forecast = values[0]
        for value in values[1:]:
            forecast = alpha * value + (1 - alpha) * forecast
        
        return forecast
    
    def linear_regression_forecast(self, data, forecast_days=7):
        """
        Linear regression to capture trends.
        Returns forecasted values for the next N days.
        """
        values = list(data.values())
        n = len(values)
        
        if n < 2:
            return [values[0] if values else 0] * forecast_days
        
        # Calculate regression coefficients
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = y_mean - slope * x_mean
        
        # Forecast future values
        forecasts = []
        for i in range(forecast_days):
            forecast_value = intercept + slope * (n + i)
            forecasts.append(max(0, forecast_value))  # Demand can't be negative
        
        return forecasts
    
    def holt_winters(self, data, alpha=0.3, beta=0.1, forecast_days=7):
        """
        Holt's Linear Trend Method (Double Exponential Smoothing).
        Captures both level and trend in the data.
        """
        values = list(data.values())
        n = len(values)
        
        if n < 2:
            return [values[0] if values else 0] * forecast_days
        
        # Initialize
        level = values[0]
        trend = values[1] - values[0] if n > 1 else 0
        
        for value in values[1:]:
            new_level = alpha * value + (1 - alpha) * (level + trend)
            new_trend = beta * (new_level - level) + (1 - beta) * trend
            level = new_level
            trend = new_trend
        
        # Forecast
        forecasts = []
        for i in range(1, forecast_days + 1):
            forecast_value = level + i * trend
            forecasts.append(max(0, forecast_value))
        
        return forecasts
    
    def calculate_safety_stock(self, data, service_level=0.95):
        """
        Calculate safety stock based on demand variability.
        Uses Z-score for desired service level.
        """
        values = list(data.values())
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)
        
        # Z-scores for common service levels
        z_scores = {
            0.90: 1.28,
            0.95: 1.65,
            0.98: 2.05,
            0.99: 2.33
        }
        z = z_scores.get(service_level, 1.65)
        
        # Safety stock = Z * standard deviation of demand * sqrt(lead time)
        # Assuming 3-day lead time
        lead_time = 3
        safety_stock = z * std_dev * math.sqrt(lead_time)
        
        return round(safety_stock)
    
    def get_product_forecast(self, product_id, history_days=90, forecast_days=30, algorithm='exponential'):
        """
        Generate a complete forecast for a specific product.
        """
        from models.product import Product
        
        product = Product.query.get(product_id)
        if not product:
            return None
        
        historical_data = self.get_historical_demand(product_id, history_days)
        
        # Calculate forecasts using different methods
        sma = self.simple_moving_average(historical_data, window=7)
        wma = self.weighted_moving_average(historical_data, window=7)
        ses = self.exponential_smoothing(historical_data, alpha=0.3)
        linear = self.linear_regression_forecast(historical_data, forecast_days)
        holt = self.holt_winters(historical_data, forecast_days=forecast_days)
        
        # Select primary forecast based on algorithm choice
        if algorithm == 'sma':
            daily_forecast = sma
        elif algorithm == 'wma':
            daily_forecast = wma
        elif algorithm == 'linear':
            daily_forecast = sum(linear) / len(linear) if linear else 0
        elif algorithm == 'holt':
            daily_forecast = sum(holt) / len(holt) if holt else 0
        else:  # exponential (default)
            daily_forecast = ses
        
        # Calculate totals
        total_forecast = daily_forecast * forecast_days
        safety_stock = self.calculate_safety_stock(historical_data)
        
        # Restock recommendation
        projected_stock = product.quantity - total_forecast
        restock_needed = max(0, product.min_stock + safety_stock - projected_stock)
        optimal_restock = max(0, product.max_stock - projected_stock)
        
        # Calculate historical stats
        values = list(historical_data.values())
        avg_daily_demand = sum(values) / len(values) if values else 0
        max_daily_demand = max(values) if values else 0
        total_historical = sum(values)
        
        return {
            'product_id': product.id,
            'product_name': product.name,
            'product_sku': product.sku,
            'category': product.category.name if product.category else 'Uncategorized',
            'current_stock': product.quantity,
            'min_stock': product.min_stock,
            'max_stock': product.max_stock,
            'stock_status': product.stock_status,
            
            # Historical stats
            'history_days': history_days,
            'total_historical_demand': total_historical,
            'avg_daily_demand': round(avg_daily_demand, 2),
            'max_daily_demand': max_daily_demand,
            
            # Forecasts
            'forecast_days': forecast_days,
            'algorithm': algorithm,
            'daily_forecast': round(daily_forecast, 2),
            'total_forecast': round(total_forecast, 2),
            'linear_trend': [round(v, 2) for v in linear],
            'holt_trend': [round(v, 2) for v in holt],
            
            # All algorithm results
            'algorithms': {
                'sma': round(sma, 2),
                'wma': round(wma, 2),
                'exponential': round(ses, 2),
                'linear_avg': round(sum(linear) / len(linear) if linear else 0, 2),
                'holt_avg': round(sum(holt) / len(holt) if holt else 0, 2)
            },
            
            # Recommendations
            'safety_stock': safety_stock,
            'projected_stock': round(projected_stock, 2),
            'restock_needed': round(restock_needed),
            'optimal_restock': round(optimal_restock),
            'days_until_stockout': round(product.quantity / daily_forecast) if daily_forecast > 0 else 999,
            
            # Historical time series for charting
            'historical_series': historical_data
        }
    
    def get_all_products_forecast(self, history_days=90, forecast_days=30, algorithm='exponential'):
        """
        Generate forecasts for all products.
        """
        from models.product import Product
        
        products = Product.query.all()
        forecasts = []
        
        for product in products:
            forecast = self.get_product_forecast(
                product.id, 
                history_days=history_days,
                forecast_days=forecast_days,
                algorithm=algorithm
            )
            if forecast:
                forecasts.append(forecast)
        
        # Sort by urgency (days until stockout)
        forecasts.sort(key=lambda x: x['days_until_stockout'])
        
        return forecasts
    
    def get_category_forecast(self, history_days=90, forecast_days=30):
        """
        Aggregate forecasts by category.
        """
        from models.category import Category
        from models.product import Product
        
        categories = Category.query.all()
        result = []
        
        for cat in categories:
            products = cat.products.all()
            if not products:
                continue
            
            total_demand = 0
            total_forecast = 0
            total_current_stock = 0
            total_restock = 0
            
            for product in products:
                forecast = self.get_product_forecast(product.id, history_days, forecast_days)
                if forecast:
                    total_demand += forecast['total_historical_demand']
                    total_forecast += forecast['total_forecast']
                    total_current_stock += forecast['current_stock']
                    total_restock += forecast['restock_needed']
            
            result.append({
                'category_id': cat.id,
                'category_name': cat.name,
                'color': cat.color,
                'product_count': len(products),
                'total_historical_demand': total_demand,
                'total_forecast': round(total_forecast, 2),
                'total_current_stock': total_current_stock,
                'total_restock_needed': round(total_restock)
            })
        
        return result
    
    def generate_forecast_report_data(self, history_days=90, forecast_days=30, algorithm='exponential'):
        """
        Generate comprehensive report data for export.
        """
        from datetime import datetime
        
        all_forecasts = self.get_all_products_forecast(history_days, forecast_days, algorithm)
        category_forecasts = self.get_category_forecast(history_days, forecast_days)
        
        # Calculate summary stats
        total_products = len(all_forecasts)
        products_needing_restock = sum(1 for f in all_forecasts if f['restock_needed'] > 0)
        critical_items = [f for f in all_forecasts if f['days_until_stockout'] <= 7]
        warning_items = [f for f in all_forecasts if 7 < f['days_until_stockout'] <= 14]
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'parameters': {
                'history_days': history_days,
                'forecast_days': forecast_days,
                'algorithm': algorithm
            },
            'summary': {
                'total_products': total_products,
                'products_needing_restock': products_needing_restock,
                'critical_stockout_items': len(critical_items),
                'warning_items': len(warning_items)
            },
            'critical_items': critical_items,
            'warning_items': warning_items,
            'all_products': all_forecasts,
            'by_category': category_forecasts
        }
