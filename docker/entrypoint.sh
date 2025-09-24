#!/usr/bin/env bash
set -e
# 단일 볼륨(/app/storage) 하위 디렉터리 보장
mkdir -p /app/storage/analysis-reports /app/storage/logs /app/storage/models
exec uvicorn "${APP_MODULE}" --host "${HOST}" --port "${PORT}"
