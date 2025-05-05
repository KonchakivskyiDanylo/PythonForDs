import pymongo
import mongomock

def test_mongodb_connection():
    client = mongomock.MongoClient()
    db = client["PythonForDs"]
    assert "prediction" in db.list_collection_names()
