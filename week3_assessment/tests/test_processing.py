from src.document_processing.models import DocumentStatus, ScanResult
from unittest.mock import call

def test_process_clean_document_transitions_and_saves(processor, mock_scanner, mock_repo, pending_document):
    mock_scanner.scan.return_value = ScanResult.CLEAN
    
    doc = processor.process(pending_document.document_id)
    
    assert doc.status == DocumentStatus.PROCESSED
    mock_scanner.scan.assert_called_once()
    
    mock_repo.save.assert_has_calls([
        call(pending_document), 
        call(pending_document)  
    ])

def test_process_infected_document_is_rejected_and_deleted(processor, mock_scanner, mock_storage, pending_document):
    mock_scanner.scan.return_value = ScanResult.INFECTED
    
    doc = processor.process(pending_document.document_id)
    
    assert doc.status == DocumentStatus.REJECTED
    assert doc.failure_reason == "malware_detected"
    mock_storage.delete.assert_called_once_with(pending_document.storage_key)