from app.application.services.database_service import DatabaseService


class Clearable:
    def __init__(self):
        self.cleared = False

    def clear(self):
        self.cleared = True


def test_clear_database_clears_vectors_and_metadata():
    vectors = Clearable()
    documents = Clearable()

    DatabaseService(vectors, documents).clear_database()

    assert vectors.cleared is True
    assert documents.cleared is True
