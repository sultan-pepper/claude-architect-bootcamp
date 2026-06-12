# Container Monitoring and Observability

Monitoring containerized applications requires collecting metrics, logs, and traces across many dynamic containers.

## Metrics Collection

Kubernetes provides built-in metrics:
- **kubelet**: Collects metrics from each node
- **Metrics Server**: Aggregates metrics from kubelets
- **Prometheus**: Popular time-series database for metrics

Common metrics:
- CPU usage
- Memory consumption
- Network I/O
- Disk I/O

## Logging

Container logs are written to stdout/stderr:
- `docker logs`: View container logs
- `kubectl logs`: View pod logs

For persistent logging, aggregate logs to centralized systems (ELK stack, Splunk, Google Cloud Logging).

## Distributed Tracing

Tracing tracks requests across multiple services:
- Jaeger: Open-source tracing platform
- Zipkin: Distributed tracing system
- Cloud provider solutions (AWS X-Ray, Google Cloud Trace)

Traces show latency, dependencies, and errors in microservice architectures.
