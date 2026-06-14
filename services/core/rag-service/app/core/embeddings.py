'''Embed '''
from fastembed import TextEmbedding
from app.config import settings
import structlog

logger = structlog.get_logger()

# ── CPU implementation (active) ──────────────────────────────────────────────
# Uses fastembed — lightweight, no CUDA required
# Model runs on CPU, good for development and low-resource environments

class EmbeddingService:
    '''
    Embed service
    '''
    def __init__(self):
        self.model = TextEmbedding(
            model_name=settings.EMBEDDING_MODEL
        )
        logger.info("embedding_model_loaded", model=settings.EMBEDDING_MODEL, device="cpu")

    def embed(self, texts: list[str]) -> list[list[float]]:
        '''Embed'''
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]

    def embed_single(self, text: str) -> list[float]:
        '''Embed single'''
        return self.embed([text])[0]


# ── GPU alternative (sentence-transformers + CUDA) ───────────────────────────
# Uncomment below and comment out the class above when GPU is available
#
# from sentence_transformers import SentenceTransformer
# import torch
#
# class EmbeddingService:
#     def __init__(self):
#         self.device = settings.EMBEDDING_DEVICE  # "cuda" or "cpu"
#         self.model = SentenceTransformer(
#             settings.EMBEDDING_MODEL,
#             device=self.device
#         )
#         logger.info(
#             "embedding_model_loaded",
#             model=settings.EMBEDDING_MODEL,
#             device=self.device,
#             cuda_available=torch.cuda.is_available()
#         )
#
#     def embed(self, texts: list[str]) -> list[list[float]]:
#         embeddings = self.model.encode(
#             texts,
#             batch_size=32,
#             show_progress_bar=False,
#             convert_to_numpy=True
#         )
#         return embeddings.tolist()
#
#     def embed_single(self, text: str) -> list[float]:
#         return self.embed([text])[0]
# ─────────────────────────────────────────────────────────────────────────────

# Singleton
embedding_service = EmbeddingService()