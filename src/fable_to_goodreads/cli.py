import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .client import FableClient
from .exporter import Exporter

console = Console()

def print_header():
    console.print(Panel.fit(
        "[bold magenta]Fable to Goodreads[/bold magenta]
"
        "[italic]Free your library from the Fable ecosystem[/italic]

"
        "Created by [bold blue]Joel DeBolt[/bold blue]",
        border_style="magenta"
    ))

async def run_export():
    load_dotenv()
    
    user_id = os.getenv("FABLE_USER_ID")
    auth_token = os.getenv("FABLE_AUTH_TOKEN")
    
    if not user_id or not auth_token:
        console.print("[yellow]Credentials missing in .env![/yellow]")
        user_id = Prompt.ask("Enter your FABLE_USER_ID")
        auth_token = Prompt.ask("Enter your FABLE_AUTH_TOKEN (JWT)")
        
        with open(".env", "a") as f:
            f.write(f"
FABLE_USER_ID={user_id}
FABLE_AUTH_TOKEN={auth_token}
")

    client = FableClient(user_id, auth_token)
    exporter = Exporter()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        # Step 1: Reviews
        task1 = progress.add_task("[cyan]Fetching reviews and ratings...", total=None)
        reviews = await client.fetch_reviews()
        progress.update(task1, completed=100, description=f"[green]Fetched {len(reviews)} reviews")

        # Step 2: Lists
        task2 = progress.add_task("[cyan]Fetching book lists...", total=None)
        lists = await client.fetch_lists()
        progress.update(task2, completed=100, description=f"[green]Found {len(lists)} lists")

        # Step 3: Books
        all_raw_items = []
        task3 = progress.add_task("[cyan]Downloading book data...", total=len(lists))
        for lst in lists:
            name = lst.get("name", "Unknown")
            items = await client.fetch_books_from_list(lst["id"], name)
            all_raw_items.extend(items)
            progress.advance(task3)
            
        # Step 4: Parse
        task4 = progress.add_task("[cyan]Parsing and normalizing...", total=len(all_raw_items))
        books = []
        seen_ids = set()
        for item in all_raw_items:
            book = client.parse_book(item, reviews)
            if book.id not in seen_ids:
                books.append(book)
                seen_ids.add(book.id)
            progress.advance(task4)

        # Step 5: Export
        task5 = progress.add_task("[cyan]Exporting files...", total=3)
        json_path = exporter.to_json(books)
        progress.advance(task5)
        
        gr_path = exporter.to_goodreads_csv(books)
        progress.advance(task5)
        
        master_path = exporter.to_master_csv(books)
        progress.advance(task5)

    console.print("
[bold green]Done![/bold green]")
    console.print(f"• Master JSON: [blue]{json_path}[/blue]")
    console.print(f"• Goodreads CSV: [blue]{gr_path}[/blue]")
    console.print(f"• Master CSV: [blue]{master_path}[/blue]")
    console.print("
[italic]Raw responses saved in ./raw_data for auditing.[/italic]")

def main():
    print_header()
    try:
        asyncio.run(run_export())
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
