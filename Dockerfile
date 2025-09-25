FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Seoul \
    PYTHONPATH=/app/src \
    APP_MODULE=app.main:app \
    HOST=0.0.0.0 \
    PORT=8080

# 과학 연산/빌드 의존
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc gfortran \
      libopenblas-dev libpq-dev curl tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

# 애플리케이션
COPY src ./src

# 엔트리포인트: 스토리지 폴더 보장 후 uvicorn 실행
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 비루트 사용자(UID 고정: 1000)
RUN useradd -u 1000 -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
# 단일 볼륨 전략: VOLUME 선언 불필요(컴포즈/런에서 /app/storage만 마운트)
CMD ["/entrypoint.sh"]
