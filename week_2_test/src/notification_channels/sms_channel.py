from src.notification_channels.base import Base
from src.notification_repository import NotificationRepository
from src.models import NotificationRequest, DeliveryRecord
from src.exceptions import InvalidNotificationRequest

class SMSChannel(Base):

    def __init__(self):
        self._channel_type = "sms"

    @property
    def channel_type(self):
        return self._channel_type
    
    def send(self, notification_id : str, notification_records : NotificationRepository) -> bool:
        notification_record = notification_records.get_record(notification_id) 
        valid_request = super().validate_request(notification_record.request)

        if notification_record.request.phone_number == None or notification_record.request.phone_number == "":
            raise InvalidNotificationRequest("Does not contain phone_number")

        return True 
