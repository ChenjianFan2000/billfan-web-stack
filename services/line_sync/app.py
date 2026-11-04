"""Relay for the 《童年》 line-story lesson.

The projected page publishes its state into a room; phones that scanned the room
QR follow the same cue over SSE and may send transport commands back.
"""
import asyncio
import io
import json
import re
import secrets
import time

import segno
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

ROOM_TTL = 4 * 3600
MAX_ROOMS = 300
MAX_STATE = 256 * 1024
MAX_BODY = 8 * 1024
KEEPALIVE = 15
COMMANDS = ('next', 'prev', 'jump', 'timer', 'reset-timer', 'blank', 'motion', 'finish')
ROOM_RE = re.compile(r'^[A-Za-z0-9_-]{4,64}$')

app = FastAPI(title='line-story sync')


class Room:
    def __init__(self, room_id):
        self.id = room_id
        self.state = None
        self.updated = time.time()
        self.subscribers = set()

    def touch(self):
        self.updated = time.time()


rooms = {}


def room_or_404(room_id):
    if not ROOM_RE.match(room_id):
        raise HTTPException(status_code=404, detail='room not found')
    room = rooms.get(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail='room not found')
    return room


def public_url(request, room_id):
    scheme = (request.headers.get('x-forwarded-proto') or request.url.scheme or 'https').split(',')[0].strip()
    host = request.headers.get('x-forwarded-host') or request.headers.get('host') or request.url.netloc
    host = re.sub(r'[^A-Za-z0-9._:\-]', '', host.strip()) or 'tongnian.billfan.cn'
    return '{}://{}/subtitles.html?room={}'.format(scheme, host, room_id)


def frame(event, data):
    body = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return 'event: {}\ndata: {}\n\n'.format(event, body).encode('utf-8')


def broadcast(room, event, data):
    for queue in list(room.subscribers):
        try:
            queue.put_nowait({'event': event, 'data': data})
        except asyncio.QueueFull:
            pass


def prune():
    now = time.time()
    for room in [r for r in rooms.values() if not r.subscribers and now - r.updated > ROOM_TTL]:
        rooms.pop(room.id, None)
    if len(rooms) > MAX_ROOMS:
        extra = sorted(rooms.values(), key=lambda r: r.updated)[:len(rooms) - MAX_ROOMS]
        for room in extra:
            rooms.pop(room.id, None)


async def read_json(request, limit):
    body = await request.body()
    if len(body) > limit:
        return None
    try:
        return json.loads(body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return None


PRUNER = None


@app.on_event('startup')
async def start_pruning():
    global PRUNER

    async def loop():
        while True:
            await asyncio.sleep(600)
            prune()

    PRUNER = asyncio.ensure_future(loop())


@app.on_event('shutdown')
async def stop_pruning():
    if PRUNER is not None:
        PRUNER.cancel()


@app.get('/api/health')
async def health():
    return {'ok': True, 'rooms': len(rooms)}


@app.post('/api/rooms')
async def create_room(request: Request):
    prune()
    room_id = secrets.token_urlsafe(6)
    rooms[room_id] = Room(room_id)
    return {'room': room_id, 'url': public_url(request, room_id)}


@app.get('/api/rooms/{room_id}/qr.svg')
async def room_qr(room_id: str, request: Request):
    room = room_or_404(room_id)
    room.touch()
    code = segno.make(public_url(request, room_id), error='m')
    buffer = io.BytesIO()
    # save() writes a standalone SVG document (with xmlns) that <img> can render.
    code.save(buffer, kind='svg', scale=6)
    return Response(content=buffer.getvalue(), media_type='image/svg+xml',
                    headers={'Cache-Control': 'no-store'})


@app.post('/api/rooms/{room_id}/state')
async def publish_state(room_id: str, request: Request):
    room = room_or_404(room_id)
    state = await read_json(request, MAX_STATE)
    if not isinstance(state, dict):
        return JSONResponse({'error': 'state must be a JSON object'}, status_code=400)
    room.state = state
    room.touch()
    broadcast(room, 'state', state)
    return {'ok': True}


@app.post('/api/rooms/{room_id}/command')
async def publish_command(room_id: str, request: Request):
    room = room_or_404(room_id)
    data = await read_json(request, MAX_BODY)
    if not isinstance(data, dict) or data.get('command') not in COMMANDS:
        return JSONResponse({'error': 'unknown command'}, status_code=400)
    index = data.get('index')
    room.touch()
    broadcast(room, 'command', {'command': data['command'], 'index': index if isinstance(index, int) else None})
    return {'ok': True}


@app.get('/api/rooms/{room_id}/stream')
async def stream(room_id: str):
    room = room_or_404(room_id)
    queue = asyncio.Queue(maxsize=64)
    room.subscribers.add(queue)
    room.touch()

    async def events():
        try:
            if room.state is not None:
                yield frame('state', room.state)
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE)
                except asyncio.TimeoutError:
                    yield b': keep-alive\n\n'
                    continue
                yield frame(item['event'], item['data'])
        finally:
            room.subscribers.discard(queue)

    return StreamingResponse(events(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})
