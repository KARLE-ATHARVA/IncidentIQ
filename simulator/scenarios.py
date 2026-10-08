from datetime import datetime, timedelta, timezone

from simulator.client import IncidentIQClient
from simulator.config import SimulatorConfig


def run_bad_deployment(
    client: IncidentIQClient,
    config: SimulatorConfig,
):
    now = datetime.now(timezone.utc)

    print()
    print("========================================")
    print("IncidentIQ Production Simulator")
    print("Scenario: BAD DEPLOYMENT")
    print("========================================")
    print()

    print("1. Generating normal checkout telemetry...")

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

    for index, value in enumerate(normal_values):
        timestamp = (
            now - timedelta(minutes=26 - index)
        )

        client.create_metric(
            project_id=config.project_id,
            service_id=config.service_id,
            timestamp=timestamp.isoformat(),
            name=config.metric_name,
            value=value,
        )

    print(
        "   ✓ Normal checkout traffic established"
    )

    deployment_time = (
        now - timedelta(minutes=2)
    )

    print()
    print(
        "2. Deploying checkout-service "
        f"{config.deployment_version}..."
    )

    client.create_deployment(
        project_id=config.project_id,
        service_id=config.service_id,
        timestamp=deployment_time.isoformat(),
        version=config.deployment_version,
        description=(
            "Deployed checkout payment "
            "integration changes."
        ),
    )

    print("   ✓ Deployment event recorded")

    print()
    print(
        "3. Injecting production degradation..."
    )

    anomaly_values = [
        160,
        165,
        162,
        168,
        170,
    ]

    for index, value in enumerate(anomaly_values):
        timestamp = (
            now - timedelta(minutes=6 - index)
        )

        client.create_metric(
            project_id=config.project_id,
            service_id=config.service_id,
            timestamp=timestamp.isoformat(),
            name=config.metric_name,
            value=value,
        )

    current_metric = client.create_metric(
        project_id=config.project_id,
        service_id=config.service_id,
        timestamp=now.isoformat(),
        name=config.metric_name,
        value=config.degraded_latency,
    )

    print(
        "   ✓ Checkout latency increased "
        f"to {config.degraded_latency}ms"
    )

    print()
    print(
        "4. Generating correlated payment "
        "service failure..."
    )

    client.create_log(
        project_id=config.project_id,
        service_id=config.service_id,
        timestamp=(
            now - timedelta(seconds=30)
        ).isoformat(),
        level="ERROR",
        message=(
            "Checkout requests are timing out "
            "while calling payment service."
        ),
    )

    print(
        "   ✓ Payment timeout error recorded"
    )

    print()
    print(
        "5. Running existing IncidentIQ "
        "incident pipeline..."
    )

    incident_result = client.process_incident(
        project_id=config.project_id,
        service_id=config.service_id,
        metric_event_id=current_metric["id"],
    )

    print()
    print("========================================")
    print("INCIDENTIQ RESULT")
    print("========================================")

    if incident_result.get("incident_created"):
        print("✓ INCIDENT DETECTED")
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
        print(
            "⚠ No qualifying incident was created."
        )

    return incident_result