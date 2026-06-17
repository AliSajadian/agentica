from abc import ABC, abstractmethod

from app.models.schemas import SearchResult, NewsResult


class SearchProvider(ABC):

    @abstractmethod
    async def search(
        self,
        query: str,
        count: int = 10
    ) -> list[SearchResult]:
        pass

    @abstractmethod
    async def search_news(
        self,
        query: str,
        count: int = 10
    ) -> list[NewsResult]:
        pass

    @abstractmethod
    async def health(self) -> bool:
        pass