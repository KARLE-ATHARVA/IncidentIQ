import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class IncidentIQClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    def request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
    ):
        headers = {
            "Content-Type": "application/json",
        }

        if self.token:
            headers["Authorization"] = (
                f"Bearer {self.token}"
            )

        data = None

        if body is not None:
            data = json.dumps(body).encode("utf-8")

        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urlopen(request) as response:
                response_body = (
                    response.read()
                    .decode("utf-8")
                )

                if response_body:
                    return (
                        response.status,
                        json.loads(response_body),
                    )

                return response.status, None

        except HTTPError as exc:
            error_body = (
                exc.read()
                .decode("utf-8")
            )

            raise RuntimeError(
                f"IncidentIQ API error "
                f"{exc.code}: {error_body}"
            ) from exc

        except URLError as exc:
            raise RuntimeError(
                "Unable to connect to IncidentIQ "
                f"at {self.base_url}"
            ) from exc

    def login(
        self,
        email: str,
        password: str,
    ) -> str:
        status, data = self.request(
            "POST",
            "/api/auth/login",
            {
                "email": email,
                "password": password,
            },
        )

        if status != 200:
            raise RuntimeError(
                "IncidentIQ authentication failed."
            )

        self.token = data["access_token"]

        return self.token

    def create_metric(
        self,
        project_id: str,
        service_id: str,
        timestamp: str,
        name: str,
        value: float,
    ):
        _, data = self.request(
            "POST",
            (
                f"/api/projects/{project_id}"
                f"/services/{service_id}"
                f"/metrics"
            ),
            {
                "timestamp": timestamp,
                "name": name,
                "value": value,
            },
        )

        return data

    def create_log(
        self,
        project_id: str,
        service_id: str,
        timestamp: str,
        level: str,
        message: str,
    ):
        _, data = self.request(
            "POST",
            (
                f"/api/projects/{project_id}"
                f"/services/{service_id}"
                f"/logs"
            ),
            {
                "timestamp": timestamp,
                "level": level,
                "message": message,
            },
        )

        return data

    def create_deployment(
        self,
        project_id: str,
        service_id: str,
        timestamp: str,
        version: str,
        description: str,
    ):
        _, data = self.request(
            "POST",
            (
                f"/api/projects/{project_id}"
                f"/services/{service_id}"
                f"/deployments"
            ),
            {
                "timestamp": timestamp,
                "version": version,
                "description": description,
            },
        )

        return data

    def process_incident(
        self,
        project_id: str,
        service_id: str,
        metric_event_id: str,
    ):
        _, data = self.request(
            "POST",
            (
                f"/api/projects/{project_id}"
                f"/services/{service_id}"
                f"/metrics/{metric_event_id}"
                f"/process-incident"
            ),
        )

        return data