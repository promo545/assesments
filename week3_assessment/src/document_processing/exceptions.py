class DuplicateDocumentError(Exception):
    pass

class DocumentNotFoundError(Exception):
    pass

class ScannerTimeout(Exception):
    pass

class ScannerUnavailable(Exception):
    pass

class InvalidFileName(Exception):
    pass

class InvalidFileContent(Exception):
    pass

class DocumentAlreadyProcessed(Exception):
    pass

class FileContentNotFoundError(Exception):
    pass

class OwnerBlockedError(Exception):
    pass