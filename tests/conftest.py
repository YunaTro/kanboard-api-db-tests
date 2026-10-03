import os
from contextlib import closing
from pathlib import Path
from uuid import uuid4

import psycopg2
import pytest
import requests
from dotenv import load_dotenv

from clients.kanboard_api import call_api
from db.queries import (
    delete_project_by_id,
    find_project_by_id,
    list_tasks_with_project,
)

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
def created_project(api_session, db_connection):
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
        db_connection.rollback()
        with db_connection:
            delete_project_by_id(db_connection, project_id)
        with db_connection:
            remaining_project = find_project_by_id(
                db_connection,
                project_id,
            )

            with db_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM tasks WHERE project_id = %s",
                    (project_id,),
                )
                remaining_tasks = cursor.fetchall()

        assert remaining_project is None, (
            f"Project {project_id} still exists after DB cleanup"
        )
        assert remaining_tasks == [], (
            f"Tasks remain for project {project_id}: {remaining_tasks!r}"
        )