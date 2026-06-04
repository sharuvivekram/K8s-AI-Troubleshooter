# Monitoring KubeSage with Prometheus + Grafana

KubeSage exposes Prometheus metrics on `:8000/metrics` (continuous mode only).

## Metrics

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `kubesage_incidents_total` | counter | `reason` | unhealthy pods detected |
| `kubesage_analyses_total` | counter | `severity`, `provider` | AI analyses produced |
| `kubesage_errors_total` | counter | — | analysis failures |

## Scraping

- Annotation-based Prometheus: apply `deploy/service.yaml` — the
  `prometheus.io/scrape` annotations are picked up automatically.
- Prometheus Operator: create a `ServiceMonitor` selecting `app: kubesage`
  on the `metrics` port.

Verify locally:
```bash
kubectl port-forward deployment/kubesage 8000:8000
curl localhost:8000/metrics | grep kubesage_
```

## Grafana panels (PromQL)

- Incidents per hour by reason:
  `sum by (reason) (increase(kubesage_incidents_total[1h]))`
- Severity breakdown:
  `sum by (severity) (kubesage_analyses_total)`
- Error rate:
  `rate(kubesage_errors_total[5m])`

Add these as a Time series and two Stat/Pie panels in a new Grafana dashboard.
