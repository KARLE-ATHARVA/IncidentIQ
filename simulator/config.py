from dataclasses import dataclass


@dataclass(frozen=True)
class SimulatorConfig:
    base_url: str = "http://127.0.0.1:8000"

    email: str = "atharva@example.com"
    password: str = "secret123"

    project_id: str = (
        "e6a19a93-f967-4553-b94f-c173918f08a8"
    )

    service_id: str = (
        "d6e264c2-1270-49dc-a9e0-e7899dc44f31"
    )

    metric_name: str = "checkout_latency"

    normal_latency: float = 100.0
    degraded_latency: float = 175.0

    deployment_version: str = "v2.4.0"