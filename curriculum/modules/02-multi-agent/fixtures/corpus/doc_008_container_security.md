# Container Security

Container security involves securing the image, runtime, and orchestration layers.

## Image Security

- **Scanning**: Tools scan images for known vulnerabilities (e.g., Trivy, Anchore)
- **Base Images**: Use minimal, regularly updated base images (Alpine, Distroless)
- **Layer Caching**: Avoid caching steps with external dependencies

## Runtime Security

- **Resource Limits**: Set CPU and memory limits to prevent resource exhaustion
- **Security Context**: Define user permissions, capabilities, read-only filesystems
- **Network Policies**: Restrict traffic between pods

In Kubernetes:
```yaml
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

## Registry Security

- **Authentication**: Access control to pull images
- **Signing**: Digital signatures verify image authenticity
- **Scanning on Push**: Automatic vulnerability scanning when images are pushed
