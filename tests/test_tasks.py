import allure

from clients.kanboard_api import call_api
from db.queries import find_task_with_project, find_tasks_by_title

@allure.feature("Tasks API")
@allure.story("Task persistence")
@allure.title("Created task is stored in PostgreSQL")
def test_created_task_is_saved_in_database(
    task_service,
    db_connection,
    created_project,
):
    # Arrange
    project_id = created_project["id"]
    task_title = "Check API persistence"

    # Act
    task_id = task_service.create_task(project_id, task_title)

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

@allure.feature("Tasks API")
@allure.story("Identical tasks")
@allure.title("Tasks with identical titles have different IDs")
def test_two_tasks_with_identical_titles_have_different_ids(
    task_service,
    db_connection,
    created_project,
):
    project_id = created_project["id"]
    task_title = "The identical title"

    first_task_id = task_service.create_task(project_id, task_title)
    assert type(first_task_id) is int and first_task_id > 0, (
        f"Unexpected createTask result: {first_task_id!r}"
    )

    second_task_id = task_service.create_task(project_id, task_title)
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

@allure.feature("Tasks API")
@allure.story("Renaming task")
@allure.title("Renamed task is updated in database")
def test_renamed_task_is_updated_in_database(
    task_service,
    db_connection,
    created_project
):
    project_id = created_project["id"]
    task_title = "Rename title task"

    task_id = task_service.create_task(project_id, task_title)
    assert type(task_id) is int and task_id > 0, (
        f"Unexpected createTask result: {task_id!r}"
    )
    new_title = "New title of rename title task"
    renamed = task_service.rename_task(task_id, new_title)
    assert renamed is True, (
        f"Failed to rename task {task_id!r}"
    )

    with db_connection:
        task_row = find_task_with_project(db_connection, task_id)
    assert task_row is not None, (
        f"Task {task_id} was not found in PostgreSQL"
    )
    assert task_row == (
        task_id,
        new_title,
        project_id,
        created_project["name"],
    )
