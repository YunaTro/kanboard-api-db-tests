import os
from contextlib import closing
from pathlib import Path
from uuid import uuid4

import psycopg2
import requests
from dotenv import load_dotenv


def call_api(session, method, params):
    request_id = uuid4().hex

    response = session.post(
        os.environ["API_URL"],
        json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id,
        },
        timeout=(3, 15),
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["jsonrpc"] == "2.0"
    assert body["id"] == request_id
    assert "error" not in body, body

    return body["result"]


def find_project_by_id(connection, project_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name
            FROM projects
            WHERE id = %s
            """,
            (project_id,),
        )
        return cursor.fetchone()


def find_task_with_project(connection, task_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                t.id,
                t.title,
                p.id,
                p.name
            FROM tasks AS t
            JOIN projects AS p ON p.id = t.project_id
            WHERE t.id = %s
            """,
            (task_id,),
        )
        return cursor.fetchone()

def rename_task(connection, project_id, task_id, new_title):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE tasks
            SET title = %s
            WHERE id = %s AND project_id = %s
            RETURNING id, title, project_id
            """,
            (new_title, task_id, project_id),
        )
        return cursor.fetchone()

def list_tasks_with_project(connection, project_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT t.id, t.title, p.id, p.name
            FROM tasks AS t
            JOIN projects AS p ON p.id = t.project_id
            WHERE p.id = %s
            ORDER BY t.id
            """,
            (project_id,)
        )
        return cursor.fetchall()

def find_tasks_by_title(connection, project_id, title):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title
            FROM tasks
            WHERE project_id = %s AND title = %s
            ORDER BY id
            """,
            (project_id, title)
        )
        return cursor.fetchall()

def main():
    load_dotenv(Path(__file__).resolve().parent / ".env")

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
        with requests.Session() as session:
            session.auth = (
                os.environ["API_USERNAME"],
                os.environ["API_TOKEN"],
            )

            project_name = f"QA API DB {uuid4().hex[:8]}"
            number_of_tasks = 2
            task_titles = [
                f"Check data persistence task {uuid4().hex[:8]}"
                for i in range(number_of_tasks)
            ]

            project_id = call_api(
                session,
                "createProject",
                {"name": project_name},
            )

            assert type(project_id) is int and project_id > 0, (
                f"Unexpected createProject result: {project_id!r}"
            )

            try:
                with connection:
                    project_row = find_project_by_id(
                        connection,
                        project_id,
                    )

                assert project_row is not None, (
                    f"Project {project_id} was not found in PostgreSQL"
                )
                assert project_row == (project_id, project_name)

                with connection:
                    task_rows = list_tasks_with_project(
                        connection,
                        project_id,
                    )
                assert task_rows == [], (
                    f"Expected no tasks in project {project_id}, got {task_rows!r}"
                )

                task_ids = []
                for title in task_titles:
                    task_id = call_api(
                        session,
                        "createTask",
                        {
                            "title": title,
                            "project_id": project_id,
                        },
                    )
                    assert type(task_id) is int and task_id > 0, (
                        f"Unexpected createTask result: {task_id!r}"
                    )
                    task_ids.append(task_id)

                with connection:
                    task_rows = list_tasks_with_project(
                        connection,
                        project_id,
                    )

                expected_rows = sorted(
                    (
                        task_id,
                        title,
                        project_id,
                        project_name,
                    )
                    for task_id, title in zip(task_ids, task_titles, strict=True)
                )
                assert task_rows == expected_rows

                print("Project in DB:", project_row)
                print("Tasks joined with project:", task_rows)

                task_id = task_ids[0]
                new_title = "O'Reilly QA: updated task"

                # Изменяем задачу и фиксируем изменение при успешных проверках.
                with connection:
                    updated_row = rename_task(
                        connection,
                        project_id,
                        task_id,
                        new_title,
                    )

                    assert updated_row is not None, (
                        f"Task {task_id} was not found in project {project_id}"
                    )
                    assert updated_row == (task_id, new_title, project_id)

                # Отдельно читаем сохранённое состояние.
                with connection:
                    saved_row = find_task_with_project(connection, task_id)

                assert saved_row == (
                    task_id,
                    new_title,
                    project_id,
                    project_name,
                )

                with connection:
                    found_task = find_tasks_by_title(connection, project_id, new_title)
                assert found_task == [(task_id, new_title)]
                with connection:
                    suspicious_name = find_tasks_by_title(
                        connection,
                        project_id,
                        "' OR 1=1 --",
                    )
                assert suspicious_name == [], "Expected no tasks with suspicious name"
                try:
                    with connection:
                        rename_task(
                            connection,
                            project_id,
                            task_id,
                            "Temporary title"
                        )
                        found = find_task_with_project(connection, task_id)
                        assert found == (task_id, "Temporary title", project_id, project_name)
                        raise RuntimeError("Rollback exercise")
                except RuntimeError:
                    pass
                with connection:
                    found = find_task_with_project(connection, task_id)
                assert found == (task_id, new_title, project_id, project_name)

            finally:
                removed = call_api(
                    session,
                    "removeProject",
                    {"project_id": project_id},
                )
                assert removed is True, (
                    f"Could not remove project {project_id}"
                )

    print("Checks passed. Temporary project removed.")


if __name__ == "__main__":
    main()