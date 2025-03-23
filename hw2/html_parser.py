import pymongo
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["PythonForDs"]
collection = db["isw_html"]
text_collection = db["isw_report"]


def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()

    # Get the main content - adjust selectors based on ISW's HTML structure
    # This is an example, you may need to customize based on the actual website structure
    main_content = soup.find('div', class_='content')

    if not main_content:
        # Fallback to body if specific content div not found
        main_content = soup.body

    if main_content:
        # Extract all paragraphs
        paragraphs = main_content.find_all('p')
        text = '\n\n'.join([p.get_text().strip() for p in paragraphs])

        # Extract headings for structure
        headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        heading_text = '\n\n'.join([h.get_text().strip() for h in headings])

        # Combine heading and paragraph text
        full_text = heading_text + '\n\n' + text

        # Clean up extra whitespace
        return ' '.join(full_text.split())

    return ""


def process_all_documents():
    """Process all HTML documents in the MongoDB collection."""
    # Get all documents
    documents = collection.find({})

    processed_count = 0

    # Create output directory for text files if needed
    output_dir = "extracted_texts"
    os.makedirs(output_dir, exist_ok=True)

    # Process each document
    for doc in documents:
        doc_id = doc["_id"]
        date_str = doc["date"].strftime("%Y-%m-%d")

        # Check if we've already processed this document
        if text_collection.find_one({"original_id": doc_id}):
            print(f"Document {date_str} already processed, skipping...")
            continue

        # Extract text
        html_content = doc["html_content"]
        extracted_text = extract_text_from_html(html_content)

        if not extracted_text:
            print(f"No text extracted from document {date_str}")
            continue

        # Save to file
        file_path = os.path.join(output_dir, f"isw_report_{date_str}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)

        # Save to MongoDB
        text_doc = {
            "original_id": doc_id,
            "date": doc["date"],
            "url": doc["url"],
            "extracted_text": extracted_text,
            "extracted_at": datetime.now(),
            "file_path": file_path
        }

        text_collection.insert_one(text_doc)
        processed_count += 1

        print(f"Processed document for {date_str}")

    # Create metadata file
    metadata = {
        "total_documents": processed_count,
        "extraction_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "Institute for the Study of War - Russian Offensive Campaign Assessment"
    }

    with open(os.path.join(output_dir, "metadata.json"), 'w') as f:
        json.dump(metadata, f, indent=2, default=str)

    return processed_count


if __name__ == "__main__":
    print("Starting text extraction process...")
    processed = process_all_documents()
    print(f"Extraction completed. Processed {processed} documents.")
