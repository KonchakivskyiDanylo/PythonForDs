import pymongo
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from get_data.isw import html_extractor, isw_data_scraper
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

ISW_FEATURES = [
    "advanced", "air", "army", "artillery", "authority", "avdiivka", "bakhmut",
    "belarus", "border", "brigade", "command", "confirmed", "district", "division",
    "drone", "element", "footage", "frontline", "geolocated", "head", "information",
    "kreminna", "kremlin", "kupyansk", "milblogger", "milbloggers", "missile", "mod",
    "motorized", "northeast", "noted", "observed", "occupation", "operating", "personnel",
    "president", "published", "putin", "recently", "regiment", "rifle", "significant",
    "southeast", "southwest", "state", "unit", "unspecified", "wagner", "within", "would"
]

MONTHS = {
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
}


def clean_text(text: str) -> str:
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = text.lower()
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"\b\w{1,2}\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess_text(text: str, stop_words: set, months: set) -> str:
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in stop_words and t not in months]
    lemmatizer = WordNetLemmatizer()
    lemmatized = [lemmatizer.lemmatize(word) for word in tokens]
    return " ".join(lemmatized)


def get_latest_isw_html(db_name: str = "PythonForDs", collection_name: str = "isw_html") -> str:
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db[collection_name]
    latest_doc = list(collection.find())[-1]
    return latest_doc["html_content"]


def vectorize_isw_features(text: str, features: list) -> pd.DataFrame:
    vectorizer = TfidfVectorizer(vocabulary=features)

    tfidf_matrix = vectorizer.fit_transform([text])
    return pd.DataFrame(tfidf_matrix.toarray(), columns=vectorizer.get_feature_names_out())


def main():
    # Uncomment if you run for the first time
    # nltk.download("punkt")
    # nltk.download("punkt_tab")
    # nltk.download("stopwords")
    # nltk.download("wordnet")

    stop_words = set(stopwords.words("english"))

    try:
        isw_data_scraper.main()

        raw_html = get_latest_isw_html()
        extracted_text = html_extractor.extract_text_from_html(raw_html)
        cleaned_raw_text = html_extractor.clean_extracted_text(extracted_text)
        cleaned_text = clean_text(cleaned_raw_text)

        final_text = preprocess_text(cleaned_text, stop_words, MONTHS)

        return vectorize_isw_features(final_text, ISW_FEATURES)

    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def chill():
    pass


if __name__ == "__main__":
    main()
