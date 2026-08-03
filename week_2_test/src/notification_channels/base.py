from abc import ABC, abstractmethod

from src.models import NotificationRequest, DeliveryRecord
from  src.exceptions import InvalidNotificationRequest
from src.notification_repository import NotificationRepository

class Base(ABC):

    @abstractmethod
    def send(self, 
             notification_id : str, 
             notification_records : NotificationRepository) -> bool:
        pass

    def validate_request(self, notification_request : NotificationRequest) -> bool:
        
        recipient_id = notification_request.recipient_id
        channel = notification_request.channel
        message = notification_request.message

        if recipient_id == None or recipient_id == "":
            raise InvalidNotificationRequest("Does not contain recipient_id")
        if channel == None or channel == "":
            raise InvalidNotificationRequest("Does not contain channel")
        if message == None or message == "":
            raise InvalidNotificationRequest("Does not contain message")
        
        return True
