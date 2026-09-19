import json
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"

EMAIL = "atharva@example.com"
PASSWORD = "secret123"

PROJECT_ID = "e6a19a93-f967-4553-b94f-c173918f08a8"
SERVICE_ID = "d6e264c2-1270-49dc-a9e0-e7899dc44f31"


def request(
    method: str,
    path: str,
    body: dict | None = None,
    token: str | None = None,
):
    headers = {
        "Content-Type": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None

    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(req) as response:
            response_body = response.read().decode("utf-8")

            if response_body:
                return response.status, json.loads(response_body)

            return response.status, None

    except HTTPError as exc:
        error_body = exc.read().decode("utf-8")

        print()
        print("========================================")
        print("API ERROR")
        print("========================================")
        print(f"Method: {method}")
        print(f"Path:   {path}")
        print(f"Status: {exc.code}")
        print(f"Body:   {error_body}")
        print()

        raise


def login() -> str:
    print("Logging in...")

    status, data = request(
        "POST",
        "/api/auth/login",
        {
            "email": EMAIL,
            "password": PASSWORD,
        },
    )

    if status != 200:
        raise RuntimeError("Login failed.")

    print("✓ Login successful")

    return data["access_token"]


def create_metric(
    token: str,
    timestamp: datetime,
    value: float,
):
    status, data = request(
        "POST",
        f"/api/projects/{PROJECT_ID}"
        f"/services/{SERVICE_ID}/metrics",
        {
            "timestamp": timestamp.isoformat(),
            "name": "checkout_latency",
            "value": value,
        },
        token,
    )

    if status not in (200, 201):
        raise RuntimeError("Metric creation failed.")

    return data


def create_log(
    token: str,
    timestamp: datetime,
):
    status, data = request(
        "POST",
        f"/api/projects/{PROJECT_ID}"
        f"/services/{SERVICE_ID}/logs",
        {
            "timestamp": timestamp.isoformat(),
            "level": "ERROR",
            "message": (
                "Checkout requests are timing out "
                "while calling payment service."
            ),
        },
        token,
    )

    if status not in (200, 201):
        raise RuntimeError("Log creation failed.")

    return data


def create_deployment(
    token: str,
    timestamp: datetime,
):
    status, data = request(
        "POST",
        f"/api/projects/{PROJECT_ID}"
        f"/services/{SERVICE_ID}/deployments",
        {
            "timestamp": timestamp.isoformat(),
            "version": "v2.4.0",
            "description": (
                "Deployed checkout payment integration changes."
            ),
        },
        token,
    )

    if status not in (200, 201):
        raise RuntimeError("Deployment creation failed.")

    return data


def process_incident(
    token: str,
    metric_event_id: str,
):
    status, data = request(
        "POST",
        f"/api/projects/{PROJECT_ID}"
        f"/services/{SERVICE_ID}"
        f"/metrics/{metric_event_id}/process-incident",
        token=token,
    )

    if status != 200:
        raise RuntimeError("Incident processing failed.")

    return data


def main():
    print()
    print("========================================")
    print("IncidentIQ E2E Incident Seeder")
    print("========================================")
    print(f"Project: {PROJECT_ID}")
    print(f"Service: {SERVICE_ID}")
    print()

    token = login()

    now = datetime.now(timezone.utc)

    # --------------------------------------------------
    # 1. Historical normal metrics
    # --------------------------------------------------

    normal_values = [
        100,
        101,
        99,
        100,
        102,
        98,
        101,
        100,
        99,
        100,
        101,
        100,
        98,
        102,
        100,
        99,
        101,
        100,
        102,
        99,
    ]

    print()
    print("Creating 20 historical normal metrics...")

    for index, value in enumerate(normal_values):
        timestamp = now - timedelta(
            minutes=26 - index
        )

        create_metric(
            token=token,
            timestamp=timestamp,
            value=value,
        )

    print("✓ 20 historical metrics created")

    # --------------------------------------------------
    # 2. Recent anomalous metrics
    # --------------------------------------------------

    anomaly_values = [
        160,
        165,
        162,
        168,
        170,
    ]

    print()
    print("Creating 5 recent anomalous metrics...")

    for index, value in enumerate(anomaly_values):
        timestamp = now - timedelta(
            minutes=6 - index
        )

        create_metric(
            token=token,
            timestamp=timestamp,
            value=value,
        )

    print("✓ 5 recent anomalous metrics created")

    # --------------------------------------------------
    # 3. Current anomalous metric
    # --------------------------------------------------

    print()
    print("Creating current anomalous metric...")

    current_metric = create_metric(
        token=token,
        timestamp=now,
        value=175,
    )

    current_metric_id = current_metric["id"]

    print("✓ Current metric created")
    print(f"  Metric ID: {current_metric_id}")

    # --------------------------------------------------
    # 4. Correlated ERROR log
    # --------------------------------------------------

    print()
    print("Creating correlated ERROR log...")

    log_event = create_log(
        token=token,
        timestamp=now - timedelta(seconds=30),
    )

    print("✓ ERROR log created")
    print(f"  Log ID: {log_event['id']}")

    # --------------------------------------------------
    # 5. Correlated deployment
    # --------------------------------------------------

    print()
    print("Creating correlated deployment...")

    deployment_event = create_deployment(
        token=token,
        timestamp=now - timedelta(minutes=2),
    )

    print("✓ Deployment created")
    print(
        f"  Deployment ID: "
        f"{deployment_event['id']}"
    )

    # --------------------------------------------------
    # 6. Run IncidentIQ incident pipeline
    # --------------------------------------------------

    print()
    print("Running IncidentIQ incident pipeline...")

    incident_result = process_incident(
        token=token,
        metric_event_id=current_metric_id,
    )

    print()
    print("========================================")
    print("INCIDENT PIPELINE RESULT")
    print("========================================")

    print(
        json.dumps(
            incident_result,
            indent=2,
        )
    )

    # --------------------------------------------------
    # 7. Final result
    # --------------------------------------------------

    print()

    if incident_result.get("incident_created"):
        print("✓ REAL INCIDENT CREATED")
        print(
            f"  Incident ID: "
            f"{incident_result['incident_id']}"
        )
        print(
            f"  Severity: "
            f"{incident_result['severity']}"
        )
        print(
            f"  Status: "
            f"{incident_result['status']}"
        )
        print(
            f"  Title: "
            f"{incident_result['title']}"
        )

    else:
        print("⚠ NO INCIDENT WAS CREATED")
        print()
        print(
            "The telemetry was created successfully, "
            "but the detection/correlation pipeline "
            "did not produce an incident."
        )


if __name__ == "__main__":
    main()