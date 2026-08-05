from abc import ABC, abstractmethod
from typing import Callable, Any, Tuple

class RetryStrategy(ABC):

    @abstractmethod
    def execute(self, operation : Callable[[], Any]) -> Tuple[Any, int]:
        pass
