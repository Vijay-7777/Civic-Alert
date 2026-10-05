# CrimeLens

CrimeLens is a civic safety platform for submitting and tracking community
reports. It combines a Next.js web application with a FastAPI assistant API,
SQLite storage, optional AI assistance, and map-based location features.

> **Status:** This project is under active development. Do not use it as a
> replacement for emergency services. For an immediate emergency, contact
> your local emergency number.

## Features

- Anonymous or identified report submission
- Report tracking and status updates
- Interactive map and reverse geocoding
- Department routing and report management
- AI assistant for locality and report-related questions
- Optional Gemini, Ollama, news, weather, and Qdrant integrations
- Authentication and protected application routes

## Project structure

```text
frontend/
  src/app/               Next.js pages and API routes
  src/components/        Shared, map, report, feedback, and UI components
  src/lib/               Authentication, database, and utilities
  src/types/             TypeScript declarations
  scripts/               Database migration and seed utilities
  data/                  Local SQLite database (not committed)
  package.json           Frontend dependencies and scripts
backend/
  app/                   FastAPI API and assistant implementations
  tests/                 Integration and feature checks
  docs/                  Integration and architecture notes
  requirements/legacy/   Historical dependency lists
  requirements.txt       Core API dependencies
scripts/
  start.ps1              Windows launcher for both services
```

The database and seed input are kept in the frontend because the frontend and
backend share the same SQLite file. Backend model configuration and diagnostic
scripts remain in `backend/` because some load `.env` relative to that folder.

## Prerequisites

- Windows PowerShell
- Node.js 18 or newer and npm
- Python 3.11 or newer
- Git

The core application runs without optional AI services. Gemini, Ollama,
Qdrant, news, weather, and embedding integrations require their own services
and credentials.

## Installation and configuration

From the repository root, create the backend virtual environment and install
the core dependencies:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm.cmd --prefix frontend install
```

Create local environment files from the safe templates:

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Edit both files and replace placeholder values with your own development
settings. Never commit `.env` files, API keys, authentication secrets, or
local database files. The repository `.gitignore` excludes them by default.

## Run the application

To start both services in the background:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start.ps1
```

The application is then available at:

- Frontend: <http://localhost:3000>
- API: <http://localhost:8000>
- API documentation: <http://localhost:8000/docs>

The launcher writes runtime logs to `logs/` and prints the process IDs. Stop
the processes before starting another copy on the same ports.

For foreground development, use two terminals:

```powershell
cd frontend
npm.cmd run dev
```

```powershell
cd backend
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Database

Fresh clones do not include the local SQLite database. To create and seed a
development database, run:

```powershell
npm.cmd --prefix frontend run setup
```

This runs the frontend migration and seed scripts. Do not run `seed` or
`db:reset` against an existing database unless you intend to change or
replace its data.

## Optional integrations

The core backend starts the API and basic assistant. Set the relevant
variables in `backend/.env` only when using optional integrations:

- **Gemini:** set `GEMINI_API_KEY`, `GEMINI_MODEL`, and `USE_GEMINI_API=true`.
- **Ollama:** run Ollama locally and configure `OLLAMA_URL` and
  `OLLAMA_MODEL`.
- **Qdrant/vector search:** run Qdrant and configure `QDRANT_URL` plus the
  embedding settings.
- **News and weather:** provide the relevant news and weather API keys.

Optional imports are handled with fallbacks where supported. Historical files
under `backend/requirements/legacy/` are reference configurations, not a
single installation recipe.

## Validation

Run the frontend checks from the repository root:

```powershell
npm.cmd --prefix frontend exec tsc -- --noEmit
npm.cmd --prefix frontend run build
```

Run a focused backend check:

```powershell
backend/.venv/Scripts/python.exe -m tests.test_routing
```

Some backend checks call external services or create reports. Review a test
before running it against existing data.


