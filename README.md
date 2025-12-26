# Flow Gen2

## Local development quickstart

### Prerequisites
- Python 3.11 (see `PYTHON_BIN` in `Makefile`)
- Node.js 20.19+ (Vite 7 requires Node >= 20.19 or >= 22.12)
- npm
- Podman or Docker (Makefile uses `podman` by default)
- `psql` (optional, useful for inspecting local Postgres)

### Run tests locally (Makefile targets)
- `make test` (runs API tests with temporary Postgres + MinIO containers)
- `make test-db-up` / `make test-db-down`
- `make test-minio-up` / `make test-minio-down`
- `make audit` (runs `pip-audit` + `npm audit` against lockfiles)

### Run the API
- `make local-api-up`
- `make local-api-down`

### Run the UI
- `make local-ui-up`
- `make local-ui-down`

### Run the UI alt
- `make local-ui-alt-start`
- `make local-ui-alt-stop`

### Run MinIO (object storage)
- `make local-minio-up`
- `make local-minio-down`

### Environment variables (API + MinIO)
- `MINIO_ENDPOINT` supports `host:port` or `http(s)://host:port` (scheme controls TLS).
- `MINIO_SECURE` (`1`/`true` enables TLS when no scheme is provided).
- `MINIO_BUCKET`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` control MinIO access.
- `MAX_UPLOAD_SIZE_MB` limits upload size (default 128).
- `MINIO_RETRIES` / `MINIO_RETRY_DELAY_SEC` control MinIO retry behavior.

### Ports used by local services (defaults)
- API: `5556`
- UI: `5558`
- UI alt: `5560`
- Postgres (local): `5432`
- Postgres (tests): `5433`
- API tests: `4175`
- MinIO: `9000`
- MinIO console: `9001`
