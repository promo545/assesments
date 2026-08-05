from src.notification_channels.base import Base
from src.exceptions import InvalidNotificationRequest
from src.notification_repository import NotificationRepository

class EmailChannel(Base):
    def __init__(self):
        self._channel_type = "email"

    @property
    def channel_type(self):
        return self._channel_type
    
    def send(self, notification_id: str, notification_records: NotificationRepository) -> bool:
        notification_record = notification_records.get_record(notification_id)
        # Correctly extract the request using .request
        request = notification_record.request

        super().validate_request(request)
        
        if request.channel != self.channel_type:
            raise InvalidNotificationRequest(
                f"Expected channel {self.channel_type!r}, "
                f"received {request.channel!r}"
            )
        
        if not request.email_address:
            raise InvalidNotificationRequest("Does not contain email")

        return True


    