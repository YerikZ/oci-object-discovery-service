from fastapi import FastAPI
import uvicorn
from oci_object_discovery_service.internal import manifest, queue

app = FastAPI(title="OCI Object Discovery Service API")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/v1/manifests/reload")
def reload_manifests():
    jobs = manifest.load_from_file("manifests/example-catalogue.yaml")
    # In a real implementation, you might broadcast an update to the scheduler via queue/pubsub
    return {"jobs": [j["name"] for j in jobs]}

@app.post("/v1/scans/trigger")
def trigger_scan():
    # Triggers an immediate scan for all jobs in the manifest
    jobs = manifest.load_from_file("manifests/example-catalogue.yaml")
    for j in jobs:
        queue.enqueue(j)
    return {"enqueued": len(jobs)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
