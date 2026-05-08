# Past Incident: INC0001234

**App:** d2  
**Resolution:** Resolved by AI Agent (example)

## Description

P2 incident: d2 pods in CrashLoopBackOff in production. Users reported timeouts.

## Root cause

OOMKilled. Container memory limit was 512Mi; JVM heap plus non-heap usage exceeded it under load.

## Resolution

1. Retrieved runbook for CrashLoopBackOff and high memory.
2. Confirmed via `kubectl describe pod` and EFK logs that lastState.terminated.reason was OOMKilled.
3. Scaled deployment from 3 to 4 replicas to reduce per-pod load (within max 20).
4. Updated deployment memory limit from 512Mi to 1Gi and triggered rolling restart.
5. Waited for rollout; verified restarts stopped and /health returned 200.

## Verification

- `kube_deployment_status_replicas_ready` matched desired.
- No new restarts in 1h.
- Resolution notes added to SNOW; incident closed.

## Tags

d2, java, OOMKilled, CrashLoopBackOff, memory
