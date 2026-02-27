from prometheus_client import Histogram, Counter

Request_Count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ['method', 'endpoint', 'service']
)

Request_Latency = Histogram(
    "http_request_duration_seconds",
    "HTTP Request latency,"
    ["method", "endpoint", "service"]
)