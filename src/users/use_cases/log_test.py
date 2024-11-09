import pytest
from unittest.mock import patch, MagicMock
from core.models import EventLogOutbox
from core.tasks import process_outbox_entries
from sentry_sdk import capture_exception

pytestmark = pytest.mark.django_db

@pytest.fixture
def create_unprocessed_log():
    return EventLogOutbox.objects.create(
        event_type="test_event",
        event_date_time="2024-10-27 10:33:00",
        environment="test",
        event_context={"key": "value"},
        processed=False
    )

@patch("core.tasks.EventLogClient")
def test_process_outbox_entries_success(mock_client, create_unprocessed_log):
    # Mock the ClickHouse client's insert method
    mock_client.init.return_value.__enter__.return_value.insert = MagicMock()

    # Run the task
    process_outbox_entries()

    # Assert that the log is marked as processed
    processed_log = EventLogOutbox.objects.get(id=create_unprocessed_log.id)
    assert processed_log.processed is True

@patch("core.tasks.EventLogClient")
@patch("core.tasks.sentry_sdk.capture_exception")
def test_process_outbox_entries_retry_on_failure(mock_capture_exception, mock_client, create_unprocessed_log):
    # Mock the ClickHouse client's insert method to raise an exception
    mock_client.init.return_value.__enter__.return_value.insert.side_effect = Exception("ClickHouse error")

    # Run the task, expect it to retry due to failure
    with pytest.raises(Exception, match="ClickHouse error"):
        process_outbox_entries.apply()

    # Assert that the log is still unprocessed due to failure
    unprocessed_log = EventLogOutbox.objects.get(id=create_unprocessed_log.id)
    assert unprocessed_log.processed is False

    # Assert Sentry captured the exception
    mock_capture_exception.assert_called_once()

@patch("core.tasks.EventLogClient")
def test_log_processing_with_logging_and_sentry(mock_client, create_unprocessed_log, caplog):
    # Mock the ClickHouse client's insert method
    mock_client.init.return_value.__enter__.return_value.insert = MagicMock()

    with patch("core.tasks.sentry_sdk.start_transaction"):
        # Run the task with logging enabled
        process_outbox_entries()

    # Assert log messages for successful insertion
    assert "Successfully inserted logs into ClickHouse" in caplog.text
    assert "Marked logs as processed in EventLogOutbox" in caplog.text

    # Check that the log is marked as processed
    assert EventLogOutbox.objects.filter(processed=True).count() == 1
