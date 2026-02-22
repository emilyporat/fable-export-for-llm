import csv
import json
from pathlib import Path
from typing import List
from datetime import datetime
from .models import Book

class Exporter:
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def to_json(self, books: List[Book], filename: str = "fable_library.json"):
        path = self.output_dir / filename
        data = [book.dict() for book in books]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def to_goodreads_csv(self, books: List[Book]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"goodreads_import_{timestamp}.csv"
        
        headers = [
            "Title", "Author", "ISBN", "My Rating", "Average Rating", 
            "Publisher", "Binding", "Year Published", "Original Publication Year", 
            "Date Read", "Date Added", "Shelves", "Bookshelves", "My Review"
        ]
        
        rows = []
        for b in books:
            # Validate ISBN
            isbn = b.isbn or b.isbn13 or b.isbn10 or ""
            if isbn:
                clean_isbn = isbn.replace("-", "").replace(" ", "")
                if not all(c.isdigit() or c.lower() == 'x' for c in clean_isbn):
                    isbn = ""

            status = b.status.lower()
            if status in ["finished", "read"]:
                shelf = "read"
                date_read = b.finished_at[:10] if b.finished_at else ""
            elif status in ["reading", "current"]:
                shelf = "currently-reading"
                date_read = ""
            else:
                shelf = "to-read"
                date_read = ""

            rows.append({
                "Title": b.title,
                "Author": ", ".join(a.name for a in b.authors),
                "ISBN": isbn,
                "My Rating": b.my_rating or "",
                "Average Rating": b.community_ratings.average or "",
                "Publisher": b.publisher,
                "Binding": "Paperback",
                "Year Published": b.published_date[:4] if b.published_date else "",
                "Original Publication Year": b.published_date[:4] if b.published_date else "",
                "Date Read": date_read,
                "Date Added": b.date_added[:10] if b.date_added else "",
                "Shelves": shelf,
                "Bookshelves": " ".join([g.lower().replace(" ", "-") for g in b.genres]),
                "My Review": b.my_review
            })

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def to_master_csv(self, books: List[Book]):
        path = self.output_dir / "fable_master_list.csv"
        if not books: return path

        headers = [
            "Title", "Authors",
            "Non Fiction", "Genres", "Subjects", "Moods", "Content Warnings", "Tropes",
            "Series Name", "Series Position",
            "Status", "Favorite", "Finished At",
            "My Rating (Overall)", "My Rating (Characters)",
            "My Rating (Plot)", "My Rating (Writing)", "My Rating (Setting)",
            "My Review", "Description",
        ]

        rows = []
        for b in books:
            rows.append({
                "Title": b.title,
                "Authors": "; ".join(a.name for a in b.authors),
                "Non Fiction": b.non_fiction if b.non_fiction is not None else "",
                "Genres": "; ".join(b.genres),
                "Subjects": "; ".join(b.subjects),
                "Moods": "; ".join(b.moods),
                "Content Warnings": "; ".join(b.content_warnings),
                "Tropes": "; ".join(b.tropes),
                "Series Name": b.series.name if b.series else "",
                "Series Position": b.series.position if b.series else "",
                "Status": b.list_name or "",
                "Favorite": b.favorite if b.favorite is not None else "",
                "Finished At": b.finished_at[:10] if b.finished_at else "",
                "My Rating (Overall)": b.community_ratings.average if b.community_ratings.average is not None else "",
                "My Rating (Characters)": b.community_ratings.characters if b.community_ratings.characters is not None else "",
                "My Rating (Plot)": b.community_ratings.plot if b.community_ratings.plot is not None else "",
                "My Rating (Writing)": b.community_ratings.writing if b.community_ratings.writing is not None else "",
                "My Rating (Setting)": b.community_ratings.setting if b.community_ratings.setting is not None else "",
                "My Review": b.my_review or "",
                "Description": b.description or "",
            })

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def to_recommendations_jsonl(self, books: List[Book]):
        path = self.output_dir / "recommendations.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for b in books:
                record = {
                    "title": b.title,
                    "authors": [a.name for a in b.authors],
                    "status": b.list_name or b.status,
                    "rating": b.community_ratings.average,
                    "favorite": b.favorite,
                    "finished_at": b.finished_at[:10] if b.finished_at else None,
                    "non_fiction": b.non_fiction,
                    "genres": b.genres or None,
                    "moods": b.moods or None,
                    "tropes": b.tropes or None,
                    "content_warnings": b.content_warnings or None,
                    "series": {"name": b.series.name, "position": b.series.position} if b.series else None,
                    "review": b.my_review or None,
                    "description": b.description or None,
                }
                # Drop null/empty values to save tokens
                record = {k: v for k, v in record.items() if v is not None and v != [] and v != ""}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return path
