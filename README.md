# BlueStock Nifty 100 — Financial Intelligence System

An advanced data engineering, analytics, and intelligence platform for India's Top 100 (Nifty 100) companies. This project processes financial statements (Profit & Loss, Balance Sheets, Cash Flows) using a robust ETL pipeline, loads them into a star-schema database, analyzes company performance using ML scoring algorithms, and displays them via a dashboard and a REST API.

---

## 🛠️ Tech Stack & Components

1. **Backend Framework**: Django 4.2+ / 6.0+ & Django REST Framework (DRF)
2. **Database**: 
   - **SQLite**: (Default for lightweight local development, pre-populated)
   - **PostgreSQL**: (Production-grade star-schema data warehouse, available via Docker Compose)
3. **Data Engineering**: Pandas, NumPy, Scikit-learn (ML scoring and categorization), OpenPyXL
4. **Background Task Queue**: Celery & Redis (for executing periodic analytics or async operations)
5. **Aesthetics / Frontend**: Vanilla CSS with modern dark-mode elements and interactive components
6. **API Documentation**: OpenAPI / Swagger (`drf-spectacular`)

---

## 🚀 How to Run the Project

You can run this project in two ways: **natively on your local machine** (easiest, using SQLite) or **using Docker Compose** (full-stack with PostgreSQL, Redis, and Celery).

### Option A: Native Local Execution (SQLite) — *Recommended for Quick Start*

Since the project repository comes with a pre-populated SQLite database (`db.sqlite3`), you can start the development server immediately.

#### 1. Setup Virtual Environment (Optional but Recommended)
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Setup Environment Variables
Verify that your `.env` file in the root folder contains the default SQLite configurations:
```ini
SECRET_KEY=django-insecure-bluestock-n100-dev-key-change-in-production
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### 4. Run the Django Server
Start the Django development server:
```bash
python manage.py runserver
```
Visit the application in your browser at: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

### Option B: Run with Docker Compose (PostgreSQL, Redis & Celery)

This starts the full suite of services, including the PostgreSQL database container, Redis broker, Celery worker, and the Django web container.

#### 1. Start Docker Desktop
Ensure that Docker Desktop is running on your machine.

#### 2. Launch the Services
From the root directory (where `docker-compose.yml` is located), run:
```bash
docker compose up --build
```

Docker will:
1. Boot a PostgreSQL 15 database instance (`db` service).
2. Boot a Redis broker (`redis` service).
3. Build the Django container (`web` service) and launch the server at `0.0.0.0:8000`.
4. Build the Celery worker container (`celery` service) to handle background analytics.

Once build and startup are complete, visit: **[http://localhost:8000/](http://localhost:8000/)**

---

## 🔄 Running the ETL Pipeline

If you want to extract raw financial sheets, transform the data, and reload it into the database, you can run the ETL scripts sequentially:

```bash
# Step 1: Extract data (parses source spreadsheets/endpoints into raw CSVs)
python etl/01_extract_from_excel.py

# Step 2: Clean and transform the data (standardizes schemas and computes indicators)
python etl/02_clean_and_transform.py

# Step 3: Load into the warehouse (inserts/upserts rows into the active database)
python etl/03_load_to_warehouse.py
```

*Note: The loading script `03_load_to_warehouse.py` automatically detects whether you are using SQLite or PostgreSQL (based on your `.env` or Docker configuration) and populates the appropriate database.*

---

## 📂 Key Endpoints & Routes

Once the server is running, the following endpoints are available:

### 🖥️ Dashboard Views
* **Dashboard Homepage**: `http://127.0.0.1:8000/` — Main interface with market capitalization charts, financial trends, and list of Nifty 100 companies.
* **Sectors Overview**: `http://127.0.0.1:8000/sectors/` — Sector-wise breakdown of companies.
* **Company Detail Page**: `http://127.0.0.1:8000/company/<symbol>/` — Detailed financial statements, ML-based scores, pros/cons, and interactive charts for a specific stock (e.g., `http://127.0.0.1:8000/company/RELIANCE/`).

### 🔌 API Endpoints
* **API Home**: `http://127.0.0.1:8000/api/`
* **Swagger Documentation**: `http://127.0.0.1:8000/api/docs/` — Fully interactive Swagger UI listing all available endpoints, query parameters, and schemas.
* **Sectors API**: `http://127.0.0.1:8000/api/sectors/`
* **Companies API**: `http://127.0.0.1:8000/api/companies/`
* **ML scores**: `http://127.0.0.1:8000/api/ml-scores/`
* **Dashboard Stats API**: `http://127.0.0.1:8000/api/dashboard-stats/`
* **Company Chart Data API**: `http://127.0.0.1:8000/api/companies/<symbol>/chart-data/`
