# Container Networking

Containers need to communicate with each other and the outside world. Container networking is fundamental to multi-container applications.

## Docker Networking Modes

- **Bridge**: Default mode; each container gets its own IP
- **Host**: Container shares the host's network stack
- **Overlay**: For multi-host networking in Docker Swarm

Containers can communicate by container name within a Docker network.

## Kubernetes Services

Services in Kubernetes provide stable network access to pods:
- **ClusterIP**: Internal access within the cluster
- **NodePort**: External access via a port on each node
- **LoadBalancer**: Cloud provider's load balancer for external access
- **ExternalName**: CNAME record for external services

Service discovery in Kubernetes uses DNS: `service-name.namespace.svc.cluster.local`
