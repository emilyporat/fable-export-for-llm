import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx
from .models import Author, Book, SeriesInfo, CommunityRatings, ReadingProgress

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
                    if isinstance(r, dict):
                        book_data = r.get("book", {})
                        if isinstance(book_data, dict):
                            book_id = book_data.get("id")
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
                for r in results:
                    r["_list_name"] = list_name
                books.extend(results)
                
                if not results or len(results) < 100:
                    break
                offset += 100
        return books

    def parse_book(self, item: Dict[str, Any], reviews: Dict[str, Any]) -> Optional[Book]:
        if not item or not isinstance(item, dict):
            return None

        raw_book = item.get("book", item)
        if not raw_book or not isinstance(raw_book, dict):
            return None

        book_id = raw_book.get("id")
        if not book_id:
            return None

        review = reviews.get(book_id, {})
        if not isinstance(review, dict):
            review = {}

        # Series
        series_sets = raw_book.get("bookseries_set", [])
        series = None
        if series_sets and isinstance(series_sets, list):
            s = series_sets[0]
            if isinstance(s, dict):
                series_obj = s.get("book_series", {})
                series = SeriesInfo(
                    name=series_obj.get("name", "") if isinstance(series_obj, dict) else "",
                    position=str(s.get("position", ""))
                )

        # Ratings — these are the user's own sub-ratings from the reviews endpoint
        comm_ratings = CommunityRatings(
            average=review.get("rating"),
            characters=review.get("characters_rating"),
            plot=review.get("plot_rating"),
            writing=review.get("writing_style_rating"),
            setting=review.get("setting_rating"),
        )

        # ISBN
        isbn = raw_book.get("isbn", "") or ""
        isbn10 = isbn if len(isbn) == 10 else ""
        isbn13 = isbn if len(isbn) == 13 else ""

        # Status — authoritative source is reading_progress.status
        reading_progress_raw = raw_book.get("reading_progress") or {}
        if not isinstance(reading_progress_raw, dict):
            reading_progress_raw = {}
        status = reading_progress_raw.get("status") or item.get("status") or raw_book.get("status") or "unread"

        reading_progress = ReadingProgress(
            current_percentage=reading_progress_raw.get("current_percentage"),
            current_page=reading_progress_raw.get("current_page"),
            page_count=reading_progress_raw.get("page_count"),
            status=reading_progress_raw.get("status"),
        ) if reading_progress_raw else None

        # Dates
        started_at = raw_book.get("started_reading_at") or ""
        finished_at = raw_book.get("finished_reading_at") or ""
        if not finished_at and status.lower() in ["finished", "read"]:
            finished_at = review.get("created_at") or review.get("updated_at") or ""

        # Authors
        raw_authors = raw_book.get("authors", [])
        authors = []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if isinstance(a, dict):
                    name = a.get("name")
                    if name:
                        authors.append(Author(
                            name=name,
                            slug=a.get("slug"),
                            biography=a.get("biography", ""),
                        ))
                elif isinstance(a, str):
                    authors.append(Author(name=a))

        # Tags
        storygraph_tags = raw_book.get("storygraph_tags") or {}
        if not isinstance(storygraph_tags, dict):
            storygraph_tags = {}

        moods = storygraph_tags.get("moods")
        if not isinstance(moods, list): moods = []

        cw = storygraph_tags.get("content_warnings")
        if not isinstance(cw, list): cw = []

        tropes = raw_book.get("tropes")
        if not isinstance(tropes, list):
            tropes = []

        # Subjects — list of lists, flatten to "Fiction > Literary" style strings
        raw_subjects = raw_book.get("subjects") or []
        subjects = [" > ".join(s) for s in raw_subjects if isinstance(s, list)]

        return Book(
            id=book_id,
            title=raw_book.get("title", "Unknown"),
            subtitle=raw_book.get("subtitle") or "",
            authors=authors,
            isbn=isbn,
            isbn10=isbn10,
            isbn13=isbn13,
            display_isbn=raw_book.get("display_isbn") or "",
            publisher=raw_book.get("imprint") or raw_book.get("publisher") or "",
            page_count=raw_book.get("page_count"),
            chapter_count=raw_book.get("chapter_count"),
            published_date=raw_book.get("published_date") or "",
            description=raw_book.get("description") or "",
            cover_image=raw_book.get("cover_image") or "",
            cover_image_small=raw_book.get("cover_image_small") or "",
            background_color=raw_book.get("background_color") or "",
            fable_url=raw_book.get("url") or "",
            source=raw_book.get("source") or "",
            price_usd=raw_book.get("price_usd") or "",
            non_fiction=raw_book.get("non_fiction"),
            family_id=raw_book.get("family_id"),
            is_free=raw_book.get("is_free"),
            can_purchase=raw_book.get("can_purchase"),
            can_download=raw_book.get("can_download"),
            store_availability=raw_book.get("store_availability") or "",
            is_out_of_catalog=raw_book.get("is_out_of_catalog"),
            genres=[g.get("name") for g in raw_book.get("genres", []) if isinstance(g, dict) and g.get("name")],
            subjects=subjects,
            moods=moods,
            content_warnings=cw,
            tropes=tropes,
            series=series,
            status=status,
            my_rating=review.get("rating"),
            my_review=review.get("review") or "",
            started_at=started_at,
            started_at_date_type=raw_book.get("started_reading_date_type") or "",
            finished_at=finished_at,
            finished_at_date_type=raw_book.get("finished_reading_date_type") or "",
            date_added=review.get("created_at") or raw_book.get("created_at") or "",
            list_name=item.get("_list_name") or "",
            favorite=item.get("favorite"),
            sort_value=item.get("sort_value"),
            reading_progress=reading_progress,
            community_ratings=comm_ratings,
        )