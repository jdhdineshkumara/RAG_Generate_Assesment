class DomainError(Exception):
    code = "domain_error"


class CollectionNotFoundError(DomainError):
    code = "collection_not_found"


class UnsupportedFileError(DomainError):
    code = "unsupported_file"


class FileTooLargeError(DomainError):
    code = "file_too_large"


class EmptyDocumentError(DomainError):
    code = "empty_document"


class DuplicateDocumentError(DomainError):
    code = "duplicate_document"


class IndexingError(DomainError):
    code = "indexing_failed"


class QueryError(DomainError):
    code = "query_failed"
