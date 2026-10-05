# Deployment

## Running locally with Docker Compose

First time setup:

```bash
cp .env.example .env
# fill in real values in .env — this file is what docker-compose reads
# for everything except POSTGRES_URI/QDRANT_URL (see docker-compose.yml
# for why those two are special-cased)

docker compose build
docker compose up -d postgres qdrant   # start just the databases first
```

Apply the database schema. Which command depends on whether this is a
**fresh** Postgres (new volume, no data) or you're pointing at your
**existing** database:

```bash
# Fresh database (new docker volume, e.g. first time ever running this):
docker compose run --rm app alembic upgrade head

# Existing database (tables already exist from before migrations existed):
docker compose run --rm app alembic stamp head
```

See the migration file itself (`migrations/versions/..._baseline_schema...py`)
for the full explanation of why these are different commands.

Then start everything:

```bash
docker compose up -d
curl http://localhost:8000/health
```

## Image size

This image is larger than a typical FastAPI service because
`langchain_huggingface` pulls in `sentence-transformers` and `torch`
for local embeddings. If startup time or image size becomes a problem,
the two usual fixes are: (1) switch `EMBEDDING_PROVIDER` to an API-based
provider instead of a local model, or (2) use a CPU-only torch wheel
explicitly pinned in requirements.txt instead of the default
(GPU-capable) build, which is significantly smaller.

## Secrets in production

`.env` files are fine for local development — they are NOT fine to ship
inside a production container image or commit anywhere. `.dockerignore`
already excludes `.env` from the Docker build context so it can't end
up baked into an image layer by accident, but you still need a real
place for secrets to live in production. In rough order of how most
small teams actually do this:

- **Your hosting platform's built-in secret store** — Railway, Render,
  Fly.io, and most PaaS providers let you set environment variables in
  their dashboard/CLI, injected into the container at runtime. This is
  almost always the right starting point: zero extra infrastructure.
- **A dedicated secrets manager** (Doppler, AWS Secrets Manager, GCP
  Secret Manager, HashiCorp Vault) — worth it once you have multiple
  services/environments (staging + prod) sharing secrets, or need
  rotation/audit logs. Overkill for a single service on day one.

Whichever you pick, the app doesn't need to change: it already reads
every secret from the environment via `src/rag/config.py`'s `Settings`
class (see Phase 0 of the production-readiness report) — "where the
environment variables come from" is a deploy-time concern, not a code
concern.

## CI

`.github/workflows/ci.yml` lints, format-checks, runs migrations
against a throwaway Postgres service container, runs the test suite,
and verifies the Docker image still builds — on every push. It does
not deploy anywhere yet. Wiring an actual deploy step means:

1. Push this image to a registry (GitHub Container Registry is the
   path of least resistance since it needs no extra account — just
   `docker/build-push-action` with `GITHUB_TOKEN`, which Actions
   already has).
2. Tell your hosting platform to pull and run that image, or add a
   platform-specific deploy action (e.g. Railway's, Fly's) to the
   workflow, authenticated with an API token stored as a GitHub Actions
   secret.

This is deliberately left undone rather than guessed at, since it
depends entirely on which platform you choose.
