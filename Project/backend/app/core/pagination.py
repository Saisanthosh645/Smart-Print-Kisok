from typing import Generic, List, TypeVar
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PageMetadata(BaseModel):
    total: int
    page: int
    size: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    metadata: PageMetadata


async def paginate(db: AsyncSession, query, page: int = 1, size: int = 20) -> dict:
    if page < 1:
        page = 1
    if size < 1:
        size = 20
    elif size > 100:
        size = 100

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    offset = (page - 1) * size
    paginated_query = query.offset(offset).limit(size)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    pages = (total + size - 1) // size if total > 0 else 0

    return {
        "items": items,
        "metadata": {
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        },
    }
