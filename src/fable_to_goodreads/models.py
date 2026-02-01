from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Author(BaseModel):
    name: str
    slug: Optional[str] = None

class Genre(BaseModel):
    id: str
    name: str

class SeriesInfo(BaseModel):
    name: str
    position: Optional[str] = ""

class CommunityRatings(BaseModel):
    average: Optional[float] = None
    characters: Optional[float] = None
    plot: Optional[float] = None
    writing: Optional[float] = None
    setting: Optional[float] = None

class Book(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = ""
    authors: List[str] = []
    isbn10: Optional[str] = ""
    isbn13: Optional[str] = ""
    publisher: Optional[str] = ""
    page_count: Optional[int] = 0
    published_date: Optional[str] = ""
    description: Optional[str] = ""
    cover_image: Optional[str] = ""
    genres: List[str] = []
    moods: List[str] = []
    content_warnings: List[str] = []
    tropes: List[str] = []
    series: Optional[SeriesInfo] = None
    
    # User specific data
    status: str = "unread"
    my_rating: Optional[float] = None
    my_review: Optional[str] = ""
    started_at: Optional[str] = ""
    finished_at: Optional[str] = ""
    date_added: Optional[str] = ""
    
    # Community data
    community_ratings: CommunityRatings = Field(default_factory=CommunityRatings)
    
    @property
    def isbn(self) -> str:
        return self.isbn13 or self.isbn10 or ""
