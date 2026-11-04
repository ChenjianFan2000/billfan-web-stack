"""Relay endpoints for the line-story lesson."""
from fastapi.testclient import TestClient

from services.line_sync.app import app

client = TestClient(app)


def test_health():
    assert client.get('/api/health').json()['ok'] is True


def test_room_lifecycle():
    room = client.post('/api/rooms').json()['room']
    assert room and client.get('/api/health').json()['rooms'] >= 1

    qr = client.get('/api/rooms/{}/qr.svg'.format(room))
    assert qr.status_code == 200 and b'xmlns="http://www.w3.org/2000/svg"' in qr.content

    assert client.post('/api/rooms/{}/state'.format(room), json={'index': 4, 'cue': {'id': 'warmth'}}).json() == {'ok': True}
    assert client.post('/api/rooms/{}/command'.format(room), json={'command': 'next'}).json() == {'ok': True}
    assert client.post('/api/rooms/{}/command'.format(room), json={'command': 'nonsense'}).status_code == 400
    assert client.post('/api/rooms/{}/state'.format(room), json=[1, 2]).status_code == 400

    # The follow stream lives only for known rooms. (Its pushed frames are covered
    # end-to-end against the running service, not by TestClient streaming.)
    assert client.get('/api/rooms/unknown/stream').status_code == 404
    assert client.post('/api/rooms/unknown/state', json={'index': 0}).status_code == 404
