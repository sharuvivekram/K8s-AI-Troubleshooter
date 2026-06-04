"""Detect pods in an unhealthy state across the watched namespaces."""
from __future__ import annotations

from kubernetes import client

# Container waiting/terminated reasons we treat as incidents.
BAD_REASONS = {
    "CrashLoopBackOff", "Error", "ImagePullBackOff", "ErrImagePull",
    "CreateContainerConfigError", "OOMKilled", "RunContainerError",
}


def find_unhealthy_pods(core: client.CoreV1Api, namespaces: list[str]) -> list[dict]:
    """Return a list of incident dicts for pods that look broken."""
    incidents = []
    for ns in namespaces:
        pods = core.list_namespaced_pod(namespace=ns).items
        for pod in pods:
            issue = _diagnose(pod)
            if issue:
                incidents.append(issue)
    return incidents


def _diagnose(pod) -> dict | None:
    name = pod.metadata.name
    ns = pod.metadata.namespace
    phase = pod.status.phase
    statuses = pod.status.container_statuses or []

    reason = None
    restart_count = 0
    for cs in statuses:
        restart_count = max(restart_count, cs.restart_count or 0)
        waiting = cs.state.waiting if cs.state else None
        terminated = cs.state.terminated if cs.state else None
        last = cs.last_state.terminated if cs.last_state else None
        if waiting and waiting.reason in BAD_REASONS:
            reason = waiting.reason
        elif terminated and terminated.reason in BAD_REASONS:
            reason = terminated.reason
        elif last and last.reason in BAD_REASONS:
            reason = last.reason

    # Also flag pods stuck Pending or with excessive restarts.
    if reason is None and phase == "Pending":
        reason = "Pending"
    if reason is None and restart_count >= 5:
        reason = "HighRestartCount"

    if reason is None:
        return None

    # A stable key so we only alert once per (pod, reason, restart-bucket).
    key = f"{ns}/{name}:{reason}:{restart_count}"
    return {
        "key": key,
        "namespace": ns,
        "pod": name,
        "reason": reason,
        "phase": phase,
        "restart_count": restart_count,
        "container": statuses[0].name if statuses else None,
    }
