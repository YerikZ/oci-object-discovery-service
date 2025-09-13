from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from oci_object_discovery_service.internal import manifest, queue
from oci_object_discovery_service.internal.ui.routes import router as ui_router

app = FastAPI(title="OCI Object Discovery Service API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow React UI to call
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# expose under /api/ui
app.include_router(ui_router, prefix="/api/ui", tags=["UI"])


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
