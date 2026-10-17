# US Backend

A FastAPI backend scaffold based on the structure used by `fuds_backend`.

## Project Structure

```text
us/
├── alembic/
│   └── versions/                 # Database migration history
├── api/
│   ├── core/                     # Application-wide configuration and security
│   ├── db/
│   │   └── session.py            # SQLAlchemy engine and session setup
│   ├── tasks/                    # Celery/background tasks
│   ├── utils/                    # Shared integrations and helpers
│   └── v1/
│       ├── models/               # SQLAlchemy database models
│       ├── schema/               # Pydantic request/response schemas
│       ├── services/             # Business logic and data access
│       └── routes/               # FastAPI endpoint routers
├── scripts/                      # Administrative and seed scripts
├── static/                       # Files served by the application
├── tests/                        # Pytest test suite
├── main.py                       # FastAPI application entry point
├── alembic.ini                   # Alembic configuration
├── requirements.txt              # Python dependencies
├── .env.example                  # Documented environment variables
├── .gitignore
└── README.md
```

## Architecture Rules

- Keep HTTP concerns in `api/v1/routes`.
- Keep validation and serialization in `api/v1/schema`.
- Keep database models in `api/v1/models`.
- Keep business logic in `api/v1/services`.
- Put cross-cutting configuration and integrations in `api/core`, `api/db`, `api/tasks`, and `api/utils`.
- Add new endpoint groups under a versioned namespace such as `api/v1`.
- Add a focused test under `tests` for every new service or route workflow.
- Add schema changes through Alembic migrations in `alembic/versions`.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Run tests with:

```bash
pytest
```

The application modules and domain models can be added incrementally without changing this layout.
