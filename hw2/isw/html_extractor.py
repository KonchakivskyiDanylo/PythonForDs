import pymongo
from bs4 import BeautifulSoup
import argparse
import re


def validate_mongodb(mongo):
    if not mongo.startswith('mongodb://') and not mongo.startswith('mongodb+srv://'):
        raise argparse.ArgumentTypeError("Invalid MongoDB format")
    return mongo


def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove specific elements that contain metadata
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.extract()

    # Find the main content - looking for div with class 'field-item' which seems to contain the actual article
    main_content = soup.find('div', class_='field-item even', property='content:encoded')

    if not main_content:
        # Fallback to general content div or body
        main_content = soup.find('div', class_='content') or soup.body

    if main_content:
        # Extract all paragraphs with their original order
        paragraphs = []
        for p in main_content.find_all('p'):
            paragraphs.append(p.get_text().strip())

        return paragraphs

    return []


def clean_extracted_text(paragraphs):
    if not paragraphs:
        return ""

    # Identify metadata paragraphs (first paragraphs with author names and dates)
    skip_paragraphs = 0
    metadata_patterns = [
        # Pattern for author names
        r'^[A-Z][a-z]+ [A-Z][a-z]+',
        # Pattern for dates
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+',
        # Pattern for time
        r'\d+:\d+\s*(am|pm|EST)',
        # Pattern for italicized metadata (like "Press")
        r'^ISW Press$'
    ]

    # Check first paragraphs for metadata patterns
    for i, paragraph in enumerate(paragraphs):
        if i > 2:  # Normally metadata is in first 1-2 paragraphs
            break

        # Check if paragraph matches any metadata pattern
        is_metadata = any(re.search(pattern, paragraph) for pattern in metadata_patterns)

        # If it's short and looks like metadata, skip it
        if is_metadata and len(paragraph.split()) < 20:
            skip_paragraphs = i + 1
        else:
            # Found first real content paragraph
            break

    # Join remaining paragraphs (starting after metadata)
    cleaned_paragraphs = paragraphs[skip_paragraphs:]
    if not cleaned_paragraphs:
        # Fallback - if we somehow removed all paragraphs, return original
        return " ".join(paragraphs)

    text = " ".join(cleaned_paragraphs)

    # Further cleaning
    # delete references like [1]
    text = re.sub(r'\[\d+\]', '', text)

    # drop images in the text
    text = re.sub(
        r'(Click here to expand the image below\. Satellite image ©\d{4} Maxar Technologies\.)\s*', '', text
    )

    # drop links in the end
    split_point = re.search(r'https?://', text)
    if split_point:
        text = text[:split_point.start()].rstrip()

    return text.strip()


def process_documents(mongo, database, input_collection, output_collection):
    try:
        client = pymongo.MongoClient(mongo)
        db = client[database]
        input_coll = db[input_collection]
        output_coll = db[output_collection]
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        return

    documents = input_coll.find({})
    count = 0
    for doc in documents:
        try:
            if output_coll.find_one({"date": doc["date"]}):
                continue

            html_content = doc["html_content"]
            extracted_paragraphs = extract_text_from_html(html_content)
            cleaned_text = clean_extracted_text(extracted_paragraphs)

            # Debug output - print first and last part of text
            if cleaned_text:
                print(f"\nDocument from {doc['date']}:")
                print(f"Starts with: {cleaned_text[:100]}...")

            text_doc = {
                "date": doc["date"],
                "extracted_text": cleaned_text
            }
            output_coll.insert_one(text_doc)
            count += 1

        except Exception as e:
            print(f"Error processing document: {e}")

    print(f"\nTotal documents processed: {count}")


def main():
    parser = argparse.ArgumentParser(description="ISW HTML to Text Extractor")
    parser.add_argument("--mongo", default="mongodb://localhost:27017/",
                        type=validate_mongodb,
                        help="MongoDB connection string (default: localhost)")
    parser.add_argument("--database", default="PythonForDs",
                        help="MongoDB database name (default: PythonForDs)")
    parser.add_argument("--input-collection", default="isw_html",
                        help="Input MongoDB collection name (default: isw_html)")
    parser.add_argument("--output-collection", default="isw_report",
                        help="Output MongoDB collection name (default: isw_report)")

    args = parser.parse_args()
    process_documents(args.mongo, args.database, args.input_collection, args.output_collection)


if __name__ == "__main__":
    main()