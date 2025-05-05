import pymongo

def test_mongodb_connection():
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["PythonForDs"]
    assert "prediction" in db.list_collection_names()
