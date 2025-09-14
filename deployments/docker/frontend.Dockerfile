FROM python:3.11-slim

# set working directory
WORKDIR /app

# copy only requirements first for caching
COPY oci_object_discovery_service/frontend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt

# copy full source tree
COPY . .

# expose NiceGUI port
EXPOSE 3000

# run frontend as package module
CMD ["python", "-m", "oci_object_discovery_service.frontend.app"]
