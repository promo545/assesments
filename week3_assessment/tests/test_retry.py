from src.document_processing.models import DocumentStatus, ScanResult
from src.document_processing.exceptions import ScannerTimeout

def test_process_timeout_retries_three_times_and_fails_gracefully(processor, mock_scanner, pending_document):
    mock_scanner.scan.side_effect = ScannerTimeout()
    
    doc = processor.process(pending_document.document_id)
    
    assert doc.status == DocumentStatus.FAILED
    assert doc.failure_reason == 'scanner_timeout'
    assert mock_scanner.scan.call_count == 3 

def test_process_succeeds_after_two_timeouts(processor, mock_scanner, pending_document):
    mock_scanner.scan.side_effect = [ScannerTimeout(), ScannerTimeout(), ScanResult.CLEAN]
    
    doc = processor.process(pending_document.document_id)
    
    assert doc.status == DocumentStatus.PROCESSED
    assert mock_scanner.scan.call_count == 3