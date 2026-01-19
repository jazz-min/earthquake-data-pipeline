from unittest.mock import patch

from app.services.usgs_client import USGSClientError


def test_live_fallback_when_usgs_fails(client):
    """Test that /earthquakes/live falls back to DB when USGS fails."""
    with patch("app.main.fetch_usgs_earthquakes") as mock_fetch:
        mock_fetch.side_effect = USGSClientError("Connection timeout")

        # Need to also mock the DB calls since we don't have a real DB in tests
        with patch("app.main.earthquake_repo.get_earthquakes") as mock_get:
            mock_get.return_value = []

            with patch("app.main.earthquake_repo.get_max_event_time") as mock_time:
                mock_time.return_value = None

                response = client.get("/earthquakes/live?limit=5")

                assert response.status_code == 200
                data = response.json()
                assert data["source"] == "db_fallback"
                assert data["fallback_reason"] is not None
                assert "timeout" in data["fallback_reason"].lower()


def test_live_limit_validation(client):
    """Test that live endpoint validates limit parameter."""
    response = client.get("/earthquakes/live?limit=201")
    assert response.status_code == 422
