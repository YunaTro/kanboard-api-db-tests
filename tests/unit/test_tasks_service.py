import pytest
from requests.exceptions import ConnectionError, Timeout

from services.tasks_service import TasksService

def test_get_task_returns_wrapper_result(mocker):
    expected_result = {
        "id": "17",
        "title": "Check persistence",
        "project_id": "5"
    }
    mocked_call = mocker.patch(
        "services.tasks_service.call_api",
        autospec=True,
        return_value=expected_result
    )
    session = mocker.sentinel.session
    service = TasksService(session)

    task = service.get_task(task_id=17)
    assert task == expected_result
    assert mocked_call.call_count == 1
    mocked_call.assert_called_with(
        session,
        "getTask",
        {"task_id": 17}
    )


def test_create_task_returns_created_id(mocker):
    mocked_call = mocker.patch(
        "services.tasks_service.call_api",
        autospec=True,
        return_value=42
    )

    session = mocker.sentinel.session
    service = TasksService(session)
    task_id = service.create_task(project_id=5, task_title="Check persistence")
    assert task_id == 42
    assert mocked_call.call_count == 1
    mocked_call.assert_called_with(
        session,
        "createTask",
        {
            "project_id": 5,
            "title": "Check persistence"
        }
    )

def test_get_task_returns_none_when_not_found(mocker):
    mocked_call = mocker.patch(
        "services.tasks_service.call_api",
        autospec=True,
        return_value=None
    )

    session = mocker.sentinel.session
    service = TasksService(session)
    result = service.get_task(task_id=999999)
    assert result is None
    mocked_call.assert_called_once_with(
        session,
        "getTask",
        {"task_id": 999999}
    )

def test_two_mock_calls_execute_correctly(mocker):
    mocked_call = mocker.patch(
        "services.tasks_service.call_api",
        autospec=True,
        return_value=None
    )

    session = mocker.sentinel.session
    service = TasksService(session)
    service.get_task(task_id=17)
    service.get_task(task_id=25)
    assert mocked_call.call_count == 2
    assert mocked_call.call_args_list == [
        mocker.call(session, "getTask", {"task_id": 17}),
        mocker.call(session, "getTask", {"task_id": 25}),
    ]  

@pytest.mark.parametrize(
    "error, message",
    [
        pytest.param(Timeout, "Request timed out", id="timeout"),
        pytest.param(ConnectionError, "Connection error", id="connection_error")
    ]
)
def test_get_task_propagates_transport_errors(mocker, error, message):
    error_with_message = error(message)
    mocked_call = mocker.patch(
        "services.tasks_service.call_api",
        autospec=True,
        side_effect=error_with_message,
    )

    session = mocker.sentinel.session
    service = TasksService(session)

    with pytest.raises(error, match=message) as exc_info:
        service.get_task(17)

    assert exc_info.value is error_with_message
    mocked_call.assert_called_once_with(
        session,
        "getTask",
        {"task_id": 17}
    )
