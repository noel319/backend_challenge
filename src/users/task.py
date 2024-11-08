from celery import shared_task
from clickhouse_connect.driver import Client
from users.models import Outbox
from core.settings import CLICKHOUSE_HOST, CLICKHOUSE_PORT

@shared_task
def process_outbox():
    outboxes = Outbox.objects.filter(processed=False)
    ch_client = Client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT)

    for outbox in outboxes:
        try:
            ch_client.insert(
                'default.event_log',
                [(outbox.event_type, outbox.event_date_time, outbox.environment, outbox.event_context, outbox.metadata_version)]
            )
            outbox.processed = True
            outbox.save()
        except Exception as e:
            print(f"Failed to push event to ClickHouse: {e}")
