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
            isbn = b.isbn
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
                "Author": ", ".join(b.authors),
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
        
        # Flattened fields for master list
        headers = [
            "Title", "Authors", "ISBN13", "Series", "Position", "Status", 
            "My Rating", "Comm Rating", "Tropes", "Genres", "Moods", "Finished Date"
        ]
        
        rows = []
        for b in books:
            rows.append({
                "Title": b.title,
                "Authors": ", ".join(b.authors),
                "ISBN13": b.isbn13,
                "Series": b.series.name if b.series else "",
                "Position": b.series.position if b.series else "",
                "Status": b.status,
                "My Rating": b.my_rating or "",
                "Comm Rating": b.community_ratings.average or "",
                "Tropes": "; ".join(b.tropes),
                "Genres": "; ".join(b.genres),
                "Moods": "; ".join(b.moods),
                "Finished Date": b.finished_at[:10] if b.finished_at else ""
            })
            
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return path
