from src.exceptions import InvalidNotificationRequest
from src.notification_channels.base import Base

from src.models import NotificationRequest, DeliveryRecord
from src.notification_repository import NotificationRepository

class PushChannel(Base):
    def __init__(self):
        self._channel_type = "push"

    @property
    def channel_type(self):
        return self._channel_type
    
    def send(self, notification_id : str, notification_records : NotificationRepository) -> bool:
        notification_record = notification_records.get_record(notification_id)

        valid_request = super().validate_request(notification_record.request)

        if notification_record.request.device_token == None or notification_record.request.device_token == "":
            raise InvalidNotificationRequest("Does not contain device_token")

        return True 
