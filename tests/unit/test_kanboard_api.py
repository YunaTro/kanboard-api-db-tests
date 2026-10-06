import pytest
import requests
from requests.exceptions import Timeout

from clients.kanboard_api import call_api

def test_call_api_rejects_http_500(mocker, monkeypatch):
    monkeypatch.setenv(
        "API_URL",
        "https://kanboard.example/jsonrpc.php",
    )
    response = mocker.Mock(spec=requests.Response)
    response.status_code = 500
    response.text = "Internal Server Error"

    with requests.Session() as session:
        mocked_post = mocker.patch.object(
            session,
            "post",
            autospec=True,
            return_value=response,
        )

        with pytest.raises(AssertionError, match="Internal Server Error"):
            call_api(session, "getTask", {"task_id": 17})

        mocked_post.assert_called_once()
        response.json.assert_not_called() 

def test_call_api_returns_result_on_success(mocker, monkeypatch):
    monkeypatch.setenv(
        "API_URL",
        "https://kanboard.example/jsonrpc.php",
    )
    expected_task = {
        "id": "17",
        "title": "Check persistence",
        "project_id": "5",
    }
    mocked_uuid = mocker.patch(
        "clients.kanboard_api.uuid4",
        autospec=True,
    )
    mocked_uuid.return_value.hex = "test-request-id"

    response = mocker.Mock(spec=requests.Response)
    response.status_code = 200
    response.json.return_value = {
        "jsonrpc": "2.0",
        "id": "test-request-id",
        "result": expected_task,
    }

    with requests.Session() as session:
        mocked_post = mocker.patch.object(
            session,
            "post",
            autospec=True,
            return_value=response
        )

        got_task = call_api(session, "getTask", {"task_id": 17})
        assert got_task == expected_task
    mocked_post.assert_called_once_with(
        "https://kanboard.example/jsonrpc.php",
        json={
            "jsonrpc": "2.0",
            "method": "getTask",
            "params": {"task_id": 17},
            "id": "test-request-id",
        },
        timeout=(3, 15),
    )
    response.json.assert_called_once()

def test_call_api_propagates_timeout(mocker, monkeypatch):
    error = Timeout("Request timed out")
    monkeypatch.setenv(
        "API_URL",
        "https://kanboard.example/jsonrpc.php",
    )
    with requests.Session() as session:
        mocked_post = mocker.patch.object(
            session,
            "post",
            autospec=True,
            side_effect=error,
        )

        with pytest.raises(Timeout, match="Request timed out") as exc_info:
            call_api(session, "getTask", {"task_id": 17})
        assert exc_info.value is error
        mocked_post.assert_called_once()
