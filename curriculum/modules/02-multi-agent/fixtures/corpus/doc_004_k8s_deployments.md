# Kubernetes Deployments and Scaling

Deployments are the recommended way to manage stateless applications in Kubernetes. They handle pod creation, updates, and rollbacks.

## Replica Sets

A Deployment manages one or more Replica Sets, which ensure the desired number of pod replicas are running at all times. If a pod crashes, the Replica Set creates a replacement.

## Rolling Updates

Deployments support rolling updates:
1. Old pods are gradually replaced with new ones
2. Traffic is only sent to healthy pods
3. If something goes wrong, the deployment can be rolled back to the previous version

Example update strategy:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 1
```

## Horizontal Pod Autoscaling

The Horizontal Pod Autoscaler (HPA) automatically scales the number of pod replicas based on metrics like CPU usage or custom metrics.
