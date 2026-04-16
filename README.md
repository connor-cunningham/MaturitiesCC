# MaturitiesCC — Multifamily Loan Maturity Intelligence Platform

A local-first, single-user business development intelligence platform for tracking and prospecting against multifamily real estate loan maturities.

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Start the database

```bash
docker-compose up -d
```

PostgreSQL will be running on `localhost:5432`.

### 2. Set up the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env if needed (default values work with docker-compose)
```

### 3. Run database migrations

```bash
cd backend
alembic upgrade head
```

### 4. Seed with sample data

```bash
cd backend
python -m seed.seed_data
```

This inserts 15 owners, 30 properties, 50 loans, and computes initial scores.

### 5. Start the backend API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 6. Set up and start the frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

App available at: http://localhost:3000

---

## Project Structure

```
MaturitiesCC/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # REST API endpoints
│   │   ├── core/              # DB session, config, security
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── etl/               # Parsers, normalizers, entity resolution
│   │   ├── scoring/           # Rules-based opportunity scoring
│   │   └── integrations/      # Notion hook (v2)
│   ├── alembic/               # Database migrations
│   ├── seed/                  # Sample data script
│   └── tests/                 # Pytest test suite
└── frontend/
    ├── app/                   # Next.js 14 App Router pages
    ├── components/            # React components
    └── lib/                   # API client, types, helpers
```

---

## How Imports Work

1. **Upload**: Drag-drop an Excel or CSV file at `/import`. Select source type (CoStar, MSCI, Internal, Other).
2. **Preview**: The system reads sheet names and shows a sample of columns and rows.
3. **Import**: Click "Run Import". The pipeline:
   - Parses each row using the source-specific parser
   - Normalizes addresses, owner names, loan fields
   - Resolves entities against existing canonicals (owner → property → loan)
   - Auto-merges records with confidence ≥ 0.92
   - Queues pairs with confidence 0.70–0.92 for manual review
   - Creates new entities below 0.70
   - Re-runs the scoring engine
4. **Review**: Check the import summary for counts and errors.

### Column Mapping
Each source type has a built-in column detection template (CoStar/MSCI/Internal). If your columns differ, you can pass a custom `mapping_config` JSON when calling the API directly.

---

## Source-of-Truth Precedence

When data exists from multiple sources for the same field:

1. **Internal** (manually uploaded) — always wins
2. **MSCI** — second priority
3. **CoStar** — third priority

Raw source records are always preserved. The canonical record stores the winning value per field, plus a `provenance` JSON documenting which source contributed each field.

---

## Entity Resolution

### Owner Matching
- Normalize name: lowercase, remove LLC/LP/Inc/etc.
- Apply rapidfuzz WRatio fuzzy matching
- Bonus for matching city/state
- ≥0.92 confidence → auto-merge (add alias)
- 0.70–0.92 → create new + queue `match_candidates` for review
- <0.70 → create new entity

### Property Matching
- Normalize and parse address components
- Exact canonical address match → 1.0
- Fuzzy street + city/state combination scoring
- Name fuzzy match as fallback
- Same thresholds as above

### Loan Matching
- Same property + maturity within 30 days + amount within 5% → auto-merge
- Below threshold → create new

### Manual Overrides
- Use `POST /api/v1/uploads/imports/{run_id}/resolve` to accept/reject queued match candidates
- Manual overrides stored in `manual_match_overrides` table — never deleted

---

## Scoring Engine

The engine scores each loan 0–100 based on 8 configurable factors:

| Factor | Weight | Logic |
|--------|--------|-------|
| `months_to_maturity` | 35% | <6mo=100, <12mo=85, <24mo=65, <36mo=40, else=10 |
| `loan_amount` | 25% | $50M+=100, $20-50M=80, $10-20M=60, $5-10M=40, <$5M=20 |
| `portfolio_concentration` | 15% | 3+ maturities same owner=100, 2=60, 1=20 |
| `rate_type` | 10% | Floating=100, Variable=75, Fixed=20 |
| `io_flag` | 5% | IO=100, Amortizing=20 |
| `outreach_status` | 5% | Warm=100, Cold=80, Contacted=30, DNC=0 |
| `building_class` | 3% | C=80, B=50, A=30 |
| `market_tier` | 2% | Primary=80, Secondary=60, Other=40 |

### Editing Weights
- View/edit at `GET /api/v1/scoring/configs`
- Create a new config with custom weights, set `is_active: true`
- Re-run: `POST /api/v1/scoring/run`
- Score breakdown visible on each Loan detail page

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

Tests cover:
- Normalizers (name, address, field parsing)
- Parsers (CoStar, Internal)
- Entity resolution (fuzzy matching logic)
- Scoring (factor functions, composite scoring)

---

## Phase 2 Roadmap

### API Ingestion Adapters
- `backend/app/etl/parsers/` is designed to accept new parser classes
- To add a CoStar API adapter: create `costar_api.py` extending `BaseParser`, override `parse()`

### Notion Sync
- `backend/app/integrations/notion/` contains the `NotionSyncAdapter` interface
- Implement `sync_owner()`, `sync_note()`, `sync_activity()`
- Wire into CRM write routes

### Geocoding
- Add a geocoding step in the ETL pipeline (`etl/geocoder.py`)
- Use Nominatim (free) or Google Maps API
- Store lat/lng on `canonical_properties`

### Cloud Deployment
- Replace `docker-compose` PostgreSQL with AWS RDS or Cloud SQL
- Deploy FastAPI on Fly.io, Railway, or AWS ECS
- Deploy Next.js on Vercel
- Move uploads from local filesystem to S3

### Contact Management
- Extend `canonical_owners` with `contacts` table
- Add contact names, emails, phone numbers
- Track per-contact outreach history

### Email / Call Logging
- Add `email_logs` and `call_logs` tables
- Wire into outreach_activities
