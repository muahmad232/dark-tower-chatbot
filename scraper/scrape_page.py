import requests
from bs4 import BeautifulSoup, NavigableString
import json
import re


def clean_text(text):
    """Clean text by removing references and normalizing whitespace."""
    # Remove references like [1], [23]
    text = re.sub(r"\[\d+\]", "", text)
    # Normalize whitespace (but preserve intentional newlines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_with_spacing(element):
    """
    Extract text from an element, adding proper spacing around links.
    This fixes the issue of concatenated words like "ofStevenandGabrielle".
    """
    if element is None:
        return ""
    
    parts = []
    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif child.name == 'a':
            # Add space before link text if needed
            text = child.get_text()
            if parts and parts[-1] and not parts[-1].endswith((' ', '\n', '(')):
                parts.append(' ')
            parts.append(text)
            # Add space after if next sibling doesn't start with punctuation
            parts.append(' ')
        elif child.name == 'br':
            parts.append('\n')
        elif child.name in ['b', 'i', 'strong', 'em', 'span']:
            parts.append(extract_text_with_spacing(child))
        else:
            parts.append(child.get_text())
    
    result = ''.join(parts)
    # Clean up double spaces
    result = re.sub(r' +', ' ', result)
    return result


def parse_infobox(soup):
    """
    Extract structured data from the character infobox.
    Returns a dict with key attributes.
    """
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
    """
    Parse content into sections based on headings.
    Returns a list of {heading, level, content} dicts.
    """
    sections = []
    current_section = {"heading": "Introduction", "level": 0, "content": []}
    
    for element in content_div.children:
        if element.name in ['h2', 'h3', 'h4']:
            # Save previous section if it has content
            if current_section["content"]:
                sections.append(current_section)
            
            # Start new section
            heading_text = element.get_text(strip=True)
            # Remove edit links like "[edit]"
            heading_text = re.sub(r'\[edit\]', '', heading_text).strip()
            level = int(element.name[1])
            current_section = {"heading": heading_text, "level": level, "content": []}
            
        elif element.name == 'p':
            text = extract_text_with_spacing(element).strip()
            if text and len(text) > 30:  # Skip very short paragraphs
                current_section["content"].append(text)
                
        elif element.name in ['ul', 'ol']:
            # Handle lists
            items = []
            for li in element.find_all('li', recursive=False):
                item_text = extract_text_with_spacing(li).strip()
                if item_text:
                    items.append(f"• {item_text}")
            if items:
                current_section["content"].append('\n'.join(items))
    
    # Don't forget the last section
    if current_section["content"]:
        sections.append(current_section)
    
    return sections


def format_infobox_as_text(infobox, title):
    """Convert infobox dict to readable definition text."""
    if not infobox:
        return ""
    
    # Priority fields for character definition
    priority_fields = ['Alias', 'Occupation', 'Species', 'Status', 'Affiliation']
    secondary_fields = ['Relatives', 'Appearances', 'Mentioned']
    
    lines = [f"# {title}\n"]
    lines.append("## Character Information\n")
    
    for field in priority_fields:
        if field in infobox:
            lines.append(f"**{field}:** {infobox[field]}")
    
    lines.append("")  # Empty line
    
    for field in secondary_fields:
        if field in infobox:
            value = infobox[field]
            # Format long lists with line breaks
            if len(value) > 100:
                value = value.replace(') ', ')\n  - ')
            lines.append(f"**{field}:** {value}")
    
    # Any remaining fields
    for field, value in infobox.items():
        if field not in priority_fields and field not in secondary_fields:
            lines.append(f"**{field}:** {value}")
    
    return '\n'.join(lines)


def scrape_dark_tower_page(url):
    """
    Scrape a Dark Tower wiki page with intelligent parsing.
    Returns structured data with infobox, sections, and clean text.
    """
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # Page title
    title = soup.find("h1").get_text(strip=True)

    # Parse infobox for character/entity data
    infobox = parse_infobox(soup)
    
    # Main content area (Fandom wiki specific)
    content_div = soup.find("div", class_="mw-parser-output")
    
    # Parse into sections
    sections = parse_sections(content_div)
    
    # Build structured text with clear section markers
    text_parts = []
    
    # Add formatted infobox as definition section
    if infobox:
        infobox_text = format_infobox_as_text(infobox, title)
        text_parts.append(infobox_text)
    
    # Add each section with heading markers
    for section in sections:
        heading = section["heading"]
        content = '\n\n'.join(section["content"])
        
        if heading != "Introduction":
            text_parts.append(f"\n## {heading}\n")
        text_parts.append(content)
    
    full_text = clean_text('\n\n'.join(text_parts))

    return {
        "url": url,
        "title": title,
        "infobox": infobox,
        "sections": [{"heading": s["heading"], "content": '\n\n'.join(s["content"])} for s in sections],
        "text": full_text
    }


if __name__ == "__main__":
    url = "https://darktower.fandom.com/wiki/Roland_Deschain"

    data = scrape_dark_tower_page(url)

    with open("data/raw_pages.json", "w", encoding="utf-8") as f:
        json.dump([data], f, indent=2, ensure_ascii=False)

    print(f"✅ Page scraped: {data['title']}")
    print(f"   Infobox fields: {len(data['infobox']) if data['infobox'] else 0}")
    print(f"   Sections: {len(data['sections'])}")
    print(f"   Total text length: {len(data['text'])} chars")
