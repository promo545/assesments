from typing import Protocol
from datetime import datetime
import uuid

from src.document_processing.models import Document, ScanResult
class MetadataRepository(Protocol):

    def save(document: Document):
        ...
    
    def get(document_id: str):
        ...

    def find_by_owner_and_filename(owner_id: str, filename: str):
        ...

class StorageClient(Protocol):

    def upload(storage_key: str, content : bytes):
        ...
    def delete(storage_key: str):
        ...
    def get_content(storage_key: str):
        ...

class VirusScanner(Protocol):
    def scan(content : bytes):
        ...

class Clock(Protocol):

    def now():
        ...

class IdGenerator(Protocol):
    def generate():
        ...

class InMemoryRepository:

    def __init__(self):
        self.documents = {}
        self.documents_by_owner_and_filename = {}
    
    def save(self, document: Document):
        self.documents[document.document_id] = document
        '''
        Keeping it simple as it a fact that until the previous record is not rejected or failed user cannot upload again; so its safe to overwrite 
        '''
        self.documents_by_owner_and_filename[f'{document.owner_id}_{document.filename}'] = document.document_id

    def get(self, document_id: str):
        document = self.documents.get(document_id)
        return document

    def find_by_owner_and_filename(self, owner_id: str, filename: str):
        document_id = self.documents_by_owner_and_filename.get(f'{owner_id}_{filename}')
        return self.get(document_id)
        

class InMemoryStorageClient:

    def __init__(self):
        self.contents = {}

    def upload(self, storage_key: str, content: bytes):
        self.contents[storage_key] = content 

    def delete(self, storage_key: str):
        del self.contents[storage_key]

    def get_content(self, storage_key: str):
        content = self.contents.get(storage_key)
        return content

class LocalVirusScanner:
    
    def scan(self, content: bytes):
        return ScanResult.CLEAN
   
class LocalClock:
    def now(self):
        return datetime.now()

class LocalIdGenerator:
    def generate(self):
        return str(uuid.uuid4())     
