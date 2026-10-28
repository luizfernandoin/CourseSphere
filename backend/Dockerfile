# Multi-stage / Hardened Backend Dockerfile for CourseSphere Flask API
FROM python:3.11-slim-bookworm AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl sqlite3 && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt ./

# Install python dependencies including gunicorn for production WSGI server
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Create a dedicated non-root user and group (Principle of Least Privilege)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M -d /app appuser

# Copy application source code
COPY . .

# Ensure credentials.json and dummy credentials exist for emulator compatibility
RUN if [ ! -f credentials.json ]; then cp credentials.dummy.json credentials.json; fi

# Pre-populate SQLite database paths for both 'cornell' and typo 'cournell'
RUN mkdir -p /app/cournell-course-sphere-data /app/cornell-course-sphere-data && \
    python -c "import sqlite3; \
    conn = sqlite3.connect('/app/cournell-course-sphere-data/roster_reviews.sqlite.db'); \
    conn.execute('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, name TEXT, section_id INTEGER, semester TEXT, department TEXT, instructor TEXT);'); \
    conn.execute('CREATE TABLE IF NOT EXISTS course_descriptions (id INTEGER PRIMARY KEY, course_id INTEGER, description TEXT);'); \
    conn.commit(); conn.close()" && \
    cp /app/cournell-course-sphere-data/roster_reviews.sqlite.db /app/cornell-course-sphere-data/roster_reviews.sqlite.db

# Set ownership of the /app directory to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root execution
USER appuser

EXPOSE 5000

ENV PORT=5000 \
    INSTANCE_ID=backend-standalone \
    OPENAI_OFFLINE_MOCK=true

# Gunicorn WSGI production server with 2 workers and 2 threads per worker
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "endpoints:app"]

