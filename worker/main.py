import json

if __package__:
    from .redis_queue import QUEUE_NAME, redis_client
else:
    # Support direct execution from this directory: `python main.py`.
    from redis_queue import QUEUE_NAME, redis_client


def main():
    print("IncidentIQ worker started")

    while True:
        _, raw_job = redis_client.blpop(QUEUE_NAME)

        job = json.loads(raw_job)

        print(f"Worker received job: {job}")


if __name__ == "__main__":
    main()
