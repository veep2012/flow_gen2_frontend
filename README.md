# Flow Gen2

## Oracle Linux 9.4 setup

### Install system packages
mmake ```bash
sudo dnf install -y git podman python3.11 openssh-clients
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
make local-up
```

## Local development quickstart

### Prerequisites
- Python 3.11 (see `PYTHON_BIN` in `Makefile`)
- Podman or Docker (Makefile uses `podman` by default)
- `psql` (optional, useful for inspecting local Postgres)

### Default frontend workflow
- `make local-ui-up` starts the Vite dev server in a persistent `node:22.14.0-alpine` container with the repository bind-mounted from the host.
- `make local-ui-down` stops and removes the dev container.
- `make local-ui-logs` tails the dev container logs.
- `make local-ui-test` runs UI unit tests in a short-lived container when `ui/package.json` defines `test`.
- `make local-ui-lint` runs `eslint` and `prettier --write` in a short-lived container.
- `make local-ui-build` runs the production UI build in a short-lived container and writes the result to `ui/dist` in the host repo.
- `make local-ui-audit` runs `npm audit --package-lock-only` in a short-lived container.
- `make local-ui-reset` removes the UI container and the named `node_modules` volume.
- `make local-ui-hard-reset` also removes the pinned Node image.

The local UI workflow keeps source code on the host and stores `ui/node_modules` in the named container volume `flow_gen2_ui_node_modules`. The toolchain refreshes dependencies with `npm ci` when `ui/package-lock.json` changes, and normal source edits do not trigger reinstall or image rebuild.

### Run tests locally (Makefile targets)
- `make test` (runs API tests + type checks + lint; runs UI test targets if configured)
- `make test-up` / `make test-down` (bring test stack up/down for iterative debugging)
- `make test-ui-unit` (reuses `make local-ui-test`)
- `make test-ui-e2e` (runs UI E2E tests in a short-lived container if `ui/package.json` has a `test:e2e` script)
- `make test-db-up` / `make test-db-down`
- `make test-minio-up` / `make test-minio-down`
- `make audit` (runs `pip-audit` + `make local-ui-audit`)

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
- `make local-ui-logs`
- `make local-ui-reset`
- `make local-ui-hard-reset`

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

For local account switching from the UI authentication error page, the compose stack sets `OAUTH2_PROXY_PROMPT=login` so `/oauth2/start` forces a fresh Keycloak login prompt instead of silently reusing the current IdP session.

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
- `APP_ENV` controls environment mode (`local/dev/test/ci` recommended for local runs).
- `APP_USER` optionally bootstraps DB session user in non-production only; value must be a valid `user_acronym` from `workflow.users` (lookup is case-insensitive, but using the canonical uppercase acronym, e.g. `FDQC`, is recommended for consistency).
- Non-local compose/runtime flows should leave `APP_USER` unset and provide identity through the trusted request header (`TRUSTED_IDENTITY_HEADER`, default `X-Auth-User`) injected by the edge proxy.
- `APP_USER_DB_WAIT_SEC` controls how long API startup waits for DB readiness during `APP_USER` validation (default `30`).
- `APP_USER_DB_WAIT_POLL_SEC` controls retry interval for that wait loop (default `1`).
- `VITE_AUTH_START_URL` optionally overrides the UI auth re-entry target used by the authentication error page. Set it to the nginx/oauth2-proxy entrypoint (for example `http://localhost/oauth2/start`) when the UI is served directly from Vite on `:5558` instead of through nginx.
- For compose/containerized UI builds, put `VITE_API_BASE_URL` and `VITE_AUTH_START_URL` in `.env.compose` because the UI image is built by `ci/Dockerfile.ui` and Vite reads these values at build time.

### UI troubleshooting
- If the UI dev container starts but dependencies look stale, run `make local-ui-reset`.
- If the Node image itself is corrupted or you want a full frontend runtime rebuild from scratch, run `make local-ui-hard-reset`.
- File-watch behavior depends on the local container runtime. If hot reload is delayed, inspect `make local-ui-logs` first and confirm the repository is bind-mounted from the host.
- Host-side `ui/node_modules` is not part of the supported workflow. The containerized workflow mounts its own named volume over that path.

### Seed data (Postgres)
- `ci/init/flow_seed.sql` inserts into `ref/core/workflow` tables and must run as a privileged role
  (e.g., `postgres`/`db_owner`). `app_user` is read-only on workflow tables and cannot run seeds.

### Ports used by local services (defaults)
- API: `5556`
- UI: `5558`
- Postgres (local): `5432`
- Postgres (tests): `5433`
- API tests: `4175`
- MinIO: `9000`
- MinIO console: `9001`
- Keycloak: `8081`

**Note:** oauth2-proxy (port 4180) is only accessible within the Docker network via nginx and is not exposed to the host.
