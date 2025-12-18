# WMS Pro - Warehouse Management System

A modern warehouse management system built with Python/Flask.

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## Deploy to Render (Free)

### Option 1: One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Click the button above
2. Connect your GitHub repository
3. Render will automatically set up PostgreSQL and deploy

### Option 2: Manual Deploy

1. Go to https://render.com
2. Create a new **PostgreSQL** database (free tier)
3. Create a new **Web Service**
4. Connect your repository
5. Set environment variables:
   - `DATABASE_URL`: (from PostgreSQL dashboard)
   - `SECRET_KEY`: (any secure string)
6. Build Command: `pip install -r requirements.txt`
7. Start Command: `gunicorn app:app`

## Seed Sample Data

After deployment, run locally with:
```bash
set DATABASE_URL=your_postgres_url
set SEED_DATA=true
python app.py
```

## Features

- Dashboard with KPIs
- Inventory Management
- Warehouse Locations
- Receiving (Purchase Orders)
- Shipping (Sales Orders)
- Reports & Analytics
