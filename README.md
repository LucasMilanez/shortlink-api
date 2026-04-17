# ShortLink API

[![CI](https://github.com/LucasMilanez/shortlink-api/actions/workflows/ci.yml/badge.svg)](https://github.com/LucasMilanez/shortlink-api/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

URL shortener REST API with click analytics, JWT authentication, and per-user link ownership. Built with **FastAPI**, **SQLAlchemy 2.0**, and **Pydantic v2**.

> **Live demo:** <https://shortlink-api.onrender.com/docs> *(update after deploy)*  
> **Interactive API docs:** `/docs` (Swagger UI) · `/redoc` (ReDoc)

---

## Features

- 🔐 JWT authentication with OAuth2 password flow
- 🔗 Unique short code generation with collision retry
- 📊 Click analytics — count, user agent, referrer, timestamps
- 👤 Per-user link ownership and authorization checks
- ✅ 20+ pytest tests with coverage reporting
- 🐳 Production-ready multi-stage Dockerfile (non-root user, healthcheck)
- 🚦 Continuous Integration via GitHub Actions (tests + lint)
- 📖 Auto-generated OpenAPI/Swagger docs

## Tech Stack

| Layer        | Technology                                              |
| ------------ | ------------------------------------------------------- |
| **Backend**  | FastAPI, Uvicorn, Pydantic v2                           |
| **Database** | SQLAlchemy 2.0, PostgreSQL (prod) / SQLite (dev & test) |
| **Auth**     | python-jose (JWT), bcrypt                               |
| **Testing**  | pytest, httpx, pytest-cov                               |
| **DevOps**   | Docker, docker-compose, GitHub Actions, ruff            |

## Project Structure

```
shortlink-api/
├── app/
│   ├── main.py          # FastAPI routes
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database operations
│   ├── auth.py          # JWT + password hashing
│   ├── database.py      # DB engine & session
│   └── config.py        # Settings (pydantic-settings)
├── tests/
│   ├── conftest.py      # Fixtures (in-memory SQLite)
│   ├── test_auth.py
│   └── test_links.py
├── .github/workflows/
│   └── ci.yml           # GitHub Actions pipeline
├── Dockerfile           # Multi-stage, non-root
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Quick Start

### Option 1 — Local (Python 3.12+)

```bash
# Clone and enter
git clone https://github.com/LucasMilanez/shortlink-api.git
cd shortlink-api

# Virtual env
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Generate a real SECRET_KEY:
#   openssl rand -hex 32
# and paste it into .env

# Run
uvicorn app.main:app --reload
```

API available at <http://localhost:8000> — interactive docs at <http://localhost:8000/docs>

### Option 2 — Docker

```bash
cp .env.example .env  # edit SECRET_KEY first
docker compose up --build
```

## API Reference

### Authentication

| Method | Endpoint          | Description                 | Auth |
| ------ | ----------------- | --------------------------- | ---- |
| POST   | `/auth/register`  | Create a new user account   | —    |
| POST   | `/auth/login`     | Obtain JWT access token     | —    |

### Links

| Method | Endpoint                   | Description                         | Auth |
| ------ | -------------------------- | ----------------------------------- | ---- |
| POST   | `/links`                   | Create a short link                 | JWT  |
| GET    | `/links`                   | List all links owned by current user| JWT  |
| GET    | `/links/{id}/stats`        | Get click stats + recent timestamps | JWT  |
| DELETE | `/links/{id}`              | Delete a link (and its clicks)      | JWT  |
| GET    | `/r/{short_code}`          | Public redirect + click tracking    | —    |

### Example Flow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","password":"password123"}'

# 2. Login → get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=me@example.com&password=password123" \
  | jq -r .access_token)

# 3. Create short link
curl -X POST http://localhost:8000/links \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target_url":"https://github.com/LucasMilanez"}'
# → {"id":1,"short_code":"Xy2_kqP","target_url":"https://github.com/...", ...}

# 4. Use it (follows the redirect)
curl -L http://localhost:8000/r/Xy2_kqP

# 5. Check analytics
curl http://localhost:8000/links/1/stats -H "Authorization: Bearer $TOKEN"
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest -v --cov=app --cov-report=term-missing
```

Tests run against an isolated in-memory SQLite database — no external dependencies, fully parallelizable.

## Deployment (Render — free tier)

1. Push this repo to GitHub
2. At <https://render.com> → **New Web Service** → connect the repo
3. Runtime: **Docker**
4. Environment variables:
   - `SECRET_KEY` — generate with `openssl rand -hex 32`
   - `DATABASE_URL` — create a free PostgreSQL instance on Render and paste its URL
5. Deploy. First build takes ~3 minutes.

## Design Notes

- **SQLAlchemy 2.0 with session-per-request** via FastAPI dependency injection
- **Collision-safe short codes** with bounded retry loop (5 attempts — probability of failure is negligible at 7 chars of `secrets.token_urlsafe`)
- **HTTP 302 (Found) for redirects** — avoids browser caching so every click hits the server and gets tracked. Use 301 only for permanent, cacheable redirects where analytics don't matter
- **Click tracking is synchronous** for simplicity. For high traffic, this would move to a background task or message queue
- **Authorization on every link query** — users can only access their own resources (`WHERE owner_id = ?`)
- **No password in response schemas** — `hashed_password` never leaves the database layer

## License

MIT
