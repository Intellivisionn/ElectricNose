import asyncio
import json
import pytest

import source.WebSocketConnection as ws_module
from source.WebSocketConnection import WebSocketConnection
from asyncio import QueueEmpty

class FakeWS:
    def __init__(self):
        self.sent = []
        self._incoming = asyncio.Queue()
        self.closed = False
        self._popped = False  # track whether we've yielded once

    async def send(self, msg):
        self.sent.append(json.loads(msg))

    # emulate messages pushed by test
    def push(self, frm, payload):
        self._incoming.put_nowait(json.dumps({'from': frm, 'payload': payload}))

    def __aiter__(self):
        return self

    async def __anext__(self):
        # if we've already yielded once or there's nothing queued, stop iteration
        if self._popped:
            raise StopAsyncIteration
        try:
            packed = self._incoming.get_nowait()
        except QueueEmpty:
            raise StopAsyncIteration
        self._popped = True
        return packed


@pytest.mark.asyncio
async def test_set_client_and_send(monkeypatch):
    fake_ws = FakeWS()
    # patch module-level websockets.connect → returns our fake
    monkeypatch.setattr(
        ws_module,
        'websockets',
        type('FakeWSMod', (), {
            'connect': lambda uri: asyncio.sleep(0, result=fake_ws)
        })
    )

    conn = WebSocketConnection('ws://test')

    class DummyClient:
        def __init__(self):
            self.name = 'client1'
            self.received = []
        async def on_message(self, frm, payload):
            self.received.append((frm, payload))

    client = DummyClient()
    conn.set_client(client)

    # connect() should send registration and start (but then immediately stop) the listener
    await conn.connect()
    assert fake_ws.sent == [{'type': 'register', 'name': 'client1'}]

    # send()
    fake_ws.sent.clear()
    await conn.send('bob', {'foo': 'bar'})
    assert fake_ws.sent == [{'to': 'bob', 'from': 'client1', 'payload': {'foo': 'bar'}}]

    # broadcast()
    fake_ws.sent.clear()
    await conn.broadcast({'x': 5})
    assert fake_ws.sent == [{'to': 'broadcast', 'from': 'client1', 'payload': {'x': 5}}]


@pytest.mark.asyncio
async def test_listener_delegates_to_client(monkeypatch):
    fake_ws = FakeWS()
    monkeypatch.setattr(
        ws_module,
        'websockets',
        type('FakeWSMod', (), {
            'connect': lambda uri: asyncio.sleep(0, result=fake_ws)
        })
    )

    conn = WebSocketConnection('ws://dummy')

    class DummyClient:
        def __init__(self):
            self.name = 'cli'
            self.received = []
        async def on_message(self, frm, payload):
            self.received.append((frm, payload))

    client = DummyClient()
    conn.set_client(client)
    await conn.connect()

    # push a message, listener will pick it up once then exit
    fake_ws.push('alice', {'ping': True})
    await asyncio.sleep(0.01)

    assert client.received == [('alice', {'ping': True})]