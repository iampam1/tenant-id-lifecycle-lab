# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (if any are needed, e.g., for psycopg2 if not using binary)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev     #     && rm -rf /var/lib/apt/lists/*
# (psycopg2-binary should avoid needing these, but good to note)

# Install Python dependencies
# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and Alembic configuration
# Copy alembic.ini to the root of /app
COPY alembic.ini .
# Copy the migrations directory into /app/src/db/migrations (matching script_location)
COPY src/db/migrations ./src/db/migrations/
# Copy the rest of the application source code
COPY src/ ./src/

# Expose port (though Uvicorn --port will also handle this)
EXPOSE 8000

# Define the command to run the application
# This will first attempt to upgrade the database schema using Alembic,
# then start the Uvicorn server.
# Ensure DATABASE_URL is available as an environment variable in the container.
CMD sh -c "echo 'Attempting DB migration...' && alembic upgrade head && echo 'DB migration attempt finished.' && echo 'Starting Uvicorn server...' && uvicorn src.app.main:app --host 0.0.0.0 --port 8000"
