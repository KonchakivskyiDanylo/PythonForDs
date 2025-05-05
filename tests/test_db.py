import mongomock

def test_mongodb_connection():
    client = mongomock.MongoClient()
    db = client["PythonForDs"]
    db["prediction"].insert_one({"sample": "data"})
    assert "prediction" in db.list_collection_names()
