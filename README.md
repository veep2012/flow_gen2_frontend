# Flow Gen2

## Oracle Linux 9.4 setup

### Install system packages
```bash
sudo dnf install -y git podman python3.11 npm openssh-clients
sudo dnf module enable -y nodejs:22
sudo dnf module install -y nodejs:22
```

### Configure SSH access
```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
# Place your private key in ~/.ssh and ensure it has the correct permissions
chmod 600 ~/.ssh/id_ed25519
ssh-add ~/.ssh/id_ed25519
```

### Clone the repository
```bash
git clone git@github.com:veep2012/flow_gen2.git -b frontend
```

### Prepare the local environment
```bash
make local-venv
make local-npm
make local-up
```

## Local development quickstart

### Prerequisites
- Python 3.11 (see `PYTHON_BIN` in `Makefile`)
- Node.js 20.19+ (Vite 7 requires Node >= 20.19 or >= 22.12)
- npm
- Podman or Docker (Makefile uses `podman` by default)
- `psql` (optional, useful for inspecting local Postgres)

### Run tests locally (Makefile targets)
- `make test` (runs API tests + type checks + lint; runs UI test targets if configured)
- `make test-up` / `make test-down` (bring test stack up/down for iterative debugging)
- `make test-ui-unit` (runs UI unit tests if `ui/package.json` has a `test` script)
- `make test-ui-e2e` (runs UI E2E tests if `ui/package.json` has a `test:e2e` script)
- `make test-db-up` / `make test-db-down`
- `make test-minio-up` / `make test-minio-down`
- `make audit` (runs `pip-audit` + `npm audit` against lockfiles)

### Run the API
- `make local-api-up`
- `make local-api-down`

### API docs (Swagger UI / ReDoc)
With the API running (`make local-api-up`):
- Swagger UI: `http://localhost:5556/docs`
- ReDoc: `http://localhost:5556/redoc`
- OpenAPI JSON: `http://localhost:5556/openapi.json`

### Run the UI
- `make local-ui-up`
- `make local-ui-down`

### Run the UI alt
- `make local-ui-alt-start`
- `make local-ui-alt-stop`

### Run MinIO (object storage)
- `make local-minio-up`
- `make local-minio-down`

### Run Keycloak + oauth2-proxy (compose)
These services are part of the compose stack (see `ci/docker-compose.yml`).
Run compose from the repo root so relative paths resolve correctly.
The compose file mounts `../.local/keycloak` (repo root `.local/keycloak`) for Keycloak logs.
`make up` creates it automatically; if you run `podman-compose` directly, create it first:
```bash
mkdir -p .local/keycloak
```
Use an env file for compose secrets (example template in `.env.example`):
```bash
cp .env.example .env.compose
podman-compose --env-file .env.compose -f ci/docker-compose.yml up -d
```
Fast startup without auth stack (no Keycloak/oauth2-proxy/nginx):
```bash
make up-no-keycloak
```
Defaults:
- Keycloak: `http://localhost:8081` (realm `flow-local`)
- Test user: `testuser` / `TestUser!2345`
- oauth2-proxy callback: `http://localhost/oauth2/callback`

#### Configure Keycloak client for oauth2-proxy
Create a confidential client in the `flow-local` realm:
1) Keycloak Admin Console → Clients → Create client.
2) Client ID: `flow-oauth2-proxy` (or set `OAUTH2_PROXY_CLIENT_ID` to match).
3) Client type: Confidential; enable standard flow.
4) Valid redirect URIs: `http://localhost/oauth2/callback` (match `OAUTH2_PROXY_REDIRECT_URL`).
5) Copy the generated client secret.

Provide the secret to oauth2-proxy via environment variables (Makefile uses `.env.compose` for compose runs, so set it there or export in shell):
```bash
export OAUTH2_PROXY_CLIENT_SECRET="your-client-secret"
```

Generate a cookie secret (32 bytes) for oauth2-proxy:
```bash
python - <<'PY'
import secrets, string
alphabet = string.ascii_letters + string.digits
print("".join(secrets.choice(alphabet) for _ in range(32)))
PY
```
Then set it before starting compose:
```bash
export OAUTH2_PROXY_COOKIE_SECRET="your-32-byte-secret"
```

### Environment variables (API + MinIO)
- DB connection:
- Prefer `APP_DATABASE_URL` for explicit DSN overrides.
- If `APP_DATABASE_URL` is unset, the API builds it from `APP_DB_USER` / `APP_DB_PASSWORD` plus
  `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB`.
- `DATABASE_URL` is ignored (legacy). Use `APP_DATABASE_URL` instead.
- `MINIO_ENDPOINT` supports `host:port` or `http(s)://host:port` (scheme controls TLS).
- `MINIO_SECURE` (`1`/`true` enables TLS when no scheme is provided).
- `MINIO_BUCKET` defaults to `flow-default` (override as needed).
- `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` are required for MinIO access in local dev and CI.
- `MAX_UPLOAD_SIZE_MB` limits upload size (default 128).
- `MINIO_RETRIES` / `MINIO_RETRY_DELAY_SEC` control MinIO retry behavior.

### Seed data (Postgres)
- `ci/init/flow_seed.sql` inserts into `ref/core/workflow` tables and must run as a privileged role
  (e.g., `postgres`/`db_owner`). `app_user` is read-only on workflow tables and cannot run seeds.

### Ports used by local services (defaults)
- API: `5556`
- UI: `5558`
- UI alt: `5560`
- Postgres (local): `5432`
- Postgres (tests): `5433`
- API tests: `4175`
- MinIO: `9000`
- MinIO console: `9001`
- Keycloak: `8081`

**Note:** oauth2-proxy (port 4180) is only accessible within the Docker network via nginx and is not exposed to the host.
