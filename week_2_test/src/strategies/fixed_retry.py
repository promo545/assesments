import time
from typing import Callable, Tuple, Any
from src.strategies.retry_strategy import RetryStrategy
from src.exceptions import InvalidRetryConfiguration, TemporaryDeliveryError

class FixedRetry(RetryStrategy):
    strategy_type = 'fixed_retry'

    def __init__(self, max_attempts: int, delay_seconds: int):
        if max_attempts <= 0:
            raise InvalidRetryConfiguration("Must be greater than 0")
        if delay_seconds < 0:
            raise InvalidRetryConfiguration("Must be at least 0")

        self.max_attempts = max_attempts
        self.delay_seconds = delay_seconds
        self._attempt_count = 0

    @property
    def attempt_count(self) -> int:
        return self._attempt_count

    def execute(self, operation: Callable) -> Tuple[Any, int]:
        self._attempt_count = 0

        for _ in range(self.max_attempts):
            self._attempt_count += 1
            try:
                return (operation(), self._attempt_count)
            except TemporaryDeliveryError:
                if self._attempt_count == self.max_attempts:
                    raise
                time.sleep(self.delay_seconds)