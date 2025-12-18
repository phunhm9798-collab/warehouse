# WMS Pro

A modern warehouse management system built with Python, Flask, and PostgreSQL.

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

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11 + Flask 3.0 |
| Database | PostgreSQL (production) / SQLite (local) |
| ORM | Flask-SQLAlchemy |
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
set SEED_DATA=true
python app.py
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
├── app.py              # Application entry point
├── config.py           # Configuration settings
├── models/             # SQLAlchemy data models
│   ├── category.py
│   ├── location.py
│   ├── order.py
│   ├── product.py
│   └── transaction.py
├── routes/             # Flask blueprints
│   ├── dashboard.py
│   ├── inventory.py
│   ├── locations.py
│   ├── receiving.py
│   ├── shipping.py
│   └── reports.py
├── templates/          # Jinja2 HTML templates
├── static/             # CSS and assets
├── Dockerfile          # Docker configuration
├── render.yaml         # Render blueprint
└── requirements.txt    # Python dependencies
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | SQLite (local) |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `SEED_DATA` | Set to `true` to seed sample data | `false` |
| `PORT` | Server port | `5000` |

---

## License

MIT License
