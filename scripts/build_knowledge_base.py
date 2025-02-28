# scripts/build_knowledge_base.py
from scraper import scrape_all_cdps
from processor import process_and_index_documents

if __name__ == "__main__":
    print("Step 1: Scraping documentation...")
    scrape_all_cdps()
    
    print("Step 2: Processing and indexing documents...")
    process_and_index_documents()
    
    print("Knowledge base built successfully!")