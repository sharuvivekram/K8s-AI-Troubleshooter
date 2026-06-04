"""Prometheus metrics. Scraped from an HTTP endpoint (default :8000/metrics)."""
from prometheus_client import Counter, start_http_server

incidents_total = Counter(
    "kubesage_incidents_total", "Unhealthy pods detected", ["reason"]
)
analyses_total = Counter(
    "kubesage_analyses_total", "AI analyses produced", ["severity", "provider"]
)
errors_total = Counter(
    "kubesage_errors_total", "Errors during analysis"
)


def serve(port: int) -> None:
    start_http_server(port)
    print(f"Metrics exposed on :{port}/metrics")
