import sys

from simulator.client import IncidentIQClient
from simulator.config import SimulatorConfig
from simulator.scenarios import run_bad_deployment


def main():
    scenario = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "bad-deployment"
    )

    config = SimulatorConfig()

    client = IncidentIQClient(
        base_url=config.base_url,
    )

    print()
    print("Connecting to IncidentIQ...")

    client.login(
        email=config.email,
        password=config.password,
    )

    print("✓ Connected to IncidentIQ")

    if scenario == "bad-deployment":
        run_bad_deployment(
            client=client,
            config=config,
        )
        return

    raise SystemExit(
        f"Unknown scenario: {scenario}"
    )


if __name__ == "__main__":
    main()