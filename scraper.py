#!/usr/bin/env python3
"""
Enhanced Wikipedia scraper for Phase 1 PoC
Intelligently extracts and processes Wikipedia content while preserving structure
"""

import requests
from bs4 import BeautifulSoup, NavigableString
import json
import sys
from urllib.parse import urlparse
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import traceback

class WikipediaSection:
    """Represents a section of Wikipedia content with its hierarchy"""
    def __init__(self, title: str, level: int, content: str):
        self.title = title
        self.level = level
        self.content = content
        self.subsections: List[WikipediaSection] = []

    def to_dict(self) -> Dict:
        """Convert section to dictionary format"""
        return {
            "title": self.title,
            "level": self.level,
            "content": self.content,
            "subsections": [s.to_dict() for s in self.subsections]
        }

def clean_text(text: str) -> str:
    """
    Enhanced text cleaning specifically for Wikipedia content
    """
    # Remove edit links [edit]
    text = re.sub(r'\[\s*edit\s*\]', '', text)
    
    # Remove citation numbers but preserve important brackets
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[citation needed\]', '', text)
    
    # Remove reference numbers at the end of sentences
    text = re.sub(r'\d+$', '', text)
    
    # Handle special Wikipedia notations
    text = re.sub(r'\(; .*?\)', '', text)  # Remove pronunciation guides
    text = re.sub(r'\s*\([^)]*\b(?:born|died)\b[^)]*\)', '', text)  # Remove birth/death dates
    
    # Normalize whitespace while preserving paragraph breaks
    paragraphs = text.split('\n\n')
    paragraphs = [re.sub(r'\s+', ' ', p.strip()) for p in paragraphs]
    text = '\n\n'.join(filter(None, paragraphs))
    
    return text.strip()

def extract_section_content(section_tag) -> str:
    """
    Extract clean content from a section, handling special cases
    """
    content = []
    current = section_tag.find_next_sibling()
    
    while current and not (current.name and current.name.startswith('h')):
        if current.name == 'p':
            text = current.get_text().strip()
            if text:  # Only add non-empty paragraphs
                content.append(text)
        elif current.name in ['ul', 'ol']:
            # Handle lists
            for item in current.find_all('li', recursive=False):
                text = item.get_text().strip()
                if text:
                    content.append(f"• {text}")
        
        current = current.find_next_sibling()
    
    return '\n\n'.join(content)

def get_section_level(tag) -> int:
    """Get the level of a section heading (h1=1, h2=2, etc.)"""
    return int(tag.name[1]) if tag.name[1].isdigit() else 0

def extract_wikipedia_content(soup: BeautifulSoup) -> Tuple[str, List[WikipediaSection]]:
    """
    Extract Wikipedia content preserving structure and hierarchy
    """
    # Extract the lead section (before the first heading)
    lead_paragraphs = []
    current = soup.find('p')
    
    while current and current.name == 'p':
        # Skip empty or special paragraphs
        if not current.get('class') and current.get_text().strip():
            text = current.get_text().strip()
            lead_paragraphs.append(text)
        current = current.find_next_sibling()
        # Stop at first heading
        if current and current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            break
    
    lead_text = '\n\n'.join(lead_paragraphs)
    lead_text = clean_text(lead_text)

    # Extract all sections
    sections = []
    current_section_stack = []
    
    # Get all headings
    for heading in soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
        # Skip unwanted sections
        heading_text = heading.get_text().strip()
        if any(x in heading_text.lower() for x in [
            'references', 'external links', 'see also', 'notes', 
            'further reading', 'bibliography', 'footnotes'
        ]):
            continue
            
        # Remove edit links and other spans from heading
        for span in heading.find_all('span'):
            span.decompose()
            
        # Get clean heading text
        title = heading.get_text().strip()
        level = int(heading.name[1])  # h2 -> 2, h3 -> 3, etc.
        
        # Extract section content
        content_parts = []
        current = heading.find_next_sibling()
        
        while current and not (current.name and current.name.startswith('h')):
            if current.name == 'p' and current.get_text().strip():
                content_parts.append(current.get_text().strip())
            elif current.name in ['ul', 'ol']:
                for item in current.find_all('li', recursive=False):
                    text = item.get_text().strip()
                    if text:
                        content_parts.append(f"• {text}")
            elif current.name == 'div' and 'hatnote' not in current.get('class', []):
                text = current.get_text().strip()
                if text:
                    content_parts.append(text)
            current = current.find_next_sibling()
        
        section_content = '\n\n'.join(content_parts)
        section_content = clean_text(section_content)
        
        # Only create section if it has content or subsections
        if section_content.strip():
            # Create new section
            new_section = WikipediaSection(title, level, section_content)
            
            # Handle section hierarchy
            while current_section_stack and current_section_stack[-1].level >= level:
                current_section_stack.pop()
                
            if current_section_stack:
                current_section_stack[-1].subsections.append(new_section)
            else:
                sections.append(new_section)
                
            current_section_stack.append(new_section)

    return lead_text, sections

def scrape_wikipedia(url: str) -> Optional[str]:
    """
    Scrape and process a Wikipedia page using the API
    """
    try:
        # Verify it's a Wikipedia URL
        if 'wikipedia.org' not in url:
            raise ValueError("This scraper is specifically for Wikipedia pages")

        # Parse the URL to get the title
        parsed_url = urlparse(url)
        title = parsed_url.path.split('/')[-1]
        
        # Configure API parameters
        api_url = f"https://{parsed_url.netloc}/w/api.php"
        headers = {
            'User-Agent': 'NeuroForge/1.0 (Research Project; contact@example.com) Python/3.8'
        }
        
        # First, get the sections
        section_params = {
            'action': 'parse',
            'page': title,
            'format': 'json',
            'prop': 'sections'
        }
        
        print(f"🌐 Fetching structure for: {title}")
        section_response = requests.get(api_url, headers=headers, params=section_params)
        section_response.raise_for_status()
        section_data = section_response.json()
        
        if 'error' in section_data:
            raise ValueError(f"Wikipedia API error: {section_data['error']}")
            
        # Get the lead section (introduction)
        lead_params = {
            'action': 'query',
            'titles': title,
            'prop': 'extracts',
            'exintro': True,
            'format': 'json'
        }
        
        print("📡 Fetching lead section...")
        lead_response = requests.get(api_url, headers=headers, params=lead_params)
        lead_response.raise_for_status()
        lead_data = lead_response.json()
        
        # Extract lead text
        page_id = next(iter(lead_data['query']['pages'].keys()))
        lead_html = lead_data['query']['pages'][page_id].get('extract', '')
        lead_soup = BeautifulSoup(lead_html, 'html.parser')
        lead_text = clean_text('\n\n'.join(p.get_text().strip() for p in lead_soup.find_all('p') if p.get_text().strip()))
        
        print(f"📝 Lead section length: {len(lead_text)} characters")
        
        # Process sections
        sections = []
        section_stack = []
        
        print("📚 Processing sections...")
        for section in section_data['parse']['sections']:
            # Skip unwanted sections
            if any(x in section['line'].lower() for x in [
                'references', 'external links', 'see also', 'notes',
                'further reading', 'bibliography', 'footnotes'
            ]):
                continue
                
            # Get section content
            content_params = {
                'action': 'parse',
                'page': title,
                'section': section['index'],
                'prop': 'text',
                'format': 'json'
            }
            
            content_response = requests.get(api_url, headers=headers, params=content_params)
            content_response.raise_for_status()
            content_data = content_response.json()
            
            if 'error' not in content_data:
                content_html = content_data['parse']['text']['*']
                content_soup = BeautifulSoup(content_html, 'html.parser')
                
                # Extract text content
                content_parts = []
                for elem in content_soup.find_all(['p', 'ul', 'ol']):
                    if elem.name == 'p':
                        text = elem.get_text().strip()
                        if text:
                            content_parts.append(text)
                    else:  # ul or ol
                        for item in elem.find_all('li', recursive=False):
                            text = item.get_text().strip()
                            if text:
                                content_parts.append(f"• {text}")
                
                section_content = clean_text('\n\n'.join(content_parts))
                
                if section_content.strip():
                    new_section = WikipediaSection(
                        title=section['line'],
                        level=int(section['level']),
                        content=section_content
                    )
                    
                    # Handle section hierarchy
                    while section_stack and section_stack[-1].level >= int(section['level']):
                        section_stack.pop()
                        
                    if section_stack:
                        section_stack[-1].subsections.append(new_section)
                    else:
                        sections.append(new_section)
                        
                    section_stack.append(new_section)
        
        print(f"📊 Processed {len(sections)} main sections")
        
        # Prepare the structured data
        data = {
            "url": url,
            "title": title.replace('_', ' '),
            "lead_text": lead_text,
            "sections": [s.to_dict() for s in sections],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": "wikipedia",
                "language": parsed_url.netloc.split('.')[0],
                "api_version": section_data['parse'].get('revid', 'unknown')
            }
        }
        
        # Save to file
        filename = f"scraped_data_{parsed_url.netloc.replace('.', '_')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Successfully scraped and saved to: {filename}")
        print(f"📊 Article sections: {len(sections)}")
        print(f"📝 Lead text length: {len(lead_text)} characters")
        
        return filename
        
    except requests.RequestException as e:
        print(f"❌ Error fetching content: {e}")
        return None
    except ValueError as e:
        print(f"❌ Value error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("Stack trace:", traceback.format_exc())
        return None

def main():
    """Main function to run the scraper"""
    if len(sys.argv) != 2:
        print("Usage: python scraper.py <wikipedia_url>")
        print("Example: python scraper.py https://en.wikipedia.org/wiki/Artificial_intelligence")
        sys.exit(1)
    
    url = sys.argv[1]
    filename = scrape_wikipedia(url)
    
    if filename:
        print(f"\n🎉 Wikipedia scraping completed! Data saved to: {filename}")
    else:
        print("\n💥 Scraping failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 