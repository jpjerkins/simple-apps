"""Migrate books from TiddlyWiki markdown files to Books app."""

import re
import requests

API_BASE = "http://thejerkins.duckdns.org:8001/api"

# Category mapping
CATEGORY_MAP = {
    "Christian Loving": "Christian Living",
    "Business/Entrepreneurship": "Business/Entrepreneurship",
    "Leadership": "Leadership",
    "Communication": "Communication",
    "Miscellany Non-fiction": "Non-Fiction",
    "Fiction": "Fiction",
    "I lead teams to success": "Leadership",
    "I grow assets": "Finance",
    "Miscellany": "Non-Fiction"
}

def parse_book_entry(line, category):
    """Parse a book entry line and extract title, author, notes."""
    # Remove markdown formatting
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    # Remove list markers
    line = re.sub(r'^\*+\s*', '', line)
    line = re.sub(r'^-\s*', '', line)
    line = re.sub(r'^__', '', line)
    line = re.sub(r'__.*$', '', line)  # Remove everything after closing __

    # Extract title and author
    title = None
    author = None
    notes = None
    recommended_by = None

    # Pattern: Title by Author
    match = re.match(r'(.+?)\s+by\s+(.+)', line, re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        author_part = match.group(2).strip()
        # Remove any trailing notes in parentheses
        author = re.sub(r'\s*\([^)]+\).*$', '', author_part)
    else:
        # Just a title
        title = line.strip()
        # Clean up common patterns
        title = re.sub(r'\s*\([^)]+\).*$', '', title)
        title = re.sub(r'\s*-\s*.*$', '', title)

    # Extract recommended by from original line if present
    if 'recommended by' in line.lower():
        rec_match = re.search(r'recommended by\s+(.+?)(?:\)|$)', line, re.IGNORECASE)
        if rec_match:
            recommended_by = rec_match.group(1).strip()

    if not title:
        return None

    return {
        "title": title,
        "author": author or "",
        "category": CATEGORY_MAP.get(category, "Non-Fiction"),
        "status": "to-read",
        "priority": "medium",
        "recommendedBy": recommended_by or "",
        "link": "",
        "notes": ""
    }

def migrate_books_from_file(file_path):
    """Parse markdown file and extract books."""
    books = []
    current_category = None

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Skip frontmatter and empty lines
            if line.startswith('---') or not line:
                continue

            # Check for category header
            if line.startswith('##'):
                current_category = line.replace('##', '').strip()
                continue

            # Check for sub-headers (recommended by sections)
            if line.startswith('###'):
                rec_by = line.replace('###', '').strip()
                if 'Recommended by' in rec_by:
                    current_category = f"Fiction ({rec_by})"
                continue

            # Skip links, notes (lines starting with **), and other metadata
            if line.startswith('http') or line.startswith('**') or line.startswith('*#'):
                continue

            # Skip reference links and other non-book lines
            if '[[' in line and ']]' in line and 'Parent' not in line:
                continue

            # Parse book entry
            if line.startswith('-') or line.startswith('*'):
                if current_category:
                    book = parse_book_entry(line, current_category)
                    if book and book['title']:
                        # Filter out very short titles (likely parsing errors)
                        if len(book['title']) > 2:
                            books.append(book)

    return books

def create_book(book_data):
    """Create a book via the API."""
    response = requests.post(f"{API_BASE}/books/items", json=book_data)
    if response.status_code in [200, 201]:
        print(f"[OK] Created: {book_data['title']}")
        return True
    else:
        print(f"[FAIL] Failed: {book_data['title']} - {response.text}")
        return False

def main():
    """Main migration function."""
    files = [
        r"C:\Users\PhilJ\Nextcloud\Notes\3 Resources\Reference\Books to Read.md",
        r"C:\Users\PhilJ\Nextcloud\Notes\3 Resources\Reference\BooksToRead.md"
    ]

    all_books = []
    for file_path in files:
        print(f"\nParsing {file_path}...")
        books = migrate_books_from_file(file_path)
        all_books.extend(books)
        print(f"Found {len(books)} books")

    print(f"\nTotal books to migrate: {len(all_books)}")
    print("\nStarting migration...\n")

    success_count = 0
    for book in all_books:
        if create_book(book):
            success_count += 1

    print(f"\n{'='*50}")
    print(f"Migration complete: {success_count}/{len(all_books)} books created")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
