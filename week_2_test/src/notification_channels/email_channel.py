from src.notification_channels.base import Base

from src.models import NotificationRequest, DeliveryRecord
from src.exceptions import InvalidNotificationRequest
from src.notification_status import NotificationStatus
from src.notification_repository import NotificationRepository

import uuid

class EmailChannel(Base):
    def __init__(self):
        self._channel_type = "email"

    @property
    def channel_type(self):
        return self._channel_type
    
    
    def send(self, notification_id : str, notification_records : NotificationRepository):
        notification_record = notification_records.get_record(notification_id)

        valid_request = super().validate_request(notification_record.request)

        if notification_record.request.email_address == None or notification_record.request.email_address == "":
            raise InvalidNotificationRequest("Does not contain email")

        return True 
        



    