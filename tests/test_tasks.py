from clients.kanboard_api import call_api
from db.queries import find_task_with_project, find_tasks_by_title


def test_created_task_is_saved_in_database(
    api_session,
    db_connection,
    created_project,
):
    # Arrange
    project_id = created_project["id"]
    task_title = "Check API persistence"

    # Act
    task_id = call_api(
        api_session,
        "createTask",
        {
            "title": task_title,
            "project_id": project_id,
        },
    )

    # Assert
    assert type(task_id) is int and task_id > 0, (
        f"Unexpected createTask result: {task_id!r}"
    )

    with db_connection:
        task_row = find_task_with_project(db_connection, task_id)

    assert task_row is not None, (
        f"Task {task_id} was not found in PostgreSQL"
    )
    assert task_row == (
        task_id,
        task_title,
        project_id,
        created_project["name"],
    )

def test_two_tasks_with_identical_titles_have_different_ids(
    api_session,
    db_connection,
    created_project,
):
    project_id = created_project["id"]
    task_title = "The identical title"

    first_task_id = call_api(
        api_session,
        "createTask",
        {
            "title": task_title,
            "project_id": project_id
        }
    )
    assert type(first_task_id) is int and first_task_id > 0, (
        f"Unexpected createTask result: {first_task_id!r}"
    )

    second_task_id = call_api(
        api_session,
        "createTask",
        {
            "title": task_title,
            "project_id": project_id
        }
    )
    assert type(second_task_id) is int and second_task_id > 0, (
        f"Unexpected createTask result: {second_task_id!r}"
    )
    assert first_task_id != second_task_id
    with db_connection:
        found_tasks_rows = find_tasks_by_title(
            db_connection,
            project_id,
            task_title
        )
    expected_rows = sorted([
        (first_task_id, task_title),
        (second_task_id, task_title),
    ])
    assert found_tasks_rows == expected_rows