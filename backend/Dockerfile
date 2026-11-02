FROM python:3.12-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
       | gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
       > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-16 \
    && pg_dump --version | grep -E '^pg_dump \(PostgreSQL\) 16\.' \
    && pg_restore --version | grep -E '^pg_restore \(PostgreSQL\) 16\.' \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-lock.txt requirements-stack.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt -r requirements-stack.txt
COPY odontologia ./odontologia
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh && mkdir -p /data
EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
