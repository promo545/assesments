from src.notification_processor import Processor
from src.models import NotificationRequest, DeliveryRecord
from src.strategies.fixed_retry import FixedRetry
from src.notification_status import NotificationStatus
from src.exceptions import InvalidNotificationRequest, NotificationNotFound, PermanentDeliveryError, TemporaryDeliveryError
from tests.conftest import MockFactory, CustomMockChannel
import pytest

def test_email_success(repository, channel_factory):
    request = NotificationRequest(
                "001",
                'email',
                'testing email',
                'test001@test.com'
            )

    processor = Processor(
        FixedRetry(1, 0)
    )
    notification_id = processor.process(
                            request,
                            repository,
                            channel_factory
                        )

    assert processor.get_notifcation_status(notification_id, repository) == NotificationStatus.SENT 


def test_sms_success(repository, channel_factory):
    request = NotificationRequest(
                "001",
                'sms',
                'testing sms',
                None,
                786094732
            )

    processor = Processor(
        FixedRetry(1, 0)
    )
    notification_id = processor.process(
                            request,
                            repository,
                            channel_factory
                        )

    assert processor.get_notifcation_status(notification_id, repository) == NotificationStatus.SENT 



def test_push_success(repository, channel_factory):
    request = NotificationRequest(
                "001",
                'push',
                'testing push',
                None,
                None,
                '4567-9383-0398'
            )

    processor = Processor(
        FixedRetry(1, 0)
    )
    notification_id = processor.process(
                            request,
                            repository,
                            channel_factory
                        )

    assert processor.get_notifcation_status(notification_id, repository) == NotificationStatus.SENT 

def test_email_fail(repository , channel_factory):

    request = NotificationRequest(
                '001',
                'email',
                'testing email',
                None
            )
    processor = Processor(
                FixedRetry(1, 0)
                )
    with pytest.raises(InvalidNotificationRequest):
        notification_id = processor.process(
            request,
            repository,
            channel_factory
        )
    records = list(repository.records.values())
    assert len(records) == 1
    assert records[0].status == NotificationStatus.FAILED

def test_sms_fail(repository , channel_factory):

    request = NotificationRequest(
                '001',
                'sms',
                'testing sms',
                None
            )
    processor = Processor(
                FixedRetry(1, 0)
                )
    with pytest.raises(InvalidNotificationRequest):
        notification_id = processor.process(
            request,
            repository,
            channel_factory
        )
    records = list(repository.records.values())
    assert len(records) == 1
    assert records[0].status == NotificationStatus.FAILED

def test_push_fail(repository , channel_factory):

    request = NotificationRequest(
                '001',
                'push',
                'testing push',
                None
            )
    processor = Processor(
                FixedRetry(1, 0)
                )
    with pytest.raises(InvalidNotificationRequest):
        notification_id = processor.process(
            request,
            repository,
            channel_factory
        )
    records = list(repository.records.values())
    assert len(records) == 1
    assert records[0].status == NotificationStatus.FAILED

def test_failures_retried_success(repository):
    mock_channel = CustomMockChannel(attempts_to_be_made=2, should_succeed=True)
    mock_factory = MockFactory(mock_channel)
    
    request = NotificationRequest('001', 'mock', 'testing mock', None)
    processor = Processor(FixedRetry(3, 0)) 
    
    notification_id = processor.process(request, repository, mock_factory)
    
    assert mock_channel.attempt_count == 3
    assert processor.get_notifcation_status(notification_id, repository) == NotificationStatus.SENT


def test_exhausted_temporary_failures(repository):
    mock_channel = CustomMockChannel(attempts_to_be_made=5, should_succeed=True)
    mock_factory = MockFactory(mock_channel)

    request = NotificationRequest('002', 'mock', 'testing mock', None)
    processor = Processor(FixedRetry(2, 0)) 

    with pytest.raises(TemporaryDeliveryError):
        processor.process(request, repository, mock_factory)
        
    records = list(repository.records.values())
    
    assert mock_channel.attempt_count == 2
    assert records[-1].status == NotificationStatus.FAILED
    assert records[-1].failure_reason == "Simulated temporary failure"
    

def test_permanent_delivery_error_not_retried(repository):
    mock_channel = CustomMockChannel(attempts_to_be_made=0, should_succeed=False)
    mock_factory = MockFactory(mock_channel)

    request = NotificationRequest('003', 'mock', 'testing mock', None)
    processor = Processor(FixedRetry(3, 0)) 

    with pytest.raises(PermanentDeliveryError):
        processor.process(request, repository, mock_factory)
        
    records = list(repository.records.values())
    
    assert mock_channel.attempt_count == 1
    assert records[-1].status == NotificationStatus.FAILED


def test_unsupported_channel_fails_correctly(repository, channel_factory):
    request = NotificationRequest('004', 'invalid_channel', 'testing invalid', None)
    processor = Processor(FixedRetry(1, 0))

    with pytest.raises(Exception): 
        processor.process(request, repository, channel_factory)


def test_unknown_notification_id_raises_exception(repository):
    processor = Processor(FixedRetry(1, 0))
    
    with pytest.raises(NotificationNotFound):
        processor.get_notifcation_status("non_existent_id", repository)