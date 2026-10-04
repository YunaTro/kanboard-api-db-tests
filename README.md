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

## Continuous Integration

[![API and DB checks](https://github.com/YunaTro/kanboard-api-db-tests/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/YunaTro/kanboard-api-db-tests/actions/workflows/tests.yml)

GitHub Actions runs the test suite on pushes to `main` and pull requests targeting `main`.

Each run:

1. Sets up Python and restores the pip dependency cache.
2. Installs and checks project dependencies.
3. Starts an isolated Kanboard and PostgreSQL environment with Docker Compose.
4. Waits for an authenticated API readiness check.
5. Runs pytest and records Allure results.
6. Generates and uploads the HTML report.
7. Prints service logs on failure and tears down the temporary environment.

Test failures keep the workflow failed even when report generation and publication succeed.

### Required Secrets

Configure these repository secrets under **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|---|---|
| `CI_DB_PASSWORD` | Password for the temporary PostgreSQL instance |
| `CI_API_TOKEN` | Shared API token for the CI Kanboard instance and test client |

The workflow passes these values through environment variables. A `.env` file is not required in CI.

The secret-based workflow is intended for branches within this repository. Pull requests from forks do not normally receive repository secrets.

## Allure Reports

[View the published Allure report](https://YunaTro.github.io/kanboard-api-db-tests/)

The workflow stores raw Allure results and generated HTML reports as separate artifacts with a 14-day retention period.

Reports are generated after test execution, including failed test runs when result files are available. If environment preparation fails before tests start, no test report is published.

For pushes to `main`, a separate deployment job publishes the generated report to GitHub Pages. Pull request runs produce downloadable artifacts without updating the public site.

The Pages site shows the most recently deployed report. If a later run cannot produce or deploy a report, the existing site remains available. Check the Actions run for the current pipeline status.

Allure history is not carried over between runs.

### GitHub Pages Setup

In **Settings → Pages → Build and deployment**, select **GitHub Actions** as the source.

The deployment uses the built-in GitHub Actions authentication mechanism; no personal access token is required.

### Local Report Generation

With the local application running and Allure Report 2 installed:

```bash
python -m pytest -v --alluredir=allure-results --clean-alluredir
allure generate allure-results --output allure-report --clean
allure open allure-report
```

Java is required for the Allure Report 2 CLI.

Generated results and reports are excluded from version control. Report attachments must not contain credentials or other sensitive data.