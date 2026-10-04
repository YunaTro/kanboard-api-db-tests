import os
import time

import requests


def main():
    deadline = time.monotonic() + 90
    last_problem = "No request has been made"

    with requests.Session() as session:
        session.auth = (
            os.environ["API_USERNAME"],
            os.environ["API_TOKEN"],
        )

        while time.monotonic() < deadline:
            try:
                response = session.post(
                    os.environ["API_URL"],
                    json={
                        "jsonrpc": "2.0",
                        "method": "getVersion",
                        "params": {},
                        "id": "readiness",
                    },
                    timeout=(3, 5),
                )
            except requests.RequestException as error:
                last_problem = type(error).__name__
            else:
                if response.status_code in (401, 403):
                    raise RuntimeError(
                        "API authentication failed. Check CI token configuration."
                    )

                if response.status_code == 200:
                    try:
                        body = response.json()
                    except requests.exceptions.JSONDecodeError:
                        last_problem = "API returned invalid JSON"
                    else:
                        if (
                            isinstance(body, dict)
                            and body.get("jsonrpc") == "2.0"
                            and body.get("id") == "readiness"
                            and "error" not in body
                            and isinstance(body.get("result"), str)
                            and body["result"]
                        ):
                            print("Kanboard API is ready")
                            return

                        last_problem = "Unexpected JSON-RPC response"
                else:
                    last_problem = f"HTTP {response.status_code}"

            time.sleep(2)

    raise RuntimeError(
        f"Kanboard API did not become ready: {last_problem}"
    )


if __name__ == "__main__":
    main()