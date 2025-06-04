# FIST Content Moderation API - Fixed pyproject.toml Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Replace pyproject.toml with fixed version
RUN mv pyproject.toml.fixed pyproject.toml

# Install dependencies
RUN pip install --no-cache-dir -e .

# Install spaCy model
RUN python -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.5.0/en_core_web_sm-3.5.0-py3-none-any.whl

# Create non-root user
RUN useradd --create-home --shell /bin/bash fist
RUN chown -R fist:fist /app
USER fist

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]