# Kubernetes Ingress

Ingress manages external HTTP(S) access to services within a cluster. It provides routing rules and load balancing.

## Ingress Resources

An Ingress resource defines rules for routing external traffic:
```yaml
rules:
  - host: api.example.com
    http:
      paths:
        - path: /
          backend:
            serviceName: api-service
            servicePort: 8080
```

## Ingress Controllers

Ingress Controllers implement the Ingress specification:
- NGINX Ingress Controller (most popular)
- HAProxy Ingress
- AWS ALB Ingress Controller
- Google Cloud Load Balancing

The controller watches Ingress resources and configures routing accordingly.

## SSL/TLS Termination

Ingress can handle SSL/TLS certificates, offloading encryption from individual services. Certificates are stored in Kubernetes Secrets.
