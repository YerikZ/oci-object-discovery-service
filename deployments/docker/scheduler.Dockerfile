FROM python:3.11-slim

WORKDIR /app

# Install uv (fast dependency installer)
RUN pip install --no-cache-dir uv

# Copy pyproject.toml (and optionally uv.lock if you generated one)
COPY pyproject.toml ./
# COPY uv.lock ./

# Install dependencies into the system environment
RUN uv pip install --system --no-cache .

# Copy the source code
COPY . .

# Run the scheduler service
CMD ["python", "-m", "oci_object_discovery_service.cmd.scheduler.main"]
