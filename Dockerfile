# Minimal Docker image for running the mailheadercheck milter
# Builds a runtime image only (no wheels/source distribution created)

FROM debian:trixie-slim AS builder
WORKDIR /app

# Copy only what we need to test and run
COPY mailheadercheck /app/mailheadercheck
COPY mailheaderchecklib/ /app/mailheaderchecklib/
COPY testing.sh /app/
COPY tests /app/tests
COPY LICENSE README.md /app/

RUN    apt-get -y update \
    && apt-get -y install --no-install-recommends \
         miltertest \
         python3-milter \
         python3-yaml \
    && rm -rf /var/lib/apt/lists/* \

    # explicit set permissions
    && find /app -type d -exec chmod 0555 {} \; \
    && find /app -type f -exec chmod 0444 {} \; \
    && chmod 0555 /app/mailheadercheck \
                  /app/testing.sh \

    # run tests
    && /app/testing.sh \

    # cleanup files in /app only used to run tests
    && rm -rf testing.sh \
              tests

FROM debian:trixie-slim
WORKDIR /app

COPY --from=builder /app/ /app/

RUN    apt-get -y update \
    && apt-get -y install --no-install-recommends \
         python3-milter \
         python3-yaml \
    && rm -rf /var/lib/apt/lists/*
         
USER nobody

# Default milter port as used in sample config
EXPOSE 30073

# By default, read config from /config/config.yaml (mounted by docker compose)
ENTRYPOINT ["python3", "-u", "/app/mailheadercheck"]
CMD ["--config", "/config/config.yaml"]
