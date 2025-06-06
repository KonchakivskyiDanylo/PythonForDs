import pytest
from server import app

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
