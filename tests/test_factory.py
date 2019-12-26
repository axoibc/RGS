from app import create_app


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_range(client):
    response = client.get('/rng/0/100?count=1')
    assert response.data is list



