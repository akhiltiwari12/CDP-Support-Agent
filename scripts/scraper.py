import requests
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import urljoin, urlparse

class DocumentationScraper:
    def __init__(self, base_url, name):
        self.base_url = base_url
        self.name = name
        self.visited_urls = set()
        self.documents = []
        
    def is_valid_url(self, url):
        """Check if URL belongs to the same documentation domain"""
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        return parsed_url.netloc == parsed_base.netloc and '/docs/' in url
    
    def extract_content(self, url):
        """Extract content from a documentation page"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove navigation, headers, footers, etc.
            for element in soup.select('nav, header, footer, .sidebar, .menu'):
                element.decompose()
            
            # Extract main content
            main_content = soup.select_one('main, .main-content, article, .documentation-content')
            
            if not main_content:
                main_content = soup.body
            
            # Extract title
            title_element = soup.select_one('h1')
            title = title_element.text.strip() if title_element else url
            
            # Create document
            document = {
                'source': self.name,
                'url': url,
                'title': title,
                'content': main_content.get_text(separator='\n').strip(),
                'html': str(main_content)
            }
            
            return document
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def find_links(self, url):
        """Find all documentation links on a page"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)
                
                if self.is_valid_url(full_url) and full_url not in self.visited_urls:
                    links.append(full_url)
                    
            return links
        except Exception as e:
            print(f"Error finding links on {url}: {e}")
            return []
    
    def crawl(self, url, max_pages=1000):
        """Crawl documentation pages starting from url"""
        if len(self.documents) >= max_pages or url in self.visited_urls:
            return
            
        print(f"Crawling: {url}")
        self.visited_urls.add(url)
        
        document = self.extract_content(url)
        if document:
            self.documents.append(document)
            
        links = self.find_links(url)
        for link in links:
            self.crawl(link, max_pages)
    
    def save_documents(self, output_dir):
        """Save scraped documents to JSON files"""
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{self.name}_docs.json")
        
        with open(output_file, 'w') as f:
            json.dump(self.documents, f, indent=2)
            
        print(f"Saved {len(self.documents)} documents to {output_file}")

# Usage
def scrape_all_cdps():
    cdps = [
        {'name': 'segment', 'url': 'https://segment.com/docs/?ref=nav'},
        {'name': 'mparticle', 'url': 'https://docs.mparticle.com/'},
        {'name': 'lytics', 'url': 'https://docs.lytics.com/'},
        {'name': 'zeotap', 'url': 'https://docs.zeotap.com/home/en-us/'}
    ]
    
    for cdp in cdps:
        scraper = DocumentationScraper(cdp['url'], cdp['name'])
        scraper.crawl(cdp['url'], max_pages=500)  # Limit to 500 pages per CDP
        scraper.save_documents('data/raw')

if __name__ == "__main__":
    scrape_all_cdps()