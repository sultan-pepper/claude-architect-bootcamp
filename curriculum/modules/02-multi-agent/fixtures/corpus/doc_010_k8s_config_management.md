# Kubernetes Configuration Management

Separating configuration from container images enables the same image to run in different environments.

## ConfigMaps

ConfigMaps store non-sensitive configuration data:
```yaml
kind: ConfigMap
metadata:
  name: app-config
data:
  log-level: INFO
  database-url: postgres://db.example.com
```

Pods reference ConfigMaps through environment variables or volume mounts.

## Secrets

Secrets store sensitive data (passwords, API keys, certificates):
```yaml
kind: Secret
metadata:
  name: api-credentials
type: Opaque
data:
  password: <base64-encoded-password>
```

Kubernetes stores secrets in etcd. For production, use external secret management (HashiCorp Vault, AWS Secrets Manager).

## Environment Variables

Pods can inject configuration through environment variables from ConfigMaps or Secrets.

## Kustomize

Kustomize provides a template-free customization approach for Kubernetes manifests, enabling base configurations with environment-specific overlays.
