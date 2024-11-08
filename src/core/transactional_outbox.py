from users.models import Outbox
from django.db import transaction
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TransactionalOutbox:
    @staticmethod
    def save_event(event_type, event_context, metadata_version=1, environment="production"):
        """
        Inserts an event into the Outbox table within a transaction.
        """
        try:
            with transaction.atomic():
                Outbox.objects.create(
                    event_type=event_type,
                    event_date_time=datetime.now(),
                    environment=environment,
                    event_context=event_context,
                    metadata_version=metadata_version,
                    processed=False
                )
        except Exception as e:
            logger.error(f"Failed to save event to Outbox: {e}")
            raise e

    @staticmethod
    def process_outbox_entries():
        """
        Processes entries in the Outbox, forwarding them to ClickHouse, and marking them as processed.
        """
        unprocessed_entries = Outbox.objects.filter(processed=False)

        for entry in unprocessed_entries:
            try:
                # Placeholder for logic to forward entry to ClickHouse
                # E.g., ClickHouseClient.write_event(entry)
                
                # If successful, mark as processed
                entry.processed = True
                entry.save(update_fields=['processed'])
                
                logger.info(f"Processed event {entry.id} for ClickHouse")
                
            except Exception as e:
                logger.error(f"Error processing Outbox entry {entry.id}: {e}")
                continue
