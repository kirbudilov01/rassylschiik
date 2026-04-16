import logging
import time
from datetime import datetime

from src.config import settings
from src.database import SessionLocal
from src.services.outreach_engine import process_ready_queue


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] worker: %(message)s",
)
logger = logging.getLogger(__name__)


def run_worker() -> None:
    logger.info("worker started poll=%ss batch=%s", settings.worker_poll_seconds, settings.worker_batch_size)
    while True:
        start = datetime.utcnow()
        db = SessionLocal()
        try:
            report = process_ready_queue(db=db, batch_size=settings.worker_batch_size)
            logger.info("tick report=%s", report)
        except Exception as exc:
            logger.exception("tick failed: %s", exc)
        finally:
            db.close()

        spent = (datetime.utcnow() - start).total_seconds()
        sleep_for = max(1, settings.worker_poll_seconds - int(spent))
        time.sleep(sleep_for)


if __name__ == "__main__":
    run_worker()
