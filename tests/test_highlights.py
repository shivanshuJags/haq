from core.highlights import highlights


def test_state_schemes_come_first_in_popular():
    bihar = highlights("IN", "Bihar")
    assert bihar.state > 0
    assert bihar.popular[0].is_state_scheme
    assert bihar.schemes == bihar.national + bihar.state


def test_states_without_data_get_national_schemes():
    # We only hold UP and Bihar state data; elsewhere = national schemes (plus the few central
    # schemes that are limited to a list of states, which may include it)
    elsewhere = highlights("IN", "Maharashtra")
    assert elsewhere.national == highlights("IN", None).national
    assert elsewhere.state < 10
    assert all(not item.is_state_scheme for item in elsewhere.popular)


def test_recent_is_dated_newest_first():
    for country in ("IN", "UK"):
        dates = [item.date for item in highlights(country, None).recent]
        assert dates and dates == sorted(dates, reverse=True)


def test_answers_are_cached_and_sent_with_cache_headers():
    from fastapi.testclient import TestClient

    from api.main import app

    assert highlights("IN", "Bihar") is highlights("IN", "Bihar")  # worked out once, then from memory
    with TestClient(app) as client:
        response = client.get("/api/highlights", params={"country": "UK"})
    assert response.status_code == 200
    assert "max-age=3600" in response.headers["cache-control"]
