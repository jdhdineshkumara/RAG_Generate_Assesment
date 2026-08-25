from pathlib import Path

from app.domain.entities import ExtractedPage
from app.domain.exceptions import EmptyDocumentError, IndexingError


class PdfPlumberDocumentLoader:
    def __init__(self, max_pages: int) -> None:
        self.max_pages = max_pages

    def load(self, path: Path) -> list[ExtractedPage]:
        try:
            import pdfplumber

            pages: list[ExtractedPage] = []
            with pdfplumber.open(path) as pdf:
                if len(pdf.pages) > self.max_pages:
                    raise IndexingError(
                        f"Document exceeds the maximum of {self.max_pages} pages"
                    )
                for page_number, page in enumerate(pdf.pages, start=1):
                    text = (page.extract_text() or "").strip()
                    if text:
                        pages.append(
                            ExtractedPage(page_number=page_number, text=text)
                        )
        except (EmptyDocumentError, IndexingError):
            raise
        except Exception as exc:
            raise IndexingError("Unable to extract text from the PDF") from exc

        if not pages:
            raise EmptyDocumentError("The PDF does not contain extractable text")
        return pages
