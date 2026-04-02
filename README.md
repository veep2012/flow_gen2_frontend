# Flow Gen2 Frontend

This repository owns only the frontend application, its local build/test workflow, and the frontend runtime image build path. Backend runtime code, backend deployment manifests, backend tests, and shared engineering tooling were intentionally removed as part of repository split phase 3.

## Repository boundary

Kept in this repository:
- `ui/` frontend source, tests, and built assets
- `scripts/local-ui-container.sh` and `scripts/local-ui-runtime.sh` for the containerized frontend workflow
- `ci/Dockerfile.ui` for the frontend runtime image build
- `documentation/repo_split/` migration and split-planning records

Not kept in this repository:
- backend API or database source
- backend-owned product contract source definitions
- backend deployment manifests and local backend compose stacks
- shared skill/tooling assets that belong in `common`

## Prerequisites

- `make`
- Podman or Docker compatible with `docker run` / `docker build` semantics

## Local frontend workflow

Start the persistent frontend dev server:

```bash
make local-ui-up
```

Stop it:

```bash
make local-ui-down
```

Tail logs:

```bash
make local-ui-logs
```

Refresh dependencies in the managed volume:

```bash
make local-npm
```

Reset the container and dependency volume:

```bash
make local-ui-reset
```

## Validation

Run the frontend test, lint, and production build sequence:

```bash
make test
```

Run individual checks:

```bash
make local-ui-test
make local-ui-lint
make local-ui-build
make local-ui-audit
```

## Backend integration contract consumption

This repository does not own backend contract source. It consumes backend-owned integration behavior through runtime configuration only:

- `VITE_API_BASE_URL` points the UI at the backend API entrypoint. Default: `/api/v1`
- `VITE_AUTH_START_URL` points the UI at the backend-owned auth start endpoint. Default: `/oauth2/start`

Set them in your shell or in a local `.env` file before running frontend commands if your integration environment differs from the defaults.

## Frontend image build

Build the frontend runtime image:

```bash
make image-build
```

Override the local image tag if needed:

```bash
make image-build FRONTEND_IMAGE_TAG=registry.example.com/frontend:dev
```
