# Kanboard API & PostgreSQL Tests

API integration tests for a local Kanboard instance backed by PostgreSQL.

The project verifies that tasks created through the JSON-RPC API are persisted correctly, belong to the expected project, and receive distinct IDs even when their titles are identical.

## Tech Stack

- Python
- pytest
- Requests
- psycopg2
- PostgreSQL 16
- Kanboard v1.2.45
- Docker Compose
- python-dotenv

## Test Coverage

- Task creation through the API with PostgreSQL persistence checks.
- Verification of task-to-project relationships using SQL joins.
- Creation of tasks with identical titles and distinct IDs.
- Exact comparison of expected and stored task records.

## Test Data Isolation

Each test receives a separate project created through the API. Tasks are created inside that project, and database checks use explicit record IDs.

A function-scoped fixture removes the test project directly from PostgreSQL during teardown. Foreign-key cascades remove its tasks. Cleanup then checks that both the project and its tasks are absent.

Cleanup runs after successful tests and assertion failures. It requires an available database and normal pytest teardown execution.

Database rollback is used to discard unfinished SQL transactions before cleanup. It cannot undo changes committed by the application through API requests.

Direct database cleanup is intended for this local test environment and the current scenarios without uploaded files or external notification workflows.

## Project structure

- `clients/` contains the JSON-RPC request helper.
- `db/` contains parameterized SQL queries.
- `tests/conftest.py` manages connections, test projects, and cleanup.
- `tests/test_tasks.py` contains API scenarios and database assertions.

## Getting Started

Run all commands from the repository root.

### 1. Install dependencies

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux and macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### 2. Configure the environment

Copy `.env.example` to `.env` and configure:

```dotenv
DB_HOST=localhost
DB_PORT=5433
DB_NAME=kanboard
DB_USER=kanboard
DB_PASSWORD=replace_with_local_database_password

API_URL=http://localhost:8081/jsonrpc.php
API_USERNAME=jsonrpc
API_TOKEN=replace_with_application_api_token
```

Keep `.env` out of version control.

### 3. Start the application

```bash
docker compose up -d
docker compose ps
```

Open [Kanboard](http://localhost:8081) to initialize the application.

For a fresh local installation, sign in with `admin` / `admin`. Open **Settings → API**, copy the application API token, and set `API_TOKEN` in `.env`.

The tests run on the host machine and connect to PostgreSQL through port `5433`. Kanboard connects to PostgreSQL over the internal Docker network.

### 4. Run the tests

```bash
python -m pytest -v
```

Run a specific scenario:

```bash
python -m pytest -v tests/test_tasks.py::test_two_tasks_with_identical_titles_have_different_ids
```

### 5. Stop the environment

```bash
docker compose down
```

Named volumes retain application and database data between runs.

## Implementation Notes

- SQL values are passed separately from query text using psycopg2 parameters.
- SQL helpers manage their own cursors; callers control transaction boundaries.
- Connections and HTTP sessions are managed by fixtures.
- API actions remain in test bodies when they are the behavior under test.
- Cleanup targets the specific project created for each test.
- Database checks intentionally depend on the Kanboard schema used by the pinned application version.