import os
from contextlib import closing
from pathlib import Path
from uuid import uuid4

import psycopg2
import pytest
import requests
from dotenv import load_dotenv

from clients.kanboard_api import call_api

@pytest.fixture(scope="session", autouse=True)
def load_environment():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)


@pytest.fixture
def api_session(load_environment):
    with requests.Session() as session:
        session.auth = (
            os.environ["API_USERNAME"],
            os.environ["API_TOKEN"],
        )
        yield session


@pytest.fixture
def db_connection(load_environment):
    with closing(
        psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            connect_timeout=5,
        )
    ) as connection:
        yield connection


@pytest.fixture
def created_project(api_session):
    project_name = f"QA DB {uuid4().hex}"

    project_id = call_api(
        api_session,
        "createProject",
        {"name": project_name},
    )
    assert type(project_id) is int and project_id > 0, (
        f"Unexpected createProject result: {project_id!r}"
    )

    try:
        yield {
            "id": project_id,
            "name": project_name,
        }
    finally:
        removed = call_api(
            api_session,
            "removeProject",
            {"project_id": project_id},
        )
        assert removed is True, (
            f"Could not remove test project {project_id}"
        )