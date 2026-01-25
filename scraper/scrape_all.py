"""
Comprehensive Dark Tower Wiki Scraper
Scrapes all characters, books, comics, places, events, objects, etc.
"""

import requests
from bs4 import BeautifulSoup, NavigableString
import json
import re
import time
from urllib.parse import urljoin, quote
from pathlib import Path

BASE_URL = "https://darktower.fandom.com"

# Category URLs to scrape (excludes community/meta pages)
CATEGORIES = {
    "character": [
        "/wiki/Category:Characters",
        "/wiki/Category:Gunslingers",
        "/wiki/Category:Villains",
        "/wiki/Category:Ka-tet",
    ],
    "book": [
        "/wiki/Category:Books",
        "/wiki/Category:Novels",
        "/wiki/Category:Short_Stories",
    ],
    "comic": [
        "/wiki/Category:Comics",
    ],
    "place": [
        "/wiki/Category:Locations",
        "/wiki/Category:Cities",
        "/wiki/Category:Mid-World",
    ],
    "event": [
        "/wiki/Category:Events",
        "/wiki/Category:Battles",
    ],
    "object": [
        "/wiki/Category:Objects",
        "/wiki/Category:Weapons",
        "/wiki/Category:Artifacts",
    ],
    "creature": [
        "/wiki/Category:Creatures",
        "/wiki/Category:Species",
    ],
    "concept": [
        "/wiki/Category:Concepts",
        "/wiki/Category:Magic",
    ],
}

# Pages to explicitly exclude (meta/community pages)
EXCLUDE_PATTERNS = [
    r'/wiki/Category:',
    r'/wiki/User:',
    r'/wiki/Template:',
    r'/wiki/File:',
    r'/wiki/Special:',
    r'/wiki/Talk:',
    r'/wiki/Blog:',
    r'/wiki/Forum:',
    r'/wiki/Help:',
    r'/wiki/MediaWiki:',
    r'/wiki/Module:',
    r'action=edit',
    r'oldid=',
]


def clean_text(text):
    """Clean text by removing references and normalizing whitespace."""
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_with_spacing(element):
    """Extract text from an element, adding proper spacing around links."""
    if element is None:
        return ""
    
    parts = []
    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif child.name == 'a':
            text = child.get_text()
            if parts and parts[-1] and not parts[-1].endswith((' ', '\n', '(')):
                parts.append(' ')
            parts.append(text)
            parts.append(' ')
        elif child.name == 'br':
            parts.append('\n')
        elif child.name in ['b', 'i', 'strong', 'em', 'span']:
            parts.append(extract_text_with_spacing(child))
        else:
            parts.append(child.get_text())
    
    result = ''.join(parts)
    result = re.sub(r' +', ' ', result)
    return result


def parse_infobox(soup):
    """Extract structured data from the infobox."""
    infobox = soup.find("aside", class_="portable-infobox") or soup.find("table", class_="infobox")
    
    if not infobox:
        return None
    
    info = {}
    
    # Try portable infobox format (modern Fandom)
    for item in infobox.find_all("div", class_="pi-item"):
        label = item.find("h3", class_="pi-data-label")
        value = item.find("div", class_="pi-data-value")
        if label and value:
            key = label.get_text(strip=True)
            val = extract_text_with_spacing(value).strip()
            if key and val:
                info[key] = val
    
    # Also try data-source attributes
    for item in infobox.find_all(attrs={"data-source": True}):
        key = item.get("data-source", "")
        value_elem = item.find("div", class_="pi-data-value") or item.find("td")
        if value_elem:
            val = extract_text_with_spacing(value_elem).strip()
            if key and val and key not in info:
                info[key] = val
    
    return info if info else None


def parse_sections(content_div):
    """Parse content into sections based on headings."""
    sections = []
    current_section = {"heading": "Introduction", "level": 0, "content": []}
    
    for element in content_div.children:
        if element.name in ['h2', 'h3', 'h4']:
            if current_section["content"]:
                sections.append(current_section)
            
            heading_text = element.get_text(strip=True)
            heading_text = re.sub(r'\[edit\]', '', heading_text).strip()
            # Remove wiki edit brackets
            heading_text = re.sub(r'\[\]$', '', heading_text).strip()
            level = int(element.name[1])
            current_section = {"heading": heading_text, "level": level, "content": []}
            
        elif element.name == 'p':
            text = extract_text_with_spacing(element).strip()
            if text and len(text) > 30:
                current_section["content"].append(text)
                
        elif element.name in ['ul', 'ol']:
            items = []
            for li in element.find_all('li', recursive=False):
                item_text = extract_text_with_spacing(li).strip()
                if item_text:
                    items.append(f"• {item_text}")
            if items:
                current_section["content"].append('\n'.join(items))
    
    if current_section["content"]:
        sections.append(current_section)
    
    return sections


