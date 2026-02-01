import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx
from .models import Book, SeriesInfo, CommunityRatings

logger = logging.getLogger(__name__)

class FableClient:
    BASE_URL = "https://api.fable.co/api"
    
    def __init__(self, user_id: str, auth_token: str):
        self.user_id = user_id
        self.auth_token = auth_token.replace("JWT ", "").replace("Token ", "")
        self.headers = {
            "Authorization": f"JWT {self.auth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "FableExporter/2.0 (Modern Modern Modern)",
        }
        self.raw_dir = Path("raw_data")
        self.raw_dir.mkdir(exist_ok=True)

    def _save_raw(self, name: str, data: Any):
        path = self.raw_dir / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    async def fetch_reviews(self) -> Dict[str, Dict[str, Any]]:
        reviews = {}
        async with httpx.AsyncClient(headers=self.headers) as client:
            offset = 0
            while True:
                url = f"{self.BASE_URL}/v2/users/{self.user_id}/reviews/?limit=50&offset={offset}"
                resp = await client.get(url)
                if resp.status_code == 404:
                    url = f"{self.BASE_URL}/users/{self.user_id}/reviews/?limit=50&offset={offset}"
                    resp = await client.get(url)
                
                resp.raise_for_status()
                data = resp.json()
                self._save_raw(f"reviews_{offset}", data)
                
                results = data.get("results", [])
                for r in results:
                    book_id = r.get("book", {}).get("id")
                    if book_id:
                        reviews[book_id] = r
                
                if not results or len(results) < 50:
                    break
                offset += 50
        return reviews

    async def fetch_lists(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(headers=self.headers) as client:
            url = f"{self.BASE_URL}/v2/users/{self.user_id}/book_lists"
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            self._save_raw("user_lists", data)
            return data.get("results", [])

    async def fetch_books_from_list(self, list_id: str, list_name: str) -> List[Dict[str, Any]]:
        books = []
        async with httpx.AsyncClient(headers=self.headers) as client:
            offset = 0
            while True:
                url = f"{self.BASE_URL}/v2/users/{self.user_id}/book_lists/{list_id}/books?limit=100&offset={offset}"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                self._save_raw(f"list_{list_name}_{offset}", data)
                
                results = data.get("results", [])
                books.extend(results)
                
                if not results or len(results) < 100:
                    break
                offset += 100
        return books

    def parse_book(self, item: Dict[str, Any], reviews: Dict[str, Any]) -> Book:
        raw_book = item.get("book", item)
        book_id = raw_book.get("id")
        review = reviews.get(book_id, {})
        
        # Series
        series_sets = raw_book.get("bookseries_set", [])
        series = None
        if series_sets:
            s = series_sets[0]
            series = SeriesInfo(
                name=s.get("book_series", {}).get("name", ""),
                position=str(s.get("position", ""))
            )
            
        # Ratings
        calc = raw_book.get("calculated_fields", {})
        comm_ratings = CommunityRatings(
            average=raw_book.get("review_average"),
            characters=calc.get("characters_rating_average"),
            plot=calc.get("plot_rating_average"),
            writing=calc.get("writing_style_rating_average"),
            setting=calc.get("setting_rating_average")
        )
        
        # ISBN
        isbn = raw_book.get("isbn", "")
        isbn10 = isbn if len(isbn) == 10 else ""
        isbn13 = isbn if len(isbn) == 13 else ""
        
        # Status
        status = item.get("status") or raw_book.get("status") or "unread"
        
        # Dates
        finished_at = raw_book.get("finished_reading_at") or ""
        if status.lower() in ["finished", "read"] and not finished_at:
            finished_at = review.get("created_at") or review.get("updated_at") or ""

        return Book(
            id=book_id,
            title=raw_book.get("title", ""),
            subtitle=raw_book.get("subtitle", ""),
            authors=[a.get("name") for a in raw_book.get("authors", [])],
            isbn10=isbn10,
            isbn13=isbn13,
            publisher=raw_book.get("imprint") or raw_book.get("publisher") or "",
            page_count=raw_book.get("page_count"),
            published_date=raw_book.get("published_date"),
            description=raw_book.get("description"),
            cover_image=raw_book.get("cover_image"),
            genres=[g.get("name") for g in raw_book.get("genres", [])],
            moods=raw_book.get("storygraph_tags", {}).get("moods", []),
            content_warnings=raw_book.get("storygraph_tags", {}).get("content_warnings", []),
            tropes=raw_book.get("tropes", []),
            series=series,
            status=status,
            my_rating=review.get("rating"),
            my_review=review.get("review", ""),
            started_at=raw_book.get("started_reading_at") or "",
            finished_at=finished_at,
            date_added=review.get("created_at") or raw_book.get("created_at") or "",
            community_ratings=comm_ratings
        )
