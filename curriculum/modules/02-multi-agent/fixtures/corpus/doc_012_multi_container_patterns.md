# Multi-Container Pod Patterns

Kubernetes allows multiple containers in a single pod for tightly coupled components.

## Sidecar Pattern

A sidecar container augments the main application container:
- Logging agent collecting logs
- Service mesh proxy (Envoy) handling network
- Security agent monitoring for threats

The main container is unaware of the sidecar's presence.

## Init Containers

Init containers run to completion before application containers start:
- Database migrations
- Configuration generation
- Certificate provisioning

Init containers share the pod's network namespace but have separate filesystem.

## Ambassador Pattern

An ambassador container mediates communication for the main container:
- Connection pooling
- Caching
- Service discovery

## Ambassador vs Sidecar

- Ambassador: Handles outbound connections
- Sidecar: Typically handles inbound concerns

Patterns are overlapping; the choice depends on responsibility and resource requirements.
