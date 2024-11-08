from celery import shared_task
from django.db import transaction
from structlog import get_logger
from core.event_log_client import EventLogClient
from users.models import Outbox

logger = get_logger(__name__)

@shared_task
def process_outbox_events():    
    pending_events = Outbox.objects.filter(status='PENDING')
    
    if not pending_events.exists():
        logger.info("No pending events in the outbox.")
        return

    with transaction.atomic():
        for event in pending_events:
            try:
                # Send the event to ClickHouse
                with EventLogClient.init() as client:
                    client.insert(
                        data=[{
                            "event_type": event.event_type,
                            "event_date_time": event.event_date_time,
                            "environment": event.environment,
                            "event_context": event.event_context,
                            "metadata_version": event.metadata_version,
                        }]
                    )
                
                # Update the status of the event in the outbox
                event.status = 'PROCESSED'
                event.save(update_fields=['status'])
                logger.info("Processed event from outbox", event_id=event.id)

            except Exception as e:
                logger.error("Failed to process event", event_id=event.id, error=str(e))
                # Rollback to ensure consistency if any error occurs
                transaction.set_rollback(True)
                break
