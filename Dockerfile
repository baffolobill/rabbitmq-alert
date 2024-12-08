FROM python:3.13-slim-bookworm

ARG POETRY_VERSION=1.8.4

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=

WORKDIR /code
COPY / /code/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN set -ex && \
    pip install -U pip && \
    pip install "poetry==$POETRY_VERSION" && \
    poetry config virtualenvs.create false && \
    bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --without=dev ; fi"

RUN set -ex && \
    ls -la . && \
    pip install . && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/tmp/* && \
    rm -rf /usr/share/man/* && \
    rm -rf /usr/share/info/* && \
    rm -rf /var/cache/man/* && \
    rm -rf /tmp/*

CMD ["rabbitmq-alert"]
