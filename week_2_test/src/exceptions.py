class UnsupportedChannel(Exception):
    pass

class InvalidNotificationRequest(Exception):
    pass

class TemporaryDeliveryError(Exception):
    pass

class PermanentDeliveryError(Exception):
    pass

class NotificationNotFound(Exception):
    pass

class InvalidRetryConfiguration(Exception):
    pass
class InvalidStateTransaction(Exception):
    pass