import pytest
from src.document_processing.ports import InMemoryRepository, InMemoryStorageClient, LocalClock, LocalIdGenerator, LocalVirusScanner
from src.document_processing.processor import DocumentProcessingervice

@pytest.fixture
def inmemoryrepository():
    return InMemoryRepository()

@pytest.fixture
def inmemorystorageclient():
    return InMemoryStorageClient()

@pytest.fixture
def localclock():
    return LocalClock()

@pytest.fixture
def localidgenerator():
    return LocalIdGenerator()

@pytest.fixture
def localvirusscanner():
    return LocalVirusScanner()

@pytest.fixture
def processor(inmemoryrepository, inmemorystorageclient, localclock, localidgenerator, localvirusscanner):
    return DocumentProcessingervice(
        inmemorystorageclient,
        localvirusscanner,
        inmemoryrepository,
        localclock,
        localidgenerator
    )

@pytest.fixture
def submit_sucess(processor):
    filename = 'test.pdf'
    content = b'hello world'
    document = processor.submit('101', filename, content)
    return document