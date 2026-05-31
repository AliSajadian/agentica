'''Chunker'''
from app.config import settings
import structlog
import re
from typing import Optional


logger = structlog.get_logger()


class TextChunker:
    '''Text chunker'''
    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, metadata: Optional[dict] = None) -> list[dict]:
        '''Chunk text with optional metadata.'''
        if metadata is None:
            metadata = {}

        text = self._clean(text)
        chunks = self._split(text)
        logger.info("text_chunked", total_chunks=len(chunks))
        return [
            {
                "text": chunk,
                "metadata": {
                    **metadata,
                    "chunk_index": i,
                    "chunk_total": len(chunks)
                }
            }
            for i, chunk in enumerate(chunks)
        ]

    def _clean(self, text: str) -> str:
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()

    def _split(self, text: str) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            # try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > self.chunk_size * 0.5:
                    end = start + last_period + 1
                    chunk = text[start:end]
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
        return [c for c in chunks if c]


# ── Alternative: LangChain splitters (more features) ─────────────────────────
# from langchain.text_splitter import RecursiveCharacterTextSplitter
#
# class TextChunker:
#     def __init__(self, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP):
#         self.splitter = RecursiveCharacterTextSplitter(
#             chunk_size=chunk_size,
#             chunk_overlap=chunk_overlap,
#             separators=["\n\n", "\n", ".", " ", ""]
#         )
#
#     def chunk(self, text: str, metadata: dict = {}) -> list[dict]:
#         docs = self.splitter.create_documents([text], metadatas=[metadata])
#         return [{"text": d.page_content, "metadata": d.metadata} for d in docs]
# ─────────────────────────────────────────────────────────────────────────────

chunker = TextChunker()
