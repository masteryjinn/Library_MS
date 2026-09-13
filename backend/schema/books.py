# --- Pydantic Схеми ---
from openai import BaseModel
from pydantic import ConfigDict
from typing import List, Optional


class BookBase(BaseModel):
    title: str
    author: str
    year: int
    publisher: Optional[str] = None
    location: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    pass

class BookOut(BookBase):
    id: int
    available: bool = True

    model_config = ConfigDict(from_attributes=True)

class BooksPaginatedResponse(BaseModel):
    books: List[BookOut]
    total: int
    total_pages: int
