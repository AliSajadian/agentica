'''Ingest'''
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.schemas import IngestRequest, IngestResponse
from app.core.embeddings import embedding_service
from app.core.chunker import chunker
from app.services.qdrant import qdrant_service
from app.utils.logger import get_logger
import pypdf
import io

router = APIRouter()
logger = get_logger(__name__)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_text(request: IngestRequest):
    '''Ingest text'''
    try:
        logger.info("ingest_started", source=request.source)

        # chunk
        chunks = chunker.chunk(request.text, metadata={
            "source": request.source or "unknown",
            **(request.metadata or {})
        })

        # embed
        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed(texts)

        # store in qdrant
        await qdrant_service.upsert(chunks, embeddings)

        logger.info("ingest_completed", chunks=len(chunks))
        return IngestResponse(chunks_created=len(chunks))

    except Exception as e:
        logger.error("ingest_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    '''Ingest file'''
    try:
        logger.info("ingest_file_started", filename=file.filename)

        content = await file.read()

        # extract text based on file type
        if file.filename.endswith(".pdf"):
            text = _extract_pdf(content)
        elif file.filename.endswith(".txt"):
            text = content.decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Only .pdf and .txt supported")

        request = IngestRequest(
            text=text,
            source=file.filename,
            metadata={"filetype": file.content_type}
        )
        return await ingest_text(request)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("ingest_file_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


def _extract_pdf(content: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() for page in reader.pages)
