# Docker Images and Registries

Docker images are blueprints for containers. An image is built from layers, each representing a step in the Dockerfile.

## Image Layers

Each instruction in a Dockerfile creates a new layer:
```
FROM python:3.11
RUN pip install requests
COPY app.py /app/
CMD ["python", "app.py"]
```

Layers are cached and reused, making rebuilds faster. The final image combines all layers.

## Image Registries

Registries store and distribute images:
- **Docker Hub**: Public registry maintained by Docker, Inc.
- **Private Registries**: Enterprise-grade storage (AWS ECR, Azure ACR, Google Artifact Registry)

Images are named following the pattern: `[registry]/[namespace]/[repository]:[tag]`

Example: `gcr.io/my-project/api-service:v1.2.3`
