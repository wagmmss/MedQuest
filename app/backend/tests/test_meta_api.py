def test_meta_endpoint(client):
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json
    
    assert "areas" in data
    assert "institutions" in data
    assert "years" in data
    assert "subtemas" in data
    assert "sources" in data
    assert "specialties" in data
    
    # Assert they are lists
    assert isinstance(data["areas"], list)
    assert isinstance(data["institutions"], list)
    assert isinstance(data["years"], list)
    assert isinstance(data["subtemas"], list)
    assert isinstance(data["sources"], list)
    assert isinstance(data["specialties"], list)

def test_meta_endpoint_with_filters(client):
    response1 = client.get("/api/meta?institution=USP-SP")
    assert response1.status_code == 200
    assert response1.json["total_questions"] == 1
    
    response2 = client.get("/api/meta?institution=USP-SP&institution=USP-RP")
    assert response2.status_code == 200
    assert response2.json["total_questions"] == 2
