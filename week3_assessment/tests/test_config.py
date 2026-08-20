from src.document_processing.config import storage_region

def test_storage_region_defaults_to_local(monkeypatch):
    monkeypatch.delenv("DOCUMENT_STORAGE_REGION", raising=False)
    assert storage_region() == "local"

def test_storage_region_uses_env_variable(monkeypatch):
    monkeypatch.setenv("DOCUMENT_STORAGE_REGION", "eu-central-1")
    assert storage_region() == "eu-central-1"