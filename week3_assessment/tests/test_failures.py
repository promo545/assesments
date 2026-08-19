import pytest
from unittest.mock import Mock, patch
from src.document_processing.models import Document, DocumentStatus, ScanResult
from src.document_processing.processor import DocumentProcessingervice
from src.document_processing.exceptions import DocumentAlreadyProcessed, ScannerUnavailable, InvalidFileName, InvalidFileContent

def test_process_failed_document_raises_already_processed():
    mock_repo = Mock()
    processor = DocumentProcessingervice(Mock(), Mock(), mock_repo, Mock(), Mock())
    failed_doc = Document(
        document_id='old_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_123/test.pdf',
        status=DocumentStatus.FAILED,
        created_at=Mock(),
    )
    mock_repo.get.return_value = failed_doc
    with pytest.raises(DocumentAlreadyProcessed):
        processor.process('old_123')

def test_process_scanner_unavailable_fails_immediately():
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
    mock_scanner.scan.side_effect = ScannerUnavailable()
    with patch.object(processor, 'get_file_content', return_value=b'content'):
        with pytest.raises(ScannerUnavailable):
            processor.process('old_123')
    assert processor.ATTEMPTS_MADE == 1

def test_submit_invalid_filename_raises_error(processor):
    with pytest.raises(InvalidFileName):
        processor.submit('101', '', b'content')

def test_submit_invalid_content_raises_error(processor):
    with pytest.raises(InvalidFileContent):
        processor.submit('101', 'test.pdf', b'   ')

def test_patch_object_on_processor_method():
    processor = DocumentProcessingervice(Mock(), Mock(), Mock(), Mock(), Mock())
    with patch.object(processor, 'get_document', return_value="custom_doc"):
        result = processor.get_document("any_id")
        assert result == "custom_doc"