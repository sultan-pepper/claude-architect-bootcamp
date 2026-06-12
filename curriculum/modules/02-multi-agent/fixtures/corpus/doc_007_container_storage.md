# Container Storage and Persistence

Containers are ephemeral by default. Data written to the container filesystem is lost when the container stops. Persistent storage is needed for databases and stateful applications.

## Docker Volumes

Docker provides several storage options:
- **Bind Mounts**: Host filesystem mounted into container
- **Named Volumes**: Managed by Docker, stored in `/var/lib/docker/volumes`
- **tmpfs Mounts**: In-memory storage, lost when container stops

## Kubernetes Persistent Volumes

Persistent Volumes (PV) are cluster-level storage resources independent of pods. Persistent Volume Claims (PVC) allow pods to request storage.

## Storage Classes

Storage Classes dynamically provision volumes based on requirements:
- Provisioner: Which storage backend to use (e.g., AWS EBS, Google Persistent Disk)
- Parameters: Configuration for the provisioner
- Reclaim Policy: What happens to the volume when the PVC is deleted

Dynamic provisioning simplifies managing storage in large clusters.
