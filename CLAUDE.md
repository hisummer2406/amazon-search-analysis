# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amazon Search Analysis System - A professional Amazon search term data analysis platform supporting GB-level file processing, real-time data analysis, and visualization. Built with FastAPI + PostgreSQL, serving ~200 concurrent users for read-heavy operations with periodic batch data imports (~500K records per batch).

## Development Commands

```bash
# Local development
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest test/

# Docker deployment
docker-compose up -d
docker-compose logs -f app | grep upload  # Monitor upload logs
docker-compose restart app  # Restart app container

# Database operations
# Uses PostgreSQL with schema "analysis"
# Connection: sync (psycopg2) + async (asyncpg) engines both configured
```

## Architecture

### Module Structure

```
app/
├── auth/              # JWT authentication + middleware (simple_auth.py for user validation)
├── table/
│   ├── analysis/      # Core data analysis (model, crud, service, api layers)
│   ├── search/        # Search schemas and components
│   └── upload/        # CSV file upload and processing (csv_processor.py handles GB files)
└── user/              # User management (model, crud, api, admin)

main.py                # FastAPI app entry, lifespan management, health check
config.py              # Pydantic settings (env-based config)
database.py            # SQLAlchemy 2.0 sync + async engines, session factories
```

### Layered Architecture Pattern

**All table modules follow strict layering:**

1. **Model** (`*_model.py`): SQLAlchemy 2.0 ORM models using `DeclarativeBase`, schema-qualified
2. **CRUD** (`*_crud.py`): Database access layer, no business logic
3. **Service** (`*_service.py`): Business logic, calls CRUD layer
4. **API** (`*_api.py`): FastAPI routers, thin controllers calling services
5. **Schemas** (`*_schemas.py`): Pydantic v2 models for request/response DTOs

**Example**: `app/table/analysis/` - `analysis_api.py` → `analysis_service.py` → `analysis_crud.py` → `analysis_model.py`

### Data Import Flow

**CSV Upload Processing** (in `app/table/upload/upload_api.py` + `csv_processor.py`):
- Validates CSV structure (metadata + header + data rows)
- Chunks files using pandas (configurable `BATCH_SIZE`, default 6000)
- Uses PostgreSQL UPSERT (`INSERT ... ON CONFLICT DO UPDATE`) for deduplication
- Implements connection retry and mini-batch commits (`MINIBATCH_SIZE=500`)
- Supports both daily and weekly data types with different field mappings
- Ranking trend stored as JSONB array (last 7 days)

### Authentication & Authorization

- JWT-based authentication via `fastapi-user-auth` + custom `simple_auth.py`
- Middleware: `AdminAuthMiddleware` validates tokens from Cookie/Authorization header
- Default admin: `admin / pwd123` (change `ADMIN_SECRET_KEY` in production)

### Database Design

**Schema**: `analysis`

**Main Table**: `amazon_origin_search_data`
- Unique constraint on `keyword`
- Stores daily + weekly ranking data in same row
- JSONB field `ranking_trend_day` for 7-day history
- Indexed on: `report_date_day`, `current_rangking_day`, `top_brand`, `top_category`

**View**: `my_category_stats` - Category statistics for dropdown options

### Performance Optimizations

1. **Connection Pooling**: `DB_POOL_SIZE=100`, `MAX_OVERFLOW=50`, `POOL_RECYCLE=1800s`
2. **Query Optimization**:
   - Uses PG statistics estimates (`pg_class.reltuples`) for total count on large tables
   - `LIMIT 10000` count for filtered queries on pagination
   - Default filter excludes keywords containing brand name and rank=0 records
   - Blacklist categories filtered out (Books, Grocery, Video Games, etc.)
3. **Batch Processing**: `BATCH_SIZE=6000` for pandas chunks, `MINIBATCH_SIZE=500` for DB commits
4. **Multi-processing**: Configurable `MAX_WORKERS=4` for files > `MULTIPROCESSING_THRESHOLD_MB=100MB`

## Key Configuration (.env)

```bash
# Database (sync + async URLs both required)
DATABASE_URL=postgresql://user:pass@host/db
DATABASE_URL_ASYNC=postgresql+asyncpg://user:pass@host/db
DATABASE_SCHEMA=analysis

# Upload
MAX_FILE_SIZE=3221225472  # 3GB
BATCH_SIZE=6000
MINIBATCH_SIZE=500

# Performance
DB_POOL_SIZE=100
DB_MAX_OVERFLOW=50
```

## Important Constraints

1. **SQLAlchemy 2.0 Only**: No `.query()`, use `select()` with session
2. **Dual Engines**: Both sync (`engine`) and async (`async_engine`) available - choose appropriately
3. **Schema Qualification**: All models use `schema=settings.DATABASE_SCHEMA`
4. **UPSERT Logic**: CSV imports use raw SQL with `ON CONFLICT (keyword) DO UPDATE` for complex ranking trend JSONB manipulation
5. **Transaction Boundaries**: Service layer controls commits, CRUD layer never commits
6. **Pydantic v2**: Uses `model_config = ConfigDict(...)`, `field_validator`