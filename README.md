# Tracr

> Open-source OSINT intelligence platform for person and entity investigation.

Tracr collects, processes, and enriches publicly available information from social media, public databases, news feeds, and other open sources — surfacing relationships, patterns of life, and actionable intelligence through a clean API and graph-based UI.

## Status

🚧 Active development — Phase 1 (Data Foundation)

## Stack

- **Python 3.11** — async throughout
- **FastAPI** — REST API
- **PostgreSQL 15 + PostGIS** — primary data store
- **SQLAlchemy 2.x async + Alembic** — ORM and migrations
- **Celery + Redis** — job queue and scheduling
- **spaCy** — NLP / NER pipeline
- **Docker Compose** — local development
- **Kubernetes + Helm** — production deployment

## Quick Start

```bash
# Clone
git clone git@github-tracr:yvanigor98/tracr.git
cd tracr

# Install dependencies
make dev-install

# Copy environment config
cp .env.example .env

# Start services
make up

# Run migrations
make migrate

# Run tests
make test
```

## Architecture

See `/docs` for full architecture specification.

## License

Apache 2.0
