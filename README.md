# Flow Gen2

## Local development quickstart

### Prerequisites
- Python 3.11 (see `PYTHON_BIN` in `Makefile`)
- Node.js 20.19+ (Vite 7 requires Node >= 20.19 or >= 22.12)
- npm
- Podman or Docker (Makefile uses `podman` by default)
- `psql` (optional, useful for inspecting local Postgres)

### Run tests locally (Makefile targets)
- `make test` (runs API tests with a temporary Postgres container)
- `make test-db-up` / `make test-db-down`
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

### Ports used by local services (defaults)
- API: `5556`
- UI: `5558`
- UI alt: `5560`
- Postgres (local): `5432`
- Postgres (tests): `5433`
- API tests: `4175`
- MinIO: `9000`
- MinIO console: `9001`
