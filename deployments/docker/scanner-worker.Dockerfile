FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy pyproject.toml (and optionally uv.lock if you generated one)
COPY pyproject.toml ./
# COPY uv.lock ./

# Install dependencies into the system environment
RUN uv pip install --system --no-cache .

# Copy the source code
COPY . .

# Run the scanner worker service
CMD ["python", "-m", "oci_object_discovery_service.cmd.scanner_worker.main"]
