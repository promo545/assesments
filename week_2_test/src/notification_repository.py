from src.exceptions import NotificationNotFound, InvalidStateTransaction
from src.notification_status import NotificationStatus
from src.models import DeliveryRecord

class NotificationRepository:
    
    def __init__(self):
        self.records = {}

    def add_record(self, record : DeliveryRecord):
        self.records[record.notification_id] = record

    def get_record(self, notification_id : str):
        
        record = self.records.get(notification_id, None)

        if record is None:
            raise NotificationNotFound("Record could not be found")
        return record
    def update_record(self, notification_id : str, status : NotificationStatus, **kwargs) -> bool:

        record = self.get_record(notification_id)

        if record.status != NotificationStatus.PENDING:
            raise InvalidStateTransaction("Already processed")
        
        record.status = status
        record.attempt_count = kwargs.get('attempt_count', record.attempt_count)
        record.failure_reason = kwargs.get('failure_reason', record.failure_reason)

        return True
