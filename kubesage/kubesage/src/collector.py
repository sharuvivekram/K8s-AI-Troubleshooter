"""Gather the context an engineer would look at: events, logs, pod status."""
from __future__ import annotations

from kubernetes import client
from . import config


def collect(core: client.CoreV1Api, incident: dict) -> dict:
    """Enrich an incident with events and recent logs."""
    ns, pod = incident["namespace"], incident["pod"]
    return {
        **incident,
        "events": _events(core, ns, pod),
        "logs": _logs(core, ns, pod, incident.get("container")),
    }


def _events(core, ns: str, pod: str) -> list[str]:
    try:
        field = f"involvedObject.name={pod}"
        evs = core.list_namespaced_event(namespace=ns, field_selector=field).items
        evs = sorted(evs, key=lambda e: e.last_timestamp or e.event_time or 0)
        return [f"{e.type}/{e.reason}: {e.message}" for e in evs[-12:]]
    except Exception as e:  # noqa: BLE001
        return [f"(could not fetch events: {e})"]


def _logs(core, ns: str, pod: str, container: str | None) -> str:
    # Try current logs, then previous (crashed) container logs.
    for previous in (False, True):
        try:
            return core.read_namespaced_pod_log(
                name=pod, namespace=ns, container=container,
                tail_lines=config.LOG_TAIL_LINES, previous=previous,
            )
        except Exception:  # noqa: BLE001
            continue
    return "(no logs available)"
