import os

def storage_region() -> str:
    return os.getenv("DOCUMENT_STORAGE_REGION", "local")