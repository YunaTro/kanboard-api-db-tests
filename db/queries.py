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


def delete_project_by_id(connection, project_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM projects
            WHERE id = %s
            RETURNING id
            """,
            (project_id,),
        )
        return cursor.fetchone()