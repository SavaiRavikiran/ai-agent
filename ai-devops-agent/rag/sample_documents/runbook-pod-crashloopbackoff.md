# Resolving Pod CrashLoopBackOff

**App:** All  
**Doc type:** Runbook

## Symptoms

- Pod status shows `CrashLoopBackOff`
- `kubectl get pods` shows high restart count
- Application not serving traffic

## Root causes

1. **OOMKilled** — Container exceeded memory limit; check `lastState.terminated.reason` in pod describe.
2. **Config error** — Wrong env, missing ConfigMap/Secret, or invalid args.
3. **Startup probe failure** — App takes longer than `initialDelaySeconds + failureThreshold * periodSeconds` to become ready.

## Step-by-step resolution

### 1. Inspect pod and events

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

Look for `OOMKilled`, `Error`, or `Failed` in container state.

### 2. If OOMKilled

- Check current memory limits: `kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].resources}'`
- Increase `resources.limits.memory` in deployment (e.g. 512Mi → 1Gi) or scale replicas and redistribute load.
- Optionally run Ansible playbook `tune-jvm.yml` for Java apps (d2, cs, dsearch) to reduce heap if applicable.

### 3. If config/startup error

- Check logs from previous container: `kubectl logs <pod> -n <ns> --previous`
- Fix ConfigMap/Secret or deployment env; then rolling restart: `kubectl rollout restart deployment/<name> -n <ns>`

### 4. Verification

- Wait for rollout: `kubectl rollout status deployment/<name> -n <ns>`
- Check pod status: `kubectl get pods -n <ns> -l app=<app>`
- PromQL to confirm no new restarts: `increase(kube_pod_container_status_restarts_total{namespace="<ns>"}[1h]) == 0`

## PromQL queries to check

- Restarts: `increase(kube_pod_container_status_restarts_total{namespace="<namespace>",pod=~"<app>.+"}[1h])`
- Ready vs desired: `kube_deployment_status_replicas_ready{deployment="<name>"}`

## Ansible playbook

If approved, use `restart-deployment.yml` with `check_mode: true` first, then run without check to apply.
