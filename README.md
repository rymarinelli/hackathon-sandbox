# Gateway Service

This project exposes a simple FastAPI gateway with health/readiness endpoints, environment-driven configuration, structured logging, and OpenTelemetry hooks.

## Configuration

Settings are pulled from environment variables (with sensible defaults):

- `APP_NAME` – logical service name (default `gateway`).
- `APP_HOST` / `APP_PORT` – bind address for the HTTP server.
- `LOG_LEVEL` – Python logging level (default `INFO`).
- `REDIS_URL` – optional Redis connection string (e.g., `redis://redis:6379/0`).
- `READY_REDIS_CHECK` – when `true`, readiness requires Redis to be reachable.
- `REQUEST_TIMEOUT_S` – timeout for dependency checks (seconds).
- `OTEL_SERVICE_NAME` – value for the OpenTelemetry `service.name` resource (default `gateway`).
- `OTEL_EXPORTER_OTLP_ENDPOINT` – OTLP gRPC endpoint for trace export.
- `OTEL_EXPORTER_OTLP_INSECURE` – set to `true` when the OTLP endpoint does not use TLS.

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn gateway.main:app --reload
```

Health and readiness probes are available at `/healthz` and `/readyz`.

## Docker usage

Build and run the container locally:

```bash
docker build -t gateway:local .
docker run --rm -p 8000:8000 -e APP_PORT=8000 -e APP_HOST=0.0.0.0 gateway:local
```

An entrypoint script automatically wires environment variables into the uvicorn command.

### Docker Compose example

A ready-to-run compose file is available at `deploy/docker-compose.yml`:

```bash
cd deploy
docker compose up --build
```

The compose stack brings up the gateway alongside Redis (and optionally an OTLP collector) and publishes the HTTP service on `localhost:8000`.

### Helm values example

Example Helm values are provided in `deploy/helm/values.yaml` for deploying the gateway and a bundled Redis instance. Adjust image repository/tag, resource requests, and environment variables to match your cluster.
