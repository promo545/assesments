from src.factory import NotificationFactory
from src.models import DeliveryRecord, NotificationRequest
from src.strategies.retry_stategy import RetryStrategy
from src.notification_repository import NotificationRepository
from src.notification_status import NotificationStatus

import uuid

class Processor():
    
    def __init__(self, retry_stategy : RetryStrategy):

        self.retry_stategy = retry_stategy

    def process(self, 
                notification_request : NotificationRequest, 
                notification_records : NotificationRepository, 
                factory : NotificationFactory):

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
            process_request, attempt_count = self.retry_stategy.execute(execute_send)
        
        except Exception as e:
            notification_records.update_record(
                notification_id, 
                NotificationStatus.FAILED, 
                attempt_count=0, 
                failure_reason=str(e)
            )
            raise
        if not process_request:
            notification_records.update_record(notification_id, NotificationStatus.FAILED, attempt_count = attempt_count, failure_reason = process_request)
        else:
            notification_records.update_record(notification_id, NotificationStatus.SENT, attempt_count = attempt_count)    

        return notification_id

    def get_notifcation_status(self, notification_id : str, notification_records : NotificationRepository):
        record = notification_records.get_record(notification_id)
        return record.status
