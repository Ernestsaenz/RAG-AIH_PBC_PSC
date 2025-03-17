# components/data_processor.py
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pathlib import Path
import json
import hashlib

class DataProcessor:
    def __init__(self):
        self.urls = [
            # Keep your existing URLs here
            #"INSERT URL WITH YOUR OWN CLINICAL GUIDELINE OR DRUGS SAFETY REPOSIROTY",
        ]
        # Using RecursiveCharacterTextSplitter for better chunk boundaries
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=300,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.batch_size = 250
        self.cache_dir = Path("./document_cache")
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_path(self, url):
        """Generate cache file path for a URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    def fetch_url(self, url):
        """Fetch content from URL with caching"""
        cache_path = self.get_cache_path(url)

        # Check cache first
        if cache_path.exists():
            print(f"Loading cached content for {url}")
            with open(cache_path, 'r') as f:
                return json.load(f)['content']

        # Fetch if not cached
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.text

            # Cache the content
            with open(cache_path, 'w') as f:
                json.dump({'url': url, 'content': content}, f)

            return content
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    def process_documents(self):
        """Process documents with improved chunking"""
        all_documents = []

        for url in self.urls:
            print(f"Processing URL: {url}")
            content = self.fetch_url(url)
            if content:
                chunks = self.text_splitter.split_text(content)
                for chunk in chunks:
                    document = Document(page_content=chunk)
                    all_documents.append(document)
                print(f"Successfully processed {len(chunks)} chunks from {url}")
            else:
                print(f"Failed to process {url}")

        print(f"Total documents collected: {len(all_documents)}")

        # Yield documents in batches
        for i in range(0, len(all_documents), self.batch_size):
            batch = all_documents[i:i + self.batch_size]
            yield batch