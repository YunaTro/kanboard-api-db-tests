import os
from uuid import uuid4


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