import pymongo
from bs4 import BeautifulSoup
import argparse


def validate_mongodb(mongo):
    if not mongo.startswith('mongodb://') and not mongo.startswith('mongodb+srv://'):
        raise argparse.ArgumentTypeError("Invalid MongoDB format")
    return mongo


def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()

    main_content = soup.find('div', class_='content') or soup.body

    if main_content:
        paragraphs = main_content.find_all('p')
        text = '\n\n'.join([p.get_text().strip() for p in paragraphs])
        headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        heading_text = '\n\n'.join([h.get_text().strip() for h in headings])
        full_text = heading_text + '\n\n' + text
        return ' '.join(full_text.split())

    return ""


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
    for doc in documents:
        try:
            if output_coll.find_one({"date": doc["date"]}):
                continue
            html_content = doc["html_content"]
            extracted_text = extract_text_from_html(html_content)
            text_doc = {
                "date": doc["date"],
                "extracted_text": extracted_text
            }
            output_coll.insert_one(text_doc)

        except Exception as e:
            print(f"Error processing document: {e}")


def main():
    parser = argparse.ArgumentParser(description="ISW HTML to Text Extractor")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017/",
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
