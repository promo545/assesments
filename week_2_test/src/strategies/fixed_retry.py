from src.strategies.retry_stategy import RetryStrategy
from typing import Callable
import time
from src.exceptions import InvalidRetryConfiguration, TemporaryDeliveryError

class FixedRetry(RetryStrategy):

    strategy_type = 'fixed_retry'

    def __init__(self, max_attempts : int, delay_seconds : int):
        if max_attempts <= 0:
            raise InvalidRetryConfiguration("Must be greater than 0")
        if delay_seconds < 0:
            raise InvalidRetryConfiguration("Must be atleast 0")


        self.max_attempts = max_attempts
        self.delay_seconds = delay_seconds

    def execute(self, operation : Callable):
        
        attempt_count = 0

        for i in range(0, self.max_attempts + 1):
            attempt_count += 1            
            try:
                return (operation(), attempt_count)

            except TemporaryDeliveryError:

                if attempt_count == self.max_attempts:
                    raise
                time.sleep(self.delay_seconds)