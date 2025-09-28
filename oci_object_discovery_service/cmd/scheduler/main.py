import time
from apscheduler.schedulers.background import BackgroundScheduler
from oci_object_discovery_service.internal import manifest, session
from oci_object_discovery_service.utils.logger import logger


def run_job(job):
    logger.info(
        f"[scheduler] Starting job {job['name']} (every {job['frequency_minutes']} minutes)"
    )
    session.create_session(job)


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
    logger.info("[scheduler] started")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
