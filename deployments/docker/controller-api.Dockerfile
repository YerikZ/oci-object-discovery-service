FROM python:3.11-slim

WORKDIR /app

# Install uv (very fast dependency resolver/installer)
RUN pip install --no-cache-dir uv

# Copy pyproject.toml (and lockfile if you generated one with uv lock)
COPY pyproject.toml ./
# COPY uv.lock ./   # if using uv lock to pin versions

# Install dependencies directly from pyproject.toml
RUN uv pip install --system --no-cache .

# Copy source
COPY . .

# Expose port (for controller-api only)
EXPOSE 8080

# Run service (example: controller-api)
CMD ["python", "-m", "oci_object_discovery_service.cmd.controller_api.main"]
