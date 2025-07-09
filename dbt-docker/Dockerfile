# dbt-postgres Dockerfile
FROM python:3.10-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install build tools + Postgres client
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libpq-dev \
    curl \
    && apt-get clean

# Install dbt-postgres
RUN pip install --no-cache-dir dbt-postgres==1.9.0

# Set working directory
WORKDIR /usr/app

# Default command
ENTRYPOINT ["tail", "-f", "/dev/null"]
