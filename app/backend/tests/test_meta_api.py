import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_meta_endpoint():
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()
    
    assert "areas" in data
    assert "institutions" in data
    assert "years" in data
    assert "subtemas" in data
    
    # Assert they are lists
    assert isinstance(data["areas"], list)
    assert isinstance(data["institutions"], list)

def test_meta_endpoint_with_filters():
    response = client.get("/api/meta?area=Cirurgia")
    assert response.status_code == 200
    data = response.json()
    
    assert "areas" in data
    assert "institutions" in data
