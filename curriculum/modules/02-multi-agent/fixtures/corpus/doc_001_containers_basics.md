# Container Fundamentals

Containers are lightweight, standalone packages that include everything needed to run an application: code, runtime, system tools, libraries, and settings. Unlike virtual machines, containers share the host OS kernel, making them more efficient.

## Key Characteristics

- **Isolation**: Each container has its own filesystem, process space, and network namespace
- **Portability**: "Write once, run anywhere" across different computing environments
- **Efficiency**: Minimal overhead compared to virtual machines
- **Speed**: Containers start in milliseconds

## Docker as Container Runtime

Docker is the most popular containerization platform. It provides:
- Images: Immutable templates containing application code and dependencies
- Containers: Running instances of images
- Registries: Centralized storage for images (e.g., Docker Hub)

A typical Docker workflow involves building an image with a Dockerfile, pushing it to a registry, and then pulling and running it on different hosts.
