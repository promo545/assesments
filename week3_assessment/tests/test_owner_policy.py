import pytest
from unittest.mock import Mock
from src.document_processing.exceptions import OwnerBlockedError
from src.document_processing.processor import DocumentProcessingervice
from src.document_processing.models import OwnerPolicy

def test_owner_policy_evaluates_blocked_status_correctly():
    policy = OwnerPolicy(blocked_owners=['999', '888'])
    assert policy.is_blocked('999') is True
    assert policy.is_blocked('101') is False

def test_submit_raises_owner_blocked_error_when_policy_rejects_owner():
    mock_policy = Mock(spec=OwnerPolicy)
    mock_policy.is_blocked.return_value = True

    processor = DocumentProcessingervice(
        storage=Mock(),
        scanner=Mock(),
        repo=Mock(),
        clock=Mock(),
        id_gen=Mock(),
        owner_policy=mock_policy
    )

    with pytest.raises(OwnerBlockedError, match='Owner is restricted from submitting documents'):
        processor.submit('999', 'test.pdf', b'content')