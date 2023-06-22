# Configuration for the Celery instance
broker_url = (
    "redis://localhost:6379/0"  # The URL of the message broker (Redis in this case)
)
result_backend = (
    "redis://localhost:6379/0"  # Optional: Using Redis to store task results
)
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "UTC"
enable_utc = True