def test_earthquakes_limit_validation(client):
    """Test that limit > 200 returns 422 validation error."""
    response = client.get("/earthquakes?limit=201")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_earthquakes_offset_validation(client):
    """Test that offset > 5000 returns 422 validation error."""
    response = client.get("/earthquakes?offset=5001")
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_earthquakes_magnitude_validation(client):
    """Test that magnitude > 10 returns 422 validation error."""
    response = client.get("/earthquakes?min_magnitude=11")
    assert response.status_code == 422


def test_earthquakes_bbox_format_validation(client):
    """Test that invalid bbox format returns 422 validation error."""
    response = client.get("/earthquakes?bbox=invalid")
    assert response.status_code == 422
