import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler = None


def start_price_sync_job(app):
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    from services.benchmark_service import sync_all_benchmarks
    from services.price_service import sync_all_live_assets

    interval_minutes = app.config["PRICE_SYNC_INTERVAL_MIN"]

    def run_sync():
        with app.app_context():
            try:
                result = sync_all_live_assets()
                logger.info("Scheduled price sync completed: %s", result["summary"])
            except Exception:
                logger.exception("Scheduled price sync failed")

            # Benchmarks ride the same schedule (§14.4) but in their own try block:
            # they're a comparison line, so a benchmark outage must never mark the
            # user's actual holdings as unsynced.
            try:
                result = sync_all_benchmarks()
                logger.info("Scheduled benchmark sync completed: %s", result["summary"])
            except Exception:
                logger.exception("Scheduled benchmark sync failed")

    scheduler = BackgroundScheduler(daemon=True)
    # first_run deliberately deferred by a full interval — an IntervalTrigger with
    # no explicit start time fires immediately, which would mean every create_app()
    # call (including Flask's debug reloader restarting on each file save) kicks
    # off a real sync against yfinance/mfapi.in.
    first_run = datetime.now() + timedelta(minutes=interval_minutes)
    scheduler.add_job(
        run_sync,
        "interval",
        minutes=interval_minutes,
        id="price_sync",
        replace_existing=True,
        next_run_time=first_run,
    )
    scheduler.start()

    _scheduler = scheduler
    return scheduler
