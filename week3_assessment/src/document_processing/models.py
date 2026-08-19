from enum import Enum, auto
from datetime import datetime
from dataclasses import dataclass

from src.document_processing.exceptions import InvalidFileName

class DocumentStatus(Enum):
    
    PENDING = auto()
    SCANNING = auto()
    PROCESSED = auto()
    REJECTED = auto()
    FAILED = auto()

class ScanResult(Enum):
    CLEAN = auto()
    INFECTED = auto()
@dataclass
class Document:
    document_id : str
    owner_id : str
    filename: str
    storage_key: str
    status: DocumentStatus
    created_at: datetime
    processed_at: datetime | None = None
    failure_reason: str | None = None

class FileNameRules:

    @staticmethod
    def validate_file_name(filename: str) -> bool:
        allowed_extensions = ['pdf', 'txt', 'csv']


        def has_white_space(filename : str):
            return any(c.isspace() for c in filename)

        
        if not isinstance(filename, str):
            raise InvalidFileName('Filename is not of type string')

        if filename is None or filename == "":
            raise InvalidFileName('Filename cannot be empty')
        
        if has_white_space(filename):
            raise InvalidFileName('Filename must not have whitespaces')
        
        if len(filename) > 255:
            raise InvalidFileName('Name cannot have more than 255 chars')
        
        extension = filename.rsplit('.', 1)[-1].lower()

        if extension not in allowed_extensions:
            raise InvalidFileName(f'File extension not supported; allowed extension = {allowed_extensions}')

        return True  


class OwnerPolicy:
    def __init__(self, blocked_owners: list[str] = None):
        self.blocked_owners = set(blocked_owners or [])

    def is_blocked(self, owner_id: str) -> bool:
        return owner_id in self.blocked_owners