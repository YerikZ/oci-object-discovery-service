import time
from apscheduler.schedulers.background import BackgroundScheduler
from oci_object_discovery_service.internal import manifest, queue


def run_job(job):
    print(
        f"[scheduler] Enqueuing scan for bucket={job['bucket']} prefixes={job['prefixes']}"
    )
    queue.enqueue(job)


def main():
    scheduler = BackgroundScheduler()
    jobs = manifest.load_from_file("manifests/example-catalogue.yaml")
    for job in jobs:
        scheduler.add_job(
            run_job,
            "interval",
            minutes=job["frequency_minutes"],
            args=[job],
            id=job["name"],
            replace_existing=True,
        )
    scheduler.start()
    print("[scheduler] started")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