def format_infobox_as_text(infobox, title, category):
    """Convert infobox dict to readable definition text based on category."""
    if not infobox:
        return ""
    
    lines = [f"# {title}\n"]
    
    # Category-specific formatting
    if category == "character":
        lines.append("## Character Information\n")
        priority_fields = ['Alias', 'Occupation', 'Species', 'Status', 'Affiliation', 'Gender']
        secondary_fields = ['Relatives', 'Appearances', 'Mentioned', 'Family']
    elif category == "book":
        lines.append("## Book Information\n")
        priority_fields = ['Author', 'Published', 'Pages', 'Publisher', 'Series', 'Preceded by', 'Followed by']
        secondary_fields = ['ISBN', 'Characters', 'Setting']
    elif category == "place":
        lines.append("## Location Information\n")
        priority_fields = ['Type', 'Location', 'World', 'Status']
        secondary_fields = ['Appearances', 'Residents', 'Notable features']
    elif category == "object":
        lines.append("## Object Information\n")
        priority_fields = ['Type', 'Owner', 'Origin', 'Powers', 'Status']
        secondary_fields = ['Appearances', 'Users']
    else:
        lines.append(f"## {category.title()} Information\n")
        priority_fields = list(infobox.keys())[:5]
        secondary_fields = []
    
    for field in priority_fields:
        for key in infobox:
            if key.lower() == field.lower():
                lines.append(f"**{key}:** {infobox[key]}")
                break
    
    lines.append("")
    
    for field in secondary_fields:
        for key in infobox:
            if key.lower() == field.lower():
                value = infobox[key]
                if len(value) > 100:
                    value = value.replace(') ', ')\n  - ')
                lines.append(f"**{key}:** {value}")
                break
    
    # Remaining fields
    used_fields = set(f.lower() for f in priority_fields + secondary_fields)
    for key, value in infobox.items():
        if key.lower() not in used_fields:
            lines.append(f"**{key}:** {value}")
    
    return '\n'.join(lines)


def scrape_page(url, category):
    """Scrape a single wiki page with intelligent parsing."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"   ⚠️ Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Page title
    title_elem = soup.find("h1")
    if not title_elem:
        return None
    title = title_elem.get_text(strip=True)
    
    # Skip disambiguation and list pages
    if any(skip in title.lower() for skip in ['disambiguation', 'list of', 'category:']):
        return None

    # Parse infobox
    infobox = parse_infobox(soup)
    
    # Main content area
    content_div = soup.find("div", class_="mw-parser-output")
    if not content_div:
        return None
    
    # Parse sections
    sections = parse_sections(content_div)
    
    # Build structured text
    text_parts = []
    
    if infobox:
        infobox_text = format_infobox_as_text(infobox, title, category)
        text_parts.append(infobox_text)
    
    for section in sections:
        heading = section["heading"]
        content = '\n\n'.join(section["content"])
        
        if heading != "Introduction":
            text_parts.append(f"\n## {heading}\n")
        text_parts.append(content)
    
    full_text = clean_text('\n\n'.join(text_parts))
    
    # Skip very short pages
    if len(full_text) < 200:
        return None

    return {
        "url": url,
        "title": title,
        "category": category,
        "infobox": infobox,
        "sections": [{"heading": s["heading"], "content": '\n\n'.join(s["content"])} for s in sections],
        "text": full_text
    }


def get_pages_from_category(category_url):
    """Get all page URLs from a category page."""
    pages = set()
    
    try:
        response = requests.get(urljoin(BASE_URL, category_url), timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"   ⚠️ Failed to fetch category {category_url}: {e}")
        return pages
    
    soup = BeautifulSoup(response.text, "lxml")
    
    # Find category members
    category_div = soup.find("div", class_="category-page__members")
    if category_div:
        for link in category_div.find_all("a", href=True):
            href = link["href"]
            if href.startswith("/wiki/") and not any(re.search(p, href) for p in EXCLUDE_PATTERNS):
                pages.add(href)
    
    # Also try the older wiki format
    content_div = soup.find("div", id="mw-pages") or soup.find("div", class_="mw-category")
    if content_div:
        for link in content_div.find_all("a", href=True):
            href = link["href"]
            if href.startswith("/wiki/") and not any(re.search(p, href) for p in EXCLUDE_PATTERNS):
                pages.add(href)
    
    return pages


def discover_all_pages():
    """Discover all pages from all categories."""
    all_pages = {}  # url -> category
    
    print("🔍 Discovering pages from categories...")
    
    for category, category_urls in CATEGORIES.items():
        print(f"\n📂 Category: {category}")
        category_pages = set()
        
        for cat_url in category_urls:
            pages = get_pages_from_category(cat_url)
            category_pages.update(pages)
            print(f"   Found {len(pages)} pages from {cat_url}")
        
        # Add to all_pages (first category wins for duplicates)
        for page_url in category_pages:
            if page_url not in all_pages:
                all_pages[page_url] = category
        
        print(f"   Total unique for {category}: {len(category_pages)}")
    
    print(f"\n📊 Total unique pages discovered: {len(all_pages)}")
    return all_pages


def scrape_all_pages(page_dict, delay=0.5, limit=None):
    """Scrape all discovered pages."""
    all_data = []
    failed = []
    
    pages_to_scrape = list(page_dict.items())
    if limit:
        pages_to_scrape = pages_to_scrape[:limit]
    
    print(f"\n🌐 Scraping {len(pages_to_scrape)} pages...")
    
    for i, (page_url, category) in enumerate(pages_to_scrape):
        full_url = urljoin(BASE_URL, page_url)
        print(f"   [{i+1}/{len(pages_to_scrape)}] {page_url.split('/')[-1]}", end="")
        
        data = scrape_page(full_url, category)
        
        if data:
            all_data.append(data)
            print(f" ✅ ({category})")
        else:
            failed.append(page_url)
            print(f" ⚠️ skipped")
        
        time.sleep(delay)  # Be nice to the server
    
    print(f"\n✅ Successfully scraped: {len(all_data)}")
    print(f"⚠️ Skipped/Failed: {len(failed)}")
    
    return all_data


def save_data(data, output_path="data/raw_pages.json"):
    """Save scraped data to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(data)} pages to {output_path}")
    
    # Print category distribution
    categories = {}
    for page in data:
        cat = page.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📊 Category distribution:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"   - {cat}: {count}")


