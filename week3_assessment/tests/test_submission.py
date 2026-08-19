import pytest
from unittest.mock import Mock

from src.document_processing.processor import DocumentProcessingervice
from src.document_processing.ports import LocalClock, LocalIdGenerator, LocalVirusScanner, InMemoryRepository, InMemoryStorageClient
from src.document_processing.exceptions import DocumentNotFoundError, DuplicateDocumentError, InvalidFileContent, InvalidFileName
from src.document_processing.models import Document, DocumentStatus

def test_success_submit(processor):
    filename = 'test.pdf'
    content = b'hello world'

    document = processor.submit('101', filename, content)
    assert document == processor.get_document_by_owner_id_and_filename('101', filename)

def  test_submit_rejects_duplicate_active_document(processor):
    filename = 'test.pdf'
    content =  b'Hello World'

    document = processor.submit('101', filename, content)
    with pytest.raises(DuplicateDocumentError):
        document1 = processor.submit('101', filename, content)
@pytest.mark.parametrize(
    'filename, content', [
        ('', b'file content'),
        (' ', b'file content'),
        ('122463738', b'file content'),
        ('test 1.pdf', b'file content'),
        ('test.exe', b'program')
    ]
)
def test_submit_does_not_generate_id_when_file_validation_fails(processor, filename, content):

    with pytest.raises(InvalidFileName):
        document = processor.submit('101', filename, content)
@pytest.mark.parametrize(
    'filename, content', [
        ('test.pdf', b' '),
        ('test.pdf', b''),
    ]
)
def test_submit_does_not_generate_id_when_content_validation_fails(processor, filename, content):

    with pytest.raises(InvalidFileContent):
        document = processor.submit('101', filename, content)

def test_submit_removes_uploaded_file_when_metadata_save_fails():

    mock_storage = Mock()
    mock_repo = Mock()
    mock_repo.find_by_owner_and_filename.return_value = None
    mock_repo.save.side_effect = Exception('Database save failed')

    processor = DocumentProcessingervice(
        storage=mock_storage,
        scanner=Mock(),
        repo=mock_repo,
        clock=Mock(),
        id_gen=Mock()
    )

    with pytest.raises(Exception, match= 'Database save failed'):
        processor.submit('101', 'test.pdf', b'file data')
    
    mock_storage.upload.assert_called_once()
    mock_storage.delete.assert_called_once()

def test_submit_allows_resubmission_after_failure():

    mock_storage = Mock()
    mock_repo = Mock()

    failed_document = Document(
        document_id='old_id_123',
        owner_id='101',
        filename='test.pdf',
        storage_key='documents/101/old_id_123/test.pdf',
        status=DocumentStatus.FAILED,  
        created_at=Mock(),
    )

    mock_repo.find_by_owner_and_filename.return_value = failed_document

    processor = DocumentProcessingervice(
        storage=mock_storage,
        scanner=Mock(),
        repo=mock_repo,
        clock=Mock(),
        id_gen=Mock()
    )

    new_document = processor.submit('101', 'test.pdf', b'file data')

    mock_storage.upload.assert_called_once()
    mock_repo.save.assert_called_once()
    
    assert new_document.status == DocumentStatus.PENDING


    
