import re

from app.core.settings import settings


class ChunkingService:
    def chunk_text(self, text: str, max_chars: int | None = None, overlap: int | None = None) -> list[str]:
        max_chars = max_chars or settings.chunk_max_chars
        overlap = overlap or settings.chunk_overlap_chars
        cleaned = re.sub(r'\n{3,}', '\n\n', text).strip()
        if not cleaned:
            return []

        chunks: list[str] = []
        start = 0
        text_len = len(cleaned)

        while start < text_len:
            end = min(start + max_chars, text_len)
            chunk = cleaned[start:end]
            if end < text_len:
                last_break = max(chunk.rfind('\n\n'), chunk.rfind('. '), chunk.rfind('; '))
                if last_break > 500:
                    end = start + last_break + 1
                    chunk = cleaned[start:end]
            chunks.append(chunk.strip())
            if end >= text_len:
                break
            start = max(end - overlap, start + 1)
        return [c for c in chunks if c]