# Also add some important pages that might be missed by categories
IMPORTANT_PAGES = [
    # Characters
    ("/wiki/Roland_Deschain", "character"),
    ("/wiki/Jake_Chambers", "character"),
    ("/wiki/Eddie_Dean", "character"),
    ("/wiki/Susannah_Dean", "character"),
    ("/wiki/Oy", "character"),
    ("/wiki/Walter_Padick", "character"),
    ("/wiki/Crimson_King", "character"),
    ("/wiki/Cuthbert_Allgood", "character"),
    ("/wiki/Alain_Johns", "character"),
    ("/wiki/Randall_Flagg", "character"),
    # Books (all 8 novels)
    ("/wiki/The_Dark_Tower_I:_The_Gunslinger", "book"),
    ("/wiki/The_Dark_Tower_II:_The_Drawing_of_the_Three", "book"),
    ("/wiki/The_Dark_Tower_III:_The_Waste_Lands", "book"),
    ("/wiki/The_Dark_Tower_IV:_Wizard_and_Glass", "book"),
    ("/wiki/The_Dark_Tower_V:_Wolves_of_the_Calla", "book"),
    ("/wiki/The_Dark_Tower_VI:_Song_of_Susannah", "book"),
    ("/wiki/The_Dark_Tower_VII:_The_Dark_Tower", "book"),
    ("/wiki/The_Wind_Through_the_Keyhole", "book"),
    # Alternate book URLs (some wikis use shorter names)
    ("/wiki/The_Gunslinger", "book"),
    ("/wiki/The_Drawing_of_the_Three", "book"),
    ("/wiki/The_Waste_Lands", "book"),
    ("/wiki/Wizard_and_Glass", "book"),
    ("/wiki/Wolves_of_the_Calla", "book"),
    ("/wiki/Song_of_Susannah", "book"),
    # Places
    ("/wiki/Dark_Tower", "place"),  # The actual tower
    ("/wiki/Mid-World", "place"),
    ("/wiki/Gilead", "place"),
    ("/wiki/All-World", "place"),
    ("/wiki/End-World", "place"),
    ("/wiki/Mejis", "place"),
    ("/wiki/Calla_Bryn_Sturgis", "place"),
    # Concepts
    ("/wiki/Ka", "concept"),
    ("/wiki/Ka-tet", "concept"),
    ("/wiki/Beam", "concept"),
    ("/wiki/Gunslinger", "concept"),
    ("/wiki/High_Speech", "concept"),
]


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Dark Tower Wiki")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of pages to scrape")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    parser.add_argument("--important-only", action="store_true", help="Only scrape important pages")
    args = parser.parse_args()
    
    if args.important_only:
        # Quick mode: just important pages
        page_dict = dict(IMPORTANT_PAGES)
        print(f"📌 Using {len(page_dict)} important pages only")
    else:
        # Full discovery mode
        page_dict = discover_all_pages()
        
        # Add important pages if not already present
        for url, cat in IMPORTANT_PAGES:
            if url not in page_dict:
                page_dict[url] = cat
    
    # Scrape all pages
    data = scrape_all_pages(page_dict, delay=args.delay, limit=args.limit)
    
    # Save data
    save_data(data)
