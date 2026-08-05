from src.notification_channels.base import Base
from src.exceptions import InvalidNotificationRequest
from src.notification_repository import NotificationRepository

class PushChannel(Base):
    def __init__(self):
        self._channel_type = "push"

    @property
    def channel_type(self):
        return self._channel_type
    
    def send(self, notification_id: str, notification_records: NotificationRepository) -> bool:
        notification_record = notification_records.get_record(notification_id)
        request = notification_record.request

        super().validate_request(request)
        
        if request.channel != self.channel_type:
            raise InvalidNotificationRequest(
                f"Expected channel {self.channel_type!r}, "
                f"received {request.channel!r}"
            )
        
        if not request.device_token:
            raise InvalidNotificationRequest("Does not contain device_token")

        return True