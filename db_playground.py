import os
from contextlib import closing
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


def find_project_by_name(connection, project_name):
    """Вернуть (id, name) найденного проекта или None."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name
            FROM projects
            WHERE name = %s
            ORDER BY id
            """,
            (project_name,),
        )

        return cursor.fetchone()


def list_projects(connection):
    """Вернуть список проектов в виде [(id, name), ...]."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name
            FROM projects
            ORDER BY id
            """
        )

        return cursor.fetchall()


def find_project_by_id(connection, project_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, name
            FROM projects
            WHERE id = %s
            """,
            (project_id,)
        )

        return cursor.fetchone()


def main():
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)

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
        with connection:
            first_project = find_project_by_name(
                connection,
                "QA Database Basics",
            )
            second_project = find_project_by_name(
                connection,
                "O'Reilly QA",
            )

            print("Первый проект:", first_project)
            print("Второй проект:", second_project)

            assert first_project is not None, (
                "Не найден проект QA Database Basics"
            )
            assert second_project is not None, (
                "Не найден проект O'Reilly QA"
            )

            assert first_project[1] == "QA Database Basics"
            assert second_project[1] == "O'Reilly QA"

            missing_project = find_project_by_name(
                connection,
                "qa-project-that-does-not-exist-999999",
            )
            assert missing_project is None

            suspicious_name = find_project_by_name(
                connection,
                "' OR 1=1 --",
            )
            assert suspicious_name is None

            print("Find project by id", find_project_by_id(connection, 1))

            projects = list_projects(connection)
            print("Все проекты:", projects)

            project_ids = {project[0] for project in projects}

            assert first_project[0] in project_ids
            assert second_project[0] in project_ids

    print("Все проверки прошли. Соединение закрыто.")


if __name__ == "__main__":
    main()