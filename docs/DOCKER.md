# Docker / Docker Compose

This document describes how to run the project locally with Docker and how CI builds are configured.

## Local (docker-compose)

1. Checkout the prepared branch:
   ```bash
   git fetch origin
   git checkout add-docker-and-compose
   ```

2. Build and run:
   ```bash
docker-compose up --build
   ```

3. Open services:
   - Frontend (Streamlit): http://localhost:8501
   - Backend (FastAPI): http://localhost:8000

Notes:
- The compose file mounts `./data` to persist an SQLite file. For production use a managed DB.
- If your FastAPI entry is not `backend.main:app` or your Streamlit entryfile is not `frontend/app.py`, update the Dockerfiles accordingly.

## CI / Container registry

A GitHub Actions workflow is included to build and push images to GitHub Container Registry (ghcr.io). The workflow expects two repository secrets:
- `GHCR_USERNAME` — your GitHub username (or an account with package write access).
- `GHCR_TOKEN` — a Personal Access Token with `write:packages` and `repo` scopes (recommended).

The workflow builds and pushes:
- `ghcr.io/<org-or-username>/nexus-backend:...`
- `ghcr.io/<org-or-username>/nexus-frontend:...`

If you prefer using the `GITHUB_TOKEN` instead of a PAT, note that workflows may require additional permissions for `packages: write`. Adjust the workflow permissions if you want to use `GITHUB_TOKEN`.