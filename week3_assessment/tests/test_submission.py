import pytest
from src.document_processing.exceptions import InvalidFileName, DuplicateDocumentError, OwnerBlockedError
from src.document_processing.models import DocumentStatus

def test_submit_success_saves_metadata_and_uploads(processor, mock_repo, mock_storage):
    mock_repo.find_by_owner_and_filename.return_value = None
    
    doc = processor.submit("101", "report.pdf", b"content")
    
    assert doc.status == DocumentStatus.PENDING
    mock_storage.upload.assert_called_once_with("local/documents/101/test-doc-id/report.pdf", b"content")
    mock_repo.save.assert_called_once_with(doc)

@pytest.mark.parametrize("filename", ["", "   ", "no_extension", "wrong.exe"])
def test_submit_invalid_filename_raises_error(processor, mock_id_gen, filename):
    with pytest.raises(InvalidFileName):
        processor.submit("101", filename, b"content")
    mock_id_gen.generate.assert_not_called()

def test_submit_rejects_duplicate_active_document(processor, mock_repo, pending_document):
    mock_repo.find_by_owner_and_filename.return_value = pending_document
    with pytest.raises(DuplicateDocumentError):
        processor.submit("101", "report.pdf", b"content")

def test_submit_blocks_restricted_owners(processor, mock_owner_policy):
    mock_owner_policy.is_blocked.return_value = True
    with pytest.raises(OwnerBlockedError):
        processor.submit("999", "report.pdf", b"content")

def test_nasty_persistence_failure_retains_original_error(processor, mock_repo, mock_storage):
    mock_repo.find_by_owner_and_filename.return_value = None
    
    mock_repo.save.side_effect = Exception("Database is down")
    mock_storage.delete.side_effect = Exception("Storage is unreachable")
    
    with pytest.raises(Exception) as exc_info:
        processor.submit("101", "test.pdf", b"content")
        
    assert str(exc_info.value) == "Database is down"
    mock_storage.delete.assert_called_once()