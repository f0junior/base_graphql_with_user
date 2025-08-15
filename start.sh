#!/bin/bash
docker compose -f docker-redis.yml up -d
poetry run uvicorn app.main:app --host 0.0.0.0 --port 10000