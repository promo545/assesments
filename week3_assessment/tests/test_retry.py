import pytest
from unittest.mock import Mock, patch
from src.document_processing.models import Document, DocumentStatus, ScanResult
from src.document_processing.processor import DocumentProcessingervice
from src.document_processing.exceptions import ScannerTimeout

def test_process_timeout_retries_three_times_and_fails():
    mock_storage = Mock()
    mock_repo = Mock()
    mock_scanner = Mock()
    processor = DocumentProcessingervice(mock_storage, mock_scanner, mock_repo, Mock(), Mock())
    doc = Document(
        document_id='old_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_123/test.pdf',
        status=DocumentStatus.PENDING,
        created_at=Mock(),
    )
    mock_repo.get.return_value = doc
    mock_scanner.scan.side_effect = ScannerTimeout()
    with patch.object(processor, 'get_file_content', return_value=b'content'):
        with pytest.raises(ScannerTimeout):
            processor.process('old_123')
    assert processor.ATTEMPTS_MADE == 3

def test_process_succeeds_after_retry_attempts():
    mock_storage = Mock()
    mock_repo = Mock()
    mock_scanner = Mock()
    processor = DocumentProcessingervice(mock_storage, mock_scanner, mock_repo, Mock(), Mock())
    doc = Document(
        document_id='old_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_123/test.pdf',
        status=DocumentStatus.PENDING,
        created_at=Mock(),
    )
    mock_repo.get.return_value = doc
    mock_scanner.scan.side_effect = [ScannerTimeout(), ScannerTimeout(), ScanResult.CLEAN]
    with patch.object(processor, 'get_file_content', return_value=b'content'):
        processed = processor.process('old_123')
    assert processor.ATTEMPTS_MADE == 3
    assert processed.status == DocumentStatus.PROCESSED

def test_submit_uses_id_generator_dependency():
    mock_id_gen = Mock()
    mock_id_gen.generate.return_value = "custom-generated-id"
    
    mock_repo = Mock()
    mock_repo.find_by_owner_and_filename.return_value = None
    
    processor = DocumentProcessingervice(
        storage=Mock(),
        scanner=Mock(),
        repo=mock_repo,
        clock=Mock(),
        id_gen=mock_id_gen
    )
    doc = processor.submit("101", "report.pdf", b"content")
    assert doc.document_id == "custom-generated-id"
    mock_id_gen.generate.assert_called_once()