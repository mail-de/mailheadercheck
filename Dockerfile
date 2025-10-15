# Minimal Docker image for running the mailheadercheck milter
# Builds a runtime image only (no wheels/source distribution created)

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system build deps for pymilter and Python runtime deps
# - gcc and libmilter-dev are needed to build the pymilter C extension
# - libc6-dev provides standard C headers (e.g., stdlib.h) required by gcc
# - PyYAML: configuration parsing
# - setproctitle: optional
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libmilter-dev \
  && pip install --no-cache-dir \
    pymilter \
    PyYAML \
    setproctitle \
  && rm -rf /var/lib/apt/lists/*

# Create application user and directories
WORKDIR /app
RUN useradd -r -u 10001 -g root appuser \
    && mkdir -p /config \
    && chown -R appuser:root /app /config

# Copy only what we need to run
COPY mailheadercheck /app/mailheadercheck
COPY mailheaderchecklib /app/mailheaderchecklib
COPY LICENSE README.md /app/

USER appuser

# Default milter port as used in sample config
EXPOSE 30073

# By default, read config from /config/config.yaml (mounted by docker compose)
ENTRYPOINT ["python", "-u", "/app/mailheadercheck"]
CMD ["--config", "/config/config.yaml"]
