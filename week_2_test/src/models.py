from dataclasses import dataclass
from src.notification_status import NotificationStatus

@dataclass
class NotificationRequest:

    recipient_id : str
    channel : str
    message : str
    email_address : str | None = None
    phone_number : str | None = None
    device_token : str | None = None

@dataclass
class DeliveryRecord:

    notification_id : str
    request : NotificationRequest
    status : NotificationStatus
    attempt_count : int = 0
    failure_reason : str | None = None