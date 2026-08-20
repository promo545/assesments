import pytest
from unittest.mock import Mock
from datetime import datetime
from src.document_processing.processor import DocumentProcessor
from src.document_processing.ports import (
    MetadataRepository, StorageClient, Clock, IdGenerator, VirusScanner
)
from src.document_processing.models import Document, DocumentStatus, OwnerPolicy

@pytest.fixture
def mock_repo():
    return Mock(spec=MetadataRepository)

@pytest.fixture
def mock_storage():
    return Mock(spec=StorageClient)

@pytest.fixture
def mock_clock():
    clock = Mock(spec=Clock)
    clock.now.return_value = datetime(2026, 1, 1)
    return clock

@pytest.fixture
def mock_id_gen():
    id_gen = Mock(spec=IdGenerator)
    id_gen.generate.return_value = "test-doc-id"
    return id_gen

@pytest.fixture
def mock_scanner():
    return Mock(spec=VirusScanner)

@pytest.fixture
def mock_owner_policy():
    policy = Mock(spec=OwnerPolicy)
    policy.is_blocked.return_value = False
    return policy

@pytest.fixture
def processor(mock_storage, mock_scanner, mock_repo, mock_clock, mock_id_gen, mock_owner_policy):
    return DocumentProcessor(
        storage=mock_storage,
        scanner=mock_scanner,
        repo=mock_repo,
        clock=mock_clock,
        id_gen=mock_id_gen,
        owner_policy=mock_owner_policy
    )

@pytest.fixture
def pending_document(mock_repo, mock_storage):
    doc = Document(
        document_id="test-doc-id",
        owner_id="101",
        filename="report.pdf",
        storage_key="local/documents/101/test-doc-id/report.pdf",
        status=DocumentStatus.PENDING,
        created_at=datetime(2026, 1, 1)
    )
    
    mock_repo.get.return_value = doc
    mock_repo.find_by_owner_and_filename.return_value = doc
    mock_storage.get_content.return_value = b"file content"
    
    return doc