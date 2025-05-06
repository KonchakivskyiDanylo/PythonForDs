import pytest
from server import app
import pymongo

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_alarms_endpoint(client):
    response = client.get('/alarms')
    assert response.status_code == 200
    assert response.get_json() is not None


def test_can_insert_and_find_document():
    client = pymongo.MongoClient("mongodb://localhost:27017")
    db = client["PythonForDs"]
    collection = db["prediction"]

    test_doc = {"_id": "test_id", "value": 42}
    collection.insert_one(test_doc)

    result = collection.find_one({"_id": "test_id"})
    assert result is not None
    assert result["value"] == 42

    collection.delete_one({"_id": "test_id"})

