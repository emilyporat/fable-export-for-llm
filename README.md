# Fable to Goodreads (fable-xport 2.0)

**By Joel DeBolt**

A modern, high-performance CLI tool built to rescue your book library from Fable.co. Fable doesn't make it easy to leave their ecosystem, so this tool reverse-engineers their API to give you a complete, high-fidelity export of your data.

Created for my wife and any other readers who want ownership of their reading history.

## Features

- **High-Fidelity Metadata:** Captures tropes, series info, community ratings, and StoryGraph-specific tags.
- **Async Engine:** Powered by `httpx` for fast, concurrent API requests.
- **Auto-Correction:** Automatically fixes missing "Read" dates using review timestamps.
- **Modern Interface:** Beautiful CLI feedback using `rich`.
- **Multiple Formats:** Exports to JSON (Master backup), Master CSV, and Goodreads-ready CSV.
- **Raw Data Audit:** Saves every raw API response in `./raw_data` for transparency and debugging.

## Why this exists?

Fable is a great platform, but like many modern "walled gardens," they lack basic data portability features. Your reading history, reviews, and ratings belong to you, not the platform. This tool ensures you can move your data to Goodreads, StoryGraph, or your own spreadsheets without losing the fine details like Tropes and detailed Rating dimensions.

## Installation

```bash
git clone https://github.com/z330/fable-to-goodreads.git
cd fable-to-goodreads
pip install .
```

## Usage

Run the tool:
```bash
fable-export
```

On first run, it will ask for your **User ID** and **Auth Token**. You can find these by inspecting Fable's web traffic in your browser's Developer Tools (Network tab).

_NOTE from Emily: the JWT was too long to paste into the CLI input, so I just changed it to always read from an env file._

### Extraction Instructions:
1. Login to `fable.co`
2. Open **DevTools (F12)** -> **Network**
3. Refresh the page
4. Look for a request to `api.fable.co`
5. Copy your **User ID** (from the URL) and **Authorization** token (from headers).

## Project Structure

- `src/fable_to_goodreads/client.py`: Async API client.
- `src/fable_to_goodreads/models.py`: Pydantic data models.
- `src/fable_to_goodreads/exporter.py`: Logic for formatting exports.
- `outputs/`: Where your finished files end up.
- `raw_data/`: Audit trail of raw API responses.

## License

MIT - Free to use and modify.
