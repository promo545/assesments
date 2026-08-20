import pytest
from src.document_processing.exceptions import DocumentNotFoundError, DocumentAlreadyProcessed, ScannerUnavailable
from src.document_processing.models import DocumentStatus

def test_process_unknown_document_raises_not_found(processor, mock_repo):
    mock_repo.get.return_value = None
    with pytest.raises(DocumentNotFoundError):
        processor.process("does-not-exist")

def test_process_already_processed_document_raises_error(processor, pending_document, mock_scanner):
    pending_document.status = DocumentStatus.PROCESSED
    with pytest.raises(DocumentAlreadyProcessed):
        processor.process(pending_document.document_id)
    mock_scanner.scan.assert_not_called()

def test_process_scanner_unavailable_fails_immediately_no_retry(processor, mock_scanner, pending_document):
    mock_scanner.scan.side_effect = ScannerUnavailable()
    
    doc = processor.process(pending_document.document_id)
    
    assert doc.status == DocumentStatus.FAILED
    assert doc.failure_reason == 'scanner_unavailable'
    assert mock_scanner.scan.call_count == 1