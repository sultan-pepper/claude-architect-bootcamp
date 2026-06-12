# Kubernetes Resource Management

Proper resource allocation ensures applications run reliably and clusters are cost-efficient.

## Requests and Limits

- **Requests**: Minimum guaranteed resources for a pod
- **Limits**: Maximum resources a pod can consume

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

The scheduler places pods on nodes with sufficient requested resources. Limits prevent resource monopolization.

## Quality of Service (QoS) Classes

Kubernetes automatically assigns QoS classes:
- **Guaranteed**: Requests = Limits (highest priority)
- **Burstable**: Requests < Limits (medium priority)
- **BestEffort**: No requests/limits (lowest priority)

During resource contention, lower QoS pods are evicted first.

## Namespace Quotas

Resource Quotas limit aggregate resources per namespace, preventing resource hoarding by individual teams.
