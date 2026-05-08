# High Memory Usage — d2, cs, dsearch

**Apps:** d2, cs, dsearch  
**Doc type:** Runbook

## Thresholds

- **Warning:** Working set > 80% of limit
- **Critical:** Working set at limit or OOMKilled

## Investigation steps

1. Query Prometheus: `container_memory_working_set_bytes{namespace="production",pod=~"d2.+|cs.+|dsearch.+"}`
2. Check pod restarts: `increase(kube_pod_container_status_restarts_total[1h])`
3. Review EFK logs for `OutOfMemoryError` or `java.lang.OutOfMemoryError`

## Fix procedures

### When to scale vs restart vs tune JVM

- **Scale up replicas** — If total load is high and per-pod memory is near limit; stay within max replicas (e.g. 20).
- **Restart** — If single pod is stuck with high memory and others are fine; use rolling restart to clear leak.
- **Tune JVM** — For Java apps (d2, cs, dsearch): adjust `-Xmx` / `-Xms` via ConfigMap or deployment env; then rolling restart.

### Steps

1. Get deployment status: `kubectl get deployment <name> -n production`
2. Scaling: `kubectl scale deployment <name> --replicas=<n> -n production` (max 20)
3. Restart: `kubectl rollout restart deployment <name> -n production`
4. Verify: wait 2–5 minutes and re-check memory metrics and restarts.

## PromQL

- Memory: `sum(container_memory_working_set_bytes{namespace="production",pod=~"<app>.+"}) by (pod)`
- Restarts: `sum(increase(kube_pod_container_status_restarts_total[1h])) by (pod)`
