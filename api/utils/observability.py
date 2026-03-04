"""Lightweight in-process observability helpers."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock

_METRIC_DEFINITIONS: dict[str, str] = {
    "flow_auth_current_user_resolution_failures_total": (
        "Current-user resolution failures by reason."
    ),
    "flow_auth_denied_by_rls_total": ("Observable auth/RLS denials by endpoint and status code."),
    "flow_auth_identity_header_parse_failures_total": (
        "Identity header parse failures by auth mode."
    ),
}

_metrics_lock = Lock()
_metrics: dict[tuple[str, tuple[tuple[str, str], ...]], int] = defaultdict(int)


def increment_counter(metric_name: str, **labels: str) -> None:
    key = (metric_name, tuple(sorted((name, str(value)) for name, value in labels.items())))
    with _metrics_lock:
        _metrics[key] += 1


def render_prometheus_text() -> str:
    lines: list[str] = []
    with _metrics_lock:
        items = sorted(_metrics.items())

    for metric_name, description in _METRIC_DEFINITIONS.items():
        lines.append(f"# HELP {metric_name} {description}")
        lines.append(f"# TYPE {metric_name} counter")

    for (metric_name, labels), value in items:
        label_text = ""
        if labels:
            label_text = "{" + ",".join(f'{name}="{value}"' for name, value in labels) + "}"
        lines.append(f"{metric_name}{label_text} {value}")

    return "\n".join(lines) + ("\n" if lines else "")


def reset_metrics() -> None:
    with _metrics_lock:
        _metrics.clear()
