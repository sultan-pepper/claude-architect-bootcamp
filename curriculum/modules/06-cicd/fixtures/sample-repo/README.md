# Sample Monorepo

A small Python monorepo with two microservices and a shared library.

## Structure

- `src/shared/` - Shared utility library
- `src/api-service/` - REST API service
- `src/worker-service/` - Background worker service
- `tests/` - Integration and unit tests
- `config/` - Configuration management

## Setup

```bash
make install
make test
make lint
```

## Services

### API Service
Provides HTTP endpoints for client requests.

### Worker Service
Processes background tasks asynchronously.

### Shared Library
Common utilities used by both services.
