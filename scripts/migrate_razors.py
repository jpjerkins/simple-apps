"""Migrate razor blade data from TiddlyWiki markdown files to Razor Blade Tracker app."""

import re
import requests
from pathlib import Path

API_BASE = "http://thejerkins.duckdns.org:8001/api"
NOTES_DIR = Path(r"C:\Users\PhilJ\Nextcloud\Notes\4 Archive")

def parse_razor_file(file_path):
    """Parse a razor blade markdown file and extract data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter
    frontmatter_match = re.search(r'---\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)

    # Extract list field (usage dates)
    list_match = re.search(r'^list:\s*(.+)$', frontmatter, re.MULTILINE)
    if not list_match:
        return None

    usage_dates_str = list_match.group(1).strip()
    usage_dates = usage_dates_str.split()

    # Extract start date from filename
    filename = file_path.stem
    start_date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if not start_date_match:
        return None

    start_date = start_date_match.group(1)

    # All archived razors are retired
    status = "retired"

    # Default brand
    brand = "Feather"

    return {
        "brand": brand,
        "startDate": start_date,
        "usages": usage_dates,
        "status": status
    }

def create_razor(razor_data):
    """Create a razor blade entry via the API."""
    response = requests.post(f"{API_BASE}/razorblades/items", json=razor_data)
    if response.status_code in [200, 201]:
        print(f"[OK] Created: Razor started {razor_data['startDate']} ({len(razor_data['usages'])} uses)")
        return True
    else:
        print(f"[FAIL] Failed: Razor started {razor_data['startDate']} - {response.text}")
        return False

def main():
    """Main migration function."""
    # Find all razor blade markdown files
    razor_files = list(NOTES_DIR.glob("Razor started *.md"))

    print(f"Found {len(razor_files)} razor blade files")
    print("\nStarting migration...\n")

    razors = []
    for file_path in razor_files:
        razor_data = parse_razor_file(file_path)
        if razor_data:
            razors.append(razor_data)
        else:
            print(f"[SKIP] Could not parse: {file_path.name}")

    # Mark the most recent razor as active, others as retired
    if razors:
        razors.sort(key=lambda r: r['startDate'], reverse=True)
        razors[0]['status'] = 'active'
        print(f"Most recent razor ({razors[0]['startDate']}) marked as ACTIVE")

    print(f"\nParsed {len(razors)} razor blades")
    print("Creating entries...\n")

    success_count = 0
    for razor in razors:
        if create_razor(razor):
            success_count += 1

    print(f"\n{'='*50}")
    print(f"Migration complete: {success_count}/{len(razors)} razors created")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
