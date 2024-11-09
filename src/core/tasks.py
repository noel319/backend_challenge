from celery import shared_task
from django.db import transaction
from core.models import EventLogOutbox
from core.event_log_client import EventLogClient
import logging
import sentry_sdk

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=5)
def process_outbox_entries(self):
    with sentry_sdk.start_transaction(op="task", name="process_outbox_entries"):
        try:
            # Query for unprocessed logs in the EventLogOutbox table
            unprocessed_logs = EventLogOutbox.objects.filter(processed=False)
            if unprocessed_logs.exists():
                with EventLogClient.init() as client:
                    # Prepare data for bulk insertion
                    data = [
                        {
                            "event_type": log.event_type,
                            "event_date_time": log.event_date_time,
                            "environment": log.environment,
                            "event_context": log.event_context,
                            "metadata_version": log.metadata_version,
                        }
                        for log in unprocessed_logs
                    ]

                    # Attempt bulk insert into ClickHouse
                    client.insert(data)
                    logger.info("Successfully inserted logs into ClickHouse", extra={"log_count": len(data)})

                # Mark logs as processed after successful insertion
                with transaction.atomic():
                    unprocessed_logs.update(processed=True)
                    logger.info("Marked logs as processed in EventLogOutbox", extra={"processed_log_count": len(data)})

        except Exception as e:
            logger.error("Failed to insert logs into ClickHouse", exc_info=True)
            sentry_sdk.capture_exception(e)
            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
