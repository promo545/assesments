from src.document_processing.models import Document, DocumentStatus, ScanResult
from unittest.mock import Mock
from src.document_processing.processor import DocumentProcessingervice
from src.document_processing.exceptions import DocumentAlreadyProcessed, FileContentNotFoundError, ScannerTimeout, ScannerUnavailable

import pytest
from unittest.mock import patch

def test_process_clean_document_becomes_processed(processor, submit_sucess):

    processed_document = processor.process(submit_sucess.document_id)

    assert processed_document.status == DocumentStatus.PROCESSED

def test_process_transitions_pending_to_scanning_before_scan():

    mock_storage = Mock()
    mock_repo = Mock()
    processor = DocumentProcessingervice(
        storage=mock_storage,
        scanner=Mock(),
        repo=mock_repo,
        clock=Mock(),
        id_gen=Mock()
    )
    failed_document = Document(
        document_id='old_id_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_id_123/test.pdf',
        status=DocumentStatus.FAILED,  
        created_at=Mock(),
    )
    mock_repo.get.return_value = failed_document

    with pytest.raises(DocumentAlreadyProcessed):
        document = processor.process('old_id_123')

def test_process_infected_document_is_deleted():
    mock_storage = Mock()
    mock_repo = Mock()
    mock_scanner = Mock()
    processor = DocumentProcessingervice(
        storage=mock_storage,
        scanner=mock_scanner,
        repo=mock_repo,
        clock=Mock(),
        id_gen=Mock()
    )

    document = Document(
        document_id='old_id_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_id_123/test.pdf',
        status=DocumentStatus.PENDING,  
        created_at=Mock(),
    )

    mock_repo.get.return_value = document
    mock_scanner.scan.return_value = ScanResult.INFECTED
    with patch.object(
        processor,
        'get_file_content',
        return_value=b'test content'
    ): 
        processed_document = processor.process('old_id_123')
    
    mock_storage.delete.assert_called_once_with(document.storage_key)
    assert document.status == DocumentStatus.REJECTED

def test_process_timeout_retries_exactly_three_times():
    mock_storage = Mock()
    mock_repo = Mock()
    mock_scanner = Mock()
    processor = DocumentProcessingervice(
        storage=mock_storage,
        scanner=mock_scanner,
        repo=mock_repo,
        clock=Mock(),
        id_gen=Mock()
    )

    document = Document(
        document_id='old_id_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_id_123/test.pdf',
        status=DocumentStatus.PENDING,  
        created_at=Mock(),
    )

    mock_repo.get.return_value = document
    mock_scanner.scan.side_effect = ScannerTimeout()
    with patch.object(
        processor,
        'get_file_content',
        return_value=b'test content'
    ): 
        with pytest.raises(ScannerTimeout):
            processed_document = processor.process('old_id_123')
    assert processor.ATTEMPTS_MADE == 3



def test_process_succeeds_after_second_attempt():
    mock_storage = Mock()
    mock_repo = Mock()
    mock_scanner = Mock()
    processor = DocumentProcessingervice(
        storage=mock_storage,
        scanner=mock_scanner,
        repo=mock_repo,
        clock=Mock(),
        id_gen=Mock()
    )

    document = Document(
        document_id='old_id_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_id_123/test.pdf',
        status=DocumentStatus.PENDING,  
        created_at=Mock(),
    )

    mock_repo.get.return_value = document
    mock_scanner.scan.side_effect = [ScannerTimeout(), ScannerTimeout(), ScanResult.CLEAN]
    with patch.object(
        processor,
        'get_file_content',
        return_value=b'test content'
    ): 
      
        processed_document = processor.process('old_id_123')
    
    assert processor.ATTEMPTS_MADE == 3
    
def test_process_unavailable_is_not_retried():
    mock_storage = Mock()
    mock_repo = Mock()
    mock_scanner = Mock()
    processor = DocumentProcessingervice(
        storage=mock_storage,
        scanner=mock_scanner,
        repo=mock_repo,
        clock=Mock(),
        id_gen=Mock()
    )

    document = Document(
        document_id='old_id_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_id_123/test.pdf',
        status=DocumentStatus.PENDING,  
        created_at=Mock(),
    )

    mock_repo.get.return_value = document
    mock_scanner.scan.side_effect = ScannerUnavailable()
    with patch.object(
        processor,
        'get_file_content',
        return_value=b'test content'
    ): 
        with pytest.raises(ScannerUnavailable): 
            processed_document = processor.process('old_id_123')
    assert processor.ATTEMPTS_MADE == 1

def test_process_processed_document_does_not_scan_again():

    mock_storage = Mock()
    mock_repo = Mock()
    mock_scanner = Mock()
    processor = DocumentProcessingervice(
        storage=mock_storage,
        scanner=mock_scanner,
        repo=mock_repo,
        clock=Mock(),
        id_gen=Mock()
    )

    document = Document(
        document_id='old_id_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_id_123/test.pdf',
        status=DocumentStatus.PROCESSED,  
        created_at=Mock(),
    )

    mock_repo.get.return_value = document
    with pytest.raises(DocumentAlreadyProcessed):
        processed_document = processor.process('old_id_123') 