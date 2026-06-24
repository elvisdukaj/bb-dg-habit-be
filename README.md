# Habit Tracker Backend

A FastAPI-based REST API for managing daily and weekly habits. Features user authentication via JWT, SQLite database, and comprehensive test coverage.

## Getting Started

### Prerequisites
- Python 3.12+
- `uv` package manager

### Installation

```bash
uv sync --extra dev
uv run opentelemetry-bootstrap -a install
```

`opentelemetry-bootstrap` auto-detects the installed packages and installs the matching OTel instrumentation libraries (FastAPI, SQLAlchemy, etc.).

### Running the Server

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Running with OpenTelemetry (Bluebox)

1. Copy `.env.otel.bluebox-template` to `.env.otel` (already done — it is git-ignored).
2. Open Bluebox → Onboarding → Instrumentation setup → **Reveal token**.
3. Replace `REPLACE_WITH_YOUR_DYNATRACE_TOKEN` in `.env.otel` with your token.
4. Start the server through the OTel launcher:

```bash
env $(grep -v '^#' .env.otel | xargs) uv run opentelemetry-instrument uvicorn app.main:app
```

The `opentelemetry-instrument` wrapper auto-instruments FastAPI, SQLAlchemy, and HTTP clients with zero code changes.

### Interactive API Documentation

FastAPI auto-generates interactive docs:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI spec:** http://localhost:8000/openapi.json

Or see the checked-in spec: [`openapi.json`](./openapi.json)

## Testing

Run the full test suite (20 tests covering auth and habits):

```bash
uv run pytest -v
```

Or with coverage:

```bash
uv run pytest --cov=app
```

## API Endpoints

### Authentication
- `POST /api/auth/register` — Create a new user account
- `POST /api/auth/login` — Log in and get a Bearer token

### Habits
All habit endpoints require a Bearer token (obtained from login).

- `POST /api/habits` — Create a habit
- `GET /api/habits` — List all habits for the user
- `GET /api/habits/{id}` — Get a single habit
- `PUT /api/habits/{id}` — Update a habit
- `DELETE /api/habits/{id}` — Delete a habit

See [`openapi.json`](./openapi.json) for full request/response schemas.

## Project Structure

```
app/
├── main.py              # FastAPI app setup
├── config.py            # Settings (database, JWT)
├── database.py          # SQLAlchemy setup
├── dependencies.py      # Shared dependency injection
├── models/              # User and Habit ORM models
├── schemas/             # Pydantic request/response schemas
├── services/auth.py     # Password hashing and JWT
└── routers/             # API endpoints
tests/
├── conftest.py          # Test fixtures
├── test_auth.py         # Auth endpoint tests
└── test_habits.py       # Habit CRUD tests
```

## Development

### Environment Variables

Create a `.env` file to override defaults:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./habits.db
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Database

The app uses SQLite. The database file is created automatically on startup at `./habits.db` (or the path specified in `DATABASE_URL`).

To reset the database, simply delete the `.db` file and restart the server.

## Tech Stack

- **Framework:** FastAPI 0.115+
- **Database:** SQLAlchemy 2.0 + SQLite
- **Auth:** bcrypt + JWT (python-jose)
- **Validation:** Pydantic v2
- **Testing:** pytest + httpx TestClient
- **Package Manager:** uv

## Spec

This API is built from the specification in the [`spec`](./spec) file in the repository root.
