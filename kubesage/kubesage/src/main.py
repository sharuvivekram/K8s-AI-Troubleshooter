"""KubeSage entry point.

Loads kube config (in-cluster when deployed, local kubeconfig otherwise),
then repeatedly: find unhealthy pods -> collect diagnostics -> analyze with
Claude -> notify. Already-seen incidents are skipped.
"""
from __future__ import annotations

import time
from kubernetes import client, config as kube_config

from . import analyzer, collector, config, metrics, notifier, watcher


def _load_kube():
    try:
        kube_config.load_incluster_config()
        print("Loaded in-cluster config.")
    except kube_config.ConfigException:
        kube_config.load_kube_config()
        print("Loaded local kubeconfig.")


def run_once(core, seen: set[str]) -> None:
    incidents = watcher.find_unhealthy_pods(core, config.NAMESPACES)
    new = [i for i in incidents if i["key"] not in seen]
    print(f"Found {len(incidents)} unhealthy pod(s), {len(new)} new.")
    for inc in new:
        metrics.incidents_total.labels(reason=inc["reason"]).inc()
        try:
            enriched = collector.collect(core, inc)
            rca = analyzer.analyze(enriched)
        except Exception as e:  # noqa: BLE001
            metrics.errors_total.inc()
            print(f"[analyze] failed for {inc['pod']}: {e}")
            seen.add(inc["key"])
            continue
        metrics.analyses_total.labels(
            severity=rca["severity"], provider=config.AI_PROVIDER
        ).inc()
        notifier.notify(enriched, rca)
        seen.add(inc["key"])


def main() -> None:
    _load_kube()
    core = client.CoreV1Api()
    seen: set[str] = set()
    print(f"Watching namespaces {config.NAMESPACES} via {config.AI_PROVIDER}.")
    if not config.RUN_ONCE:
        metrics.serve(config.METRICS_PORT)
    while True:
        try:
            run_once(core, seen)
        except Exception as e:  # noqa: BLE001
            print(f"[loop] error: {e}")
        if config.RUN_ONCE:
            break
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
