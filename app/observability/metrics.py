import os
import json
import time
import threading
from prometheus_client import Counter, Histogram, Gauge, REGISTRY

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency (seconds)",
    ["method", "path", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

HTTP_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "In-progress HTTP requests",
    ["method", "path"],
)

BUSINESS_NEWS_CREATED_TOTAL = Counter(
    "business_news_created_total",
    "Number of created news",
)

BUSINESS_USERS_REGISTERED_TOTAL = Counter(
    "business_users_registered_total",
    "Number of registered users",
)

NEWS_NOTIFICATIONS_TOTAL = Counter(
    "news_notifications_total",
    "News notifications sent",
    ["channel", "status"],
)

METRICS_JSONL = os.getenv("METRICS_JSONL", "metrics/metrics.jsonl")
METRICS_DUMP_INTERVAL_SEC = int(os.getenv("METRICS_DUMP_INTERVAL_SEC", "10"))


def _collect_registry_snapshot() -> list[dict]:
    out = []
    for metric in REGISTRY.collect():
        for s in metric.samples:
            out.append(
                {
                    "ts": time.time(),
                    "name": s.name,
                    "labels": dict(s.labels),
                    "value": s.value,
                }
            )
    return out


def start_metrics_json_dumper() -> None:
    os.makedirs(os.path.dirname(METRICS_JSONL), exist_ok=True)

    def loop():
        while True:
            snap = _collect_registry_snapshot()
            with open(METRICS_JSONL, "a", encoding="utf-8") as f:
                for row in snap:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            time.sleep(METRICS_DUMP_INTERVAL_SEC)

    threading.Thread(target=loop, daemon=True).start()
