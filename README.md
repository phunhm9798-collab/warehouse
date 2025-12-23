# WMS Pro

A modern warehouse management system built with Python, Flask, and PostgreSQL, featuring **AI-powered demand forecasting** for inventory optimization.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

| Module | Description |
|--------|-------------|
| **Dashboard** | Real-time KPIs, quick actions, low stock alerts |
| **Inventory** | Full CRUD, search/filter, category management |
| **Locations** | Zone management, bulk location creation |
| **Receiving** | Purchase orders, goods receipt processing |
| **Shipping** | Pick, pack, and ship workflow |
| **Reports** | Inventory summaries, stock levels, CSV export |
| **Forecast** | Demand prediction, restock recommendations, PDF/CSV reports |

---

## Demand Forecasting Module

The forecasting module uses historical transaction data to predict future demand and optimize inventory levels.

### Forecasting Algorithms

| Algorithm | Best For |
|-----------|----------|
| **Exponential Smoothing** | General-purpose forecasting (default) |
| **Simple Moving Average** | Stable demand patterns |
| **Weighted Moving Average** | Trending products |
| **Linear Regression** | Growing or declining demand |
| **Holt-Winters** | Seasonal patterns |

### Key Features

- **Configurable Parameters**: Adjust history period (30-180 days) and forecast horizon (7-90 days)
- **Stockout Risk Assessment**: Color-coded status (Critical/Warning/Monitor/OK)
- **Safety Stock Calculation**: Based on demand variability at 95% service level
- **Restock Recommendations**: Minimum and optimal quantities to order
- **Export Reports**: Professional PDF reports and CSV data export

### Usage

1. Navigate to `/forecast` or click "Forecast" in the sidebar
2. Configure history period, forecast horizon, and algorithm
3. Review critical items and restock recommendations
4. Export as CSV or PDF for purchasing decisions

### Seed Historical Data

To generate sample transaction data for forecasting demos:

```bash
python seed_transactions.py
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11 + Flask 3.0 |
| Database | PostgreSQL (production) / SQLite (local) |
| ORM | Flask-SQLAlchemy |
| Forecasting | NumPy, Pandas, Statsmodels |
| PDF Reports | ReportLab |
| Server | Gunicorn |
| Hosting | Render (free tier) or Docker |

---

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/warehouse.git
cd warehouse

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Then open http://localhost:5000

### Seed Sample Data

```bash
# Windows (PowerShell)
$env:SEED_DATA='true'; python app.py

# Windows (CMD)
set SEED_DATA=true && python app.py

# Linux/Mac
SEED_DATA=true python app.py
```

### Seed Historical Transactions (for Forecasting)

```bash
python seed_transactions.py
```

---

## Deploy to Render (Free)

### Option 1: Blueprint Deploy (Recommended)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) and sign up
3. Click **New → Blueprint**
4. Connect your GitHub repository
5. Render auto-detects `render.yaml` and provisions:
   - **PostgreSQL database** (free tier)
   - **Web service** (free tier)

### Option 2: Manual Deploy

1. Create a **PostgreSQL** database on Render
2. Create a **Web Service** and connect your repo
3. Set environment variables:
   - `DATABASE_URL`: *(from PostgreSQL dashboard)*
   - `SECRET_KEY`: *(any secure string)*
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`

---

## Docker

```bash
# Build the image
docker build -t wms-pro .

# Run the container
docker run -p 8080:8080 -e DATABASE_URL=your_db_url wms-pro
```

---

## Project Structure

```
warehouse/
├── app.py                  # Application entry point
├── config.py               # Configuration settings
├── seed_transactions.py    # Historical data generator for forecasting
├── models/                 # SQLAlchemy data models
│   ├── category.py
│   ├── location.py
│   ├── order.py
│   ├── product.py
│   └── transaction.py
├── services/               # Business logic services
│   └── forecast_service.py # Forecasting algorithms
├── routes/                 # Flask blueprints
│   ├── dashboard.py
│   ├── inventory.py
│   ├── locations.py
│   ├── receiving.py
│   ├── shipping.py
│   ├── reports.py
│   └── forecast.py         # Forecast API & exports
├── templates/              # Jinja2 HTML templates
│   └── forecast.html       # Forecast dashboard
├── static/                 # CSS and assets
├── Dockerfile              # Docker configuration
├── render.yaml             # Render blueprint
└── requirements.txt        # Python dependencies
```

---

## API Endpoints

### Forecast API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/forecast/` | GET | Forecast dashboard UI |
| `/forecast/api/products` | GET | All products forecast |
| `/forecast/api/products/<id>` | GET | Single product detail |
| `/forecast/api/categories` | GET | Category-level forecast |
| `/forecast/api/report` | GET | Full report data (JSON) |
| `/forecast/api/export/csv` | GET | Download CSV export |
| `/forecast/api/export/pdf` | GET | Download PDF report |

**Query Parameters:**
- `history_days` (default: 90) - Historical data period
- `forecast_days` (default: 30) - Forecast horizon
- `algorithm` (default: exponential) - sma, wma, exponential, linear, holt

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | SQLite (local) |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `SEED_DATA` | Set to `true` to seed sample data | `false` |
| `PORT` | Server port | `5000` |

---

## Dependencies

Key Python packages:
- **Flask** - Web framework
- **Flask-SQLAlchemy** - Database ORM
- **Pandas** - Data manipulation
- **NumPy** - Numerical computing
- **Statsmodels** - Statistical forecasting
- **ReportLab** - PDF generation
- **Matplotlib** - Charts (optional)

---

## License

MIT License
