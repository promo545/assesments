from src.notification_channels.base import Base
from src.strategies.retry_stategy import RetryStrategy
from src.notification_repository import NotificationRepository
from src.factory import NotificationFactory
from src.models import NotificationRequest, DeliveryRecord
from src.notification_processor import Processor
from src.exceptions import TemporaryDeliveryError, PermanentDeliveryError, NotificationNotFound
from src.notification_status import NotificationStatus
import pytest


class CustomMockChannel:
    def __init__(self, attempts_to_be_made: int, should_succeed: bool):
        self.attempt_count = 0
        self.attempts_to_be_made = attempts_to_be_made
        self.should_succeed = should_succeed

    def send(self, notification_id, notification_records):
        self.attempt_count += 1
        
        if not self.should_succeed:
            raise PermanentDeliveryError("Simulated permanent failure")
            
        if self.attempt_count <= self.attempts_to_be_made:
            raise TemporaryDeliveryError("Simulated temporary failure")
            
        return True

class MockFactory:
    def __init__(self, channel_instance):
        self.channel_instance = channel_instance

    def create(self, channel_type):
        return self.channel_instance
    
  

@pytest.fixture()
def channel_factory():
    return NotificationFactory()

@pytest.fixture()
def email_channel(channel_factory : Base):
    factory = channel_factory
    return factory.create('email')
 
@pytest.fixture()
def sms_channel(channel_factory : Base):
    factory = channel_factory
    return factory.create('sms')
 

@pytest.fixture()
def push_channel(channel_factory : Base):
    factory = channel_factory
    return factory.create('push')

@pytest.fixture()
def repository():
    return NotificationRepository()


 