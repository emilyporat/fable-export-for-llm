from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Author(BaseModel):
    name: str
    slug: Optional[str] = None
    biography: Optional[str] = ""

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

class ReadingProgress(BaseModel):
    current_percentage: Optional[float] = None
    current_page: Optional[int] = None
    page_count: Optional[int] = None
    status: Optional[str] = None

class Book(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = ""
    authors: List[Author] = []
    isbn: Optional[str] = ""
    isbn10: Optional[str] = ""
    isbn13: Optional[str] = ""
    display_isbn: Optional[str] = ""
    publisher: Optional[str] = ""
    page_count: Optional[int] = None
    chapter_count: Optional[int] = None
    published_date: Optional[str] = ""
    description: Optional[str] = ""
    cover_image: Optional[str] = ""
    cover_image_small: Optional[str] = ""
    background_color: Optional[str] = ""
    fable_url: Optional[str] = ""
    source: Optional[str] = ""
    price_usd: Optional[str] = ""
    non_fiction: Optional[bool] = None
    family_id: Optional[int] = None
    is_free: Optional[bool] = None
    can_purchase: Optional[bool] = None
    can_download: Optional[bool] = None
    store_availability: Optional[str] = ""
    is_out_of_catalog: Optional[bool] = None
    genres: List[str] = []
    subjects: List[str] = []
    moods: List[str] = []
    content_warnings: List[str] = []
    tropes: List[str] = []
    series: Optional[SeriesInfo] = None

    # User specific data
    list_name: Optional[str] = ""
    status: str = "unread"
    my_rating: Optional[float] = None
    my_review: Optional[str] = ""
    started_at: Optional[str] = ""
    started_at_date_type: Optional[str] = ""
    finished_at: Optional[str] = ""
    finished_at_date_type: Optional[str] = ""
    date_added: Optional[str] = ""
    favorite: Optional[bool] = None
    sort_value: Optional[int] = None
    reading_progress: Optional[ReadingProgress] = None

    # Community data
    community_ratings: CommunityRatings = Field(default_factory=CommunityRatings)
