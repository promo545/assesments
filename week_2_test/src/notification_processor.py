import uuid
from src.factory import NotificationFactory
from src.models import DeliveryRecord, NotificationRequest
from src.strategies.retry_strategy import RetryStrategy
from src.notification_repository import NotificationRepository
from src.notification_status import NotificationStatus
from src.exceptions import (
    TemporaryDeliveryError, 
    PermanentDeliveryError, 
    InvalidNotificationRequest
)

class Processor:
    def __init__(self, retry_strategy: RetryStrategy):
        self.retry_strategy = retry_strategy

    def process(self, 
                notification_request: NotificationRequest, 
                notification_records: NotificationRepository, 
                factory: NotificationFactory) -> str:

        notification_channel = factory.create(notification_request.channel)
        notification_id = str(uuid.uuid4())

        record = DeliveryRecord(
            notification_id,
            notification_request,
            NotificationStatus.PENDING,
            0
        )
        notification_records.add_record(record)

        def execute_send():
            return notification_channel.send(notification_id, notification_records)
            
        try: 
            process_result, attempt_count = self.retry_strategy.execute(execute_send)
        except (
            InvalidNotificationRequest,
            TemporaryDeliveryError,
            PermanentDeliveryError
        ) as e:
            notification_records.update_record(
                notification_id, 
                NotificationStatus.FAILED, 
                attempt_count=self.retry_strategy.attempt_count, 
                failure_reason=str(e)
            )
            raise
            
        if not process_result:
            notification_records.update_record(
                notification_id, 
                NotificationStatus.FAILED, 
                attempt_count=attempt_count, 
                failure_reason=str(process_result)
            )
        else:
            notification_records.update_record(
                notification_id, 
                NotificationStatus.SENT, 
                attempt_count=attempt_count
            )    

        return notification_id

    def get_notification_status(self, notification_id: str, notification_records: NotificationRepository) -> NotificationStatus:
        record = notification_records.get_record(notification_id)
        return record.status