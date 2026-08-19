from src.document_processing.models import Document, DocumentStatus, FileNameRules, ScanResult, OwnerPolicy
from src.document_processing.ports import StorageClient, VirusScanner, MetadataRepository, Clock, IdGenerator
from src.document_processing.exceptions import (
    DocumentNotFoundError, DuplicateDocumentError, InvalidFileContent, ScannerTimeout, ScannerUnavailable, DocumentAlreadyProcessed, OwnerBlockedError
)

from uuid import uuid4

class DocumentProcessingervice:
    def __init__(
        self,
        storage: StorageClient,
        scanner: VirusScanner,
        repo: MetadataRepository,
        clock: Clock,
        id_gen: IdGenerator,
        owner_policy: OwnerPolicy = None
    ):
        self.storage = storage
        self.scanner = scanner
        self.repo = repo
        self.clock = clock
        self.id_gen = id_gen
        self.owner_policy = owner_policy or OwnerPolicy()
        self.ATTEMPTS_MADE = 0
    
    def get_file_content(self, storage_key: str):
        content = self.storage.get_content(storage_key)
        if content is None:
            raise FileContentNotFoundError('File content could not be found')
        return content

    def get_document(self, document_id: str):
        document = self.repo.get(document_id)
        if document is None:
            raise DocumentNotFoundError('Document could not be found')
        return document

    def get_document_by_owner_id_and_filename(self, owner_id: str, filename: str):
        document = self.repo.find_by_owner_and_filename(owner_id, filename)
        if document is None:
            raise DocumentNotFoundError('Document could not be found')
        return document

    def submit(self, owner_id: str, filename: str, content: bytes) -> Document:
        if self.owner_policy.is_blocked(owner_id):
            raise OwnerBlockedError('Owner is restricted from submitting documents')

        FileNameRules.validate_file_name(filename)
    
        if not content or content.isspace():
            raise InvalidFileContent('File content is empty')

        try:
            document = self.get_document_by_owner_id_and_filename(owner_id, filename)
            if document.status not in [DocumentStatus.FAILED, DocumentStatus.REJECTED]:
                raise DuplicateDocumentError('Document already exists')
        except DocumentNotFoundError:
            pass 

        document_id = self.id_gen.generate()
        storage_key = f'documents/{owner_id}/{document_id}/{filename}'

        self.storage.upload(storage_key, content)

        document = Document(
            document_id=document_id, 
            owner_id=owner_id, 
            filename=filename, 
            storage_key=storage_key, 
            status=DocumentStatus.PENDING, 
            created_at=self.clock.now(),
            processed_at=None,
            failure_reason=None
        )
    
        try:
            self.repo.save(document)
        except Exception as error:
            self.storage.delete(storage_key)
            raise error 

        return document
       
    def process(self, document_id: str):
        MAX_ATTEMPTS = 3

        document = self.repo.get(document_id)

        if document.status is not DocumentStatus.PENDING:
            raise DocumentAlreadyProcessed('Document is in scanning or already processed')
        
        document.status = DocumentStatus.SCANNING
        content = self.get_file_content(document.storage_key)
        status = None

        for i in range(1, 4):
            try:
                status = self.scanner.scan(content)
            except (ScannerTimeout, ScannerUnavailable) as e:
                if isinstance(e, ScannerUnavailable):
                    document.status = DocumentStatus.FAILED
                    document.failure_reason = 'scanner_unavailable'
                    document.processed_at = self.clock.now()
                    self.ATTEMPTS_MADE = 1
                    raise e
                if i == 3:
                    document.status = DocumentStatus.FAILED
                    document.failure_reason = 'scanner_timeout'
                    document.processed_at = self.clock.now()
                    self.ATTEMPTS_MADE = i
                    raise e
            
        if status == ScanResult.INFECTED:
            self.storage.delete(document.storage_key)
            document.status = DocumentStatus.REJECTED
            document.failure_reason = 'malware_detected'
            document.processed_at = self.clock.now()

        
        elif status == ScanResult.CLEAN:
            document.status = DocumentStatus.PROCESSED
            document.processed_at = self.clock.now()
        
        self.ATTEMPTS_MADE = i
        
        return document