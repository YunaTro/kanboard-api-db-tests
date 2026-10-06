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
- Dockerfile
- python-dotenv
- allure
- GitHub Actions

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

## Running Tests with Docker

Docker Compose runs three services:

- `postgres` — the application database.
- `kanboard` — the application under test.
- `tests` — Python, project dependencies, and the pytest suite built from the project Dockerfile.

Configure `.env` as described in the setup instructions. For local runs, `API_TOKEN` must match the token accepted by the local Kanboard instance.

Build the test image and run the suite:

```bash
docker compose build tests
docker compose up -d postgres kanboard
docker compose run --rm -T tests
```

The test container waits for the authenticated API readiness check before starting pytest. It connects to Kanboard and PostgreSQL through the Compose network using service names and internal ports.

Test source files are copied into the image. Rebuild it after changing tests, helpers, dependencies, or the Dockerfile.

The `tests` service uses a Compose profile, so a regular `docker compose up -d` does not start the test suite.

### Test Results

Allure results are written to a bind-mounted `allure-results/` directory and remain available after the test container is removed.

Generate and open the HTML report with a locally installed Allure Report 2 CLI:

```bash
allure generate allure-results --output allure-report --clean
allure open allure-report
```

### Stopping the Environment

```bash
docker compose down
```

This preserves the named database volume. Adding `--volumes` also deletes the environment's named volumes and their stored data.

## Containerized CI

GitHub Actions builds the test image, starts a temporary Kanboard and PostgreSQL environment, and runs the suite inside the test container.

Credentials are supplied at runtime through GitHub Secrets. The `.dockerignore` file excludes local environment files, virtual environments, and generated reports from the build context.

Java and the Allure CLI run on the GitHub runner. They generate the HTML report from the results written by the container. Raw results and HTML reports are uploaded as artifacts; reports from pushes to `main` are also published to GitHub Pages.

Test failures keep the workflow failed while allowing available results to be processed. If API readiness fails before pytest starts, no test report is generated.

CI teardown removes the temporary containers and named volumes. Docker build cache is not currently persisted between workflow runs.

## Unit Tests and Mocking

Unit tests use `pytest-mock` to verify API wrapper and service behavior without running Kanboard or PostgreSQL.

### Coverage

- Successful JSON-RPC responses: extracting the result and verifying the request URL, payload, and timeout.
- HTTP 500 responses: rejecting unsuccessful responses with `AssertionError`, as defined by the current API wrapper implementation.
- Transport errors: propagating `Timeout` and `ConnectionError` exceptions.
- Missing tasks: preserving a `None` result returned by the API wrapper.
- Service calls: verifying method names, parameters, call counts, and call order.

Service tests mock the `call_api` wrapper. Tests of the wrapper itself mock `session.post`, allowing the actual request-building and response-handling logic to execute without network access.

### Running Unit Tests

From the project root, with dependencies installed:

```bash
python -m pytest tests/unit -v
```

No running application or database is required for these tests. Integration tests remain responsible for verifying real API behavior and data persistence in PostgreSQL.