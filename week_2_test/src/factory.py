from src.notification_channels.base import Base
from src.notification_channels.email_channel import EmailChannel
from src.notification_channels.push_channel import PushChannel
from src.notification_channels.sms_channel import SMSChannel

from src.exceptions import UnsupportedChannel

class NotificationFactory():

    __supported_channels = ['email', 'push', 'sms']
    __channel_map : dict[str, type[Base]]= {
        'email' : EmailChannel,
        'push' : PushChannel,
        'sms' : SMSChannel
    }

    @classmethod
    def create(cls, channel_type : str) -> Base:
            
        try:
            channel_class = cls.__channel_map[channel_type]
        except KeyError as exc:
            raise UnsupportedChannel(
                f"Unsupported channel: {channel_type}"
            ) from exc

        return channel_class()

