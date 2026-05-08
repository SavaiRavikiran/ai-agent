# Nginx 502 Bad Gateway

**Component:** Ingress / Nginx  
**Doc type:** Runbook

## Symptoms

- Users see 502 Bad Gateway from Nginx/Ingress
- Upstream backend unreachable

## Upstream check

1. Identify upstream from Nginx/Ingress config (service name and port).
2. Check service endpoints: `kubectl get endpoints <service> -n <namespace>`
3. If no endpoints, no ready pods are behind the service.

## Pod readiness

1. List pods for the backend: `kubectl get pods -n <namespace> -l app=<app>`
2. Check readiness probe: `kubectl describe pod <pod> -n <namespace>` — look for `Readiness: false` and events.
3. Check pod logs: `kubectl logs <pod> -n <namespace>` for application errors.
4. If pods are CrashLoopBackOff or not ready, follow runbook for Pod CrashLoopBackOff or High Memory.

## Config validation

- Test Nginx config: `nginx -t` (on node or sidecar).
- Reload Nginx: `nginx -s reload` (only after config test passes).

## Verification

- Curl backend service from within cluster: `kubectl run curl --rm -it --image=curlimages/curl -- curl -s -o /dev/null -w "%{http_code}" http://<service>.<namespace>.svc.cluster.local:<port>/`
- Check Ingress/Prometheus for 5xx rate drop.
