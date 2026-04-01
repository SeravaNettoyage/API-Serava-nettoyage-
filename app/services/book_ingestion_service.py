from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from app.services.chunking_service import ChunkingService
from app.services.supabase_client import SupabaseService


class BookIngestionService:
    def __init__(self, supabase: SupabaseService):
        self.supabase = supabase
        self.chunker = ChunkingService()

    def _extract_pdf_text(self, file_bytes: bytes) -> str:
        reader = PdfReader(BytesIO(file_bytes))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or '')
        return '\n\n'.join(parts).strip()

    def ingest_pdf(self, filename: str, file_bytes: bytes, title: str | None = None, author: str | None = None) -> tuple[str, int]:
        text = self._extract_pdf_text(file_bytes)
        if not text:
            raise ValueError('Aucun texte exploitable extrait du PDF.')

        book = self.supabase.insert_book(
            {
                'title': title or filename,
                'author': author,
                'source_type': 'pdf',
                'filename': filename,
                'status': 'parsed',
            }
        )
        book_id = book['id']

        chunks = self.chunker.chunk_text(text)
        rows = []
        for idx, chunk in enumerate(chunks):
            rows.append(
                {
                    'book_id': book_id,
                    'chunk_index': idx,
                    'content': chunk,
                    'content_type': 'raw_text',
                    'source_ref': filename,
                }
            )
        self.supabase.insert_book_chunks(rows)
        self.supabase.update_book_status(book_id, 'chunked')
        return book_id, len(chunks)
