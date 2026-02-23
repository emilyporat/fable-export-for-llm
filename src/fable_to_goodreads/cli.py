import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .auth import fetch_credentials_via_browser
from .client import FableClient
from .exporter import Exporter

console = Console()

def print_header():
    console.print(Panel.fit(
        """[bold magenta]Fable to Goodreads[/bold magenta]
[italic]Free your library from the Fable ecosystem[/italic]

Created by [bold blue]Joel DeBolt[/bold blue]""",
        border_style="magenta"
    ))

ENV_FILE = Path.home() / ".fable_export_env"

async def run_export():
    load_dotenv(ENV_FILE)

    user_id = os.getenv("FABLE_USER_ID")
    auth_token = os.getenv("FABLE_AUTH_TOKEN")

    email = os.getenv("FABLE_EMAIL")
    password = os.getenv("FABLE_PASSWORD")

    if not email or not password:
        console.print("[yellow]Enter your Fable login credentials (saved once to ~/.fable_export_env):[/yellow]")
        email = Prompt.ask("Email")
        password = Prompt.ask("Password", password=True)
        with open(ENV_FILE, "w") as f:
            f.write(f"FABLE_EMAIL={email}\nFABLE_PASSWORD={password}\n")
        console.print(f"[dim]Saved to {ENV_FILE}[/dim]")

    console.print("\n[dim]Logging into Fable...[/dim]")
    try:
        user_id, auth_token = await fetch_credentials_via_browser(email, password)
    except Exception as e:
        raise RuntimeError(f"Browser login failed: {e}") from e
    console.print(f"[dim]Authenticated as user [bold]{user_id}[/bold][/dim]")

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
        try:
            reviews = await client.fetch_reviews()
        except Exception as e:
            progress.stop()
            raise RuntimeError(f"Failed to fetch reviews: {e}") from e
        progress.update(task1, completed=100, total=100, description=f"[green]Fetched {len(reviews)} reviews")

        # Step 2: Lists
        task2 = progress.add_task("[cyan]Fetching book lists...", total=None)
        try:
            lists = await client.fetch_lists()
        except Exception as e:
            progress.stop()
            raise RuntimeError(f"Failed to fetch book lists: {e}") from e
        progress.update(task2, completed=100, total=100, description=f"[green]Found {len(lists)} lists")

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
            if book and book.id not in seen_ids:
                books.append(book)
                seen_ids.add(book.id)
            progress.advance(task4)

        # Step 5: Export
        task5 = progress.add_task("[cyan]Exporting files...", total=4)
        json_path = exporter.to_json(books)
        progress.advance(task5)

        gr_path = exporter.to_goodreads_csv(books)
        progress.advance(task5)

        master_path = exporter.to_master_csv(books)
        progress.advance(task5)

        recs_path = exporter.to_recommendations_jsonl(books)
        progress.advance(task5)

    console.print("\n[bold green]Done![/bold green]")
    console.print(f"• Master JSON: [blue]{json_path}[/blue]")
    console.print(f"• Goodreads CSV: [blue]{gr_path}[/blue]")
    console.print(f"• Master CSV: [blue]{master_path}[/blue]")
    console.print(f"• Recommendations JSONL: [blue]{recs_path}[/blue]")
    console.print("\n[italic]Raw responses saved in ./raw_data for auditing.[/italic]")

def main():
    print_header()
    try:
        asyncio.run(run_export())
    except Exception as e:
        cause = e.__cause__ or e
        console.print(f"[bold red]Error:[/bold red] {e}")
        if cause is not e:
            console.print(f"[red]Caused by:[/red] {cause}")
        sys.exit(1)

if __name__ == "__main__":
    main()