from src.document_processing.models import Document, DocumentStatus, FileNameRules, ScanResult, OwnerPolicy
from src.document_processing.ports import StorageClient, VirusScanner, MetadataRepository, Clock, IdGenerator
from src.document_processing.exceptions import (
    DocumentNotFoundError, DuplicateDocumentError, InvalidFileContent, 
    ScannerTimeout, ScannerUnavailable, DocumentAlreadyProcessed, 
    OwnerBlockedError, FileContentNotFoundError
)
from src.document_processing.config import storage_region

class DocumentProcessor:
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
    
    def get_file_content(self, storage_key: str) -> bytes:
        content = self.storage.get_content(storage_key)
        if content is None:
            raise FileContentNotFoundError('File content could not be found')
        return content

    def get_document(self, document_id: str) -> Document:
        document = self.repo.get(document_id)
        if document is None:
            raise DocumentNotFoundError('Document could not be found')
        return document

    def submit(self, owner_id: str, filename: str, content: bytes) -> Document:
        if self.owner_policy.is_blocked(owner_id):
            raise OwnerBlockedError('Owner is restricted from submitting documents')

        FileNameRules.validate_file_name(filename)
    
        if not content or content.isspace():
            raise InvalidFileContent('File content is empty')

        existing_doc = self.repo.find_by_owner_and_filename(owner_id, filename)
        if existing_doc and existing_doc.status not in [DocumentStatus.FAILED, DocumentStatus.REJECTED]:
            raise DuplicateDocumentError('Active document already exists')

        document_id = self.id_gen.generate()
        region = storage_region()
        storage_key = f'{region}/documents/{owner_id}/{document_id}/{filename}'

        self.storage.upload(storage_key, content)

        document = Document(
            document_id=document_id, 
            owner_id=owner_id, 
            filename=filename, 
            storage_key=storage_key, 
            status=DocumentStatus.PENDING, 
            created_at=self.clock.now(),
        )
    
        try:
            self.repo.save(document)
        except Exception as save_error:
            try:
                self.storage.delete(storage_key)
            except Exception:
                pass 
            raise save_error 

        return document
       
    def process(self, document_id: str) -> Document:
        document = self.get_document(document_id)

        if document.status is not DocumentStatus.PENDING:
            raise DocumentAlreadyProcessed('Document is already processed')
        
        document.status = DocumentStatus.SCANNING
        self.repo.save(document)
        
        content = self.get_file_content(document.storage_key)
        scan_result = None

        for attempt in range(1, 4):
            try:
                scan_result = self.scanner.scan(content)
                break  
            except ScannerUnavailable:
                document.status = DocumentStatus.FAILED
                document.failure_reason = 'scanner_unavailable'
                document.processed_at = self.clock.now()
                self.repo.save(document)
                return document  
            except ScannerTimeout:
                if attempt == 3:
                    document.status = DocumentStatus.FAILED
                    document.failure_reason = 'scanner_timeout'
                    document.processed_at = self.clock.now()
                    self.repo.save(document)
                    return document  

        if scan_result == ScanResult.INFECTED:
            self.storage.delete(document.storage_key)
            document.status = DocumentStatus.REJECTED
            document.failure_reason = 'malware_detected'
        elif scan_result == ScanResult.CLEAN:
            document.status = DocumentStatus.PROCESSED
            
        document.processed_at = self.clock.now()
        self.repo.save(document)
        
        return document