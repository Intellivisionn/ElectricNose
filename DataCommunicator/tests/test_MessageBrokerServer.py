import asyncio
import json
import pytest

import DataCommunicator.source.MessageBrokerServer as m_mod
from DataCommunicator.source.MessageBrokerServer import MessageBrokerServer

class DummyWebSocket:
    """
    Fake WebSocket supporting:
      - .recv() for initial registration messages
      - async iteration (__aiter__/__anext__) over messages pushed via .push()
      - .send() to record outgoing messages
      - .close() to record that it was closed
    """
    def __init__(self, recv_messages):
        # Queue of JSON strings to return from .recv()
        self._recv = asyncio.Queue()
        for msg in recv_messages:
            self._recv.put_nowait(json.dumps(msg))

        # Queue of JSON strings to yield from __anext__()
        self._iter = asyncio.Queue()
        self.sent = []
        self.closed = False

    async def recv(self):
        return await self._recv.get()

    async def send(self, msg):
        self.sent.append(json.loads(msg))

    async def close(self):
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            data = await asyncio.wait_for(self._iter.get(), timeout=0.05)
            return data
        except asyncio.TimeoutError:
            raise StopAsyncIteration

    def push(self, packet: dict):
        """Push a JSON-serializable dict to be yielded by __anext__()."""
        self._iter.put_nowait(json.dumps(packet))


@pytest.mark.asyncio
async def test_route_existing_client():
    broker = MessageBrokerServer()
    ws = DummyWebSocket([])
    broker.connections['alice'] = ws

    await broker.route('bob', 'alice', {'hello': 123})
    assert ws.sent == [{'from': 'bob', 'payload': {'hello': 123}}]


@pytest.mark.asyncio
async def test_route_missing_client(capfd):
    broker = MessageBrokerServer()
    await broker.route('bob', 'nobody', {'x': 1})

    out = capfd.readouterr().out
    assert 'No such client to route to: nobody' in out


@pytest.mark.asyncio
async def test_broadcast_to_all():
    broker = MessageBrokerServer()
    ws1 = DummyWebSocket([])
    ws2 = DummyWebSocket([])
    broker.connections['a'] = ws1
    broker.connections['b'] = ws2

    await broker.broadcast('me', {'k': 'v'})
    expected = {'from': 'me', 'payload': {'k': 'v'}}

    assert ws1.sent == [expected]
    assert ws2.sent == [expected]


@pytest.mark.asyncio
async def test_handler_register_and_cleanup(capfd):
    ws = DummyWebSocket([{'type': 'register', 'name': 'tester'}])
    broker = MessageBrokerServer()

    await broker.handler(ws, path=None)

    # After disconnect, tester should be removed
    assert 'tester' not in broker.connections

    out = capfd.readouterr().out
    assert '[Broker] Registered client: tester' in out
    assert '[Broker] Client disconnected: tester' in out


@pytest.mark.asyncio
async def test_handler_bad_registration_closes_socket(capfd):
    ws = DummyWebSocket([{'type': 'foo', 'name': 'alice'}])
    broker = MessageBrokerServer()

    await broker.handler(ws)

    assert ws.closed
    out = capfd.readouterr().out
    assert 'Registered client' not in out


@pytest.mark.asyncio
async def test_handler_routes_and_broadcasts(capfd, monkeypatch):
    # Set up a sender that registers as "bob"
    ws_sender = DummyWebSocket([{'type': 'register', 'name': 'bob'}])
    broker = MessageBrokerServer()

    # Pre-register a receiver so route() has a target
    ws_receiver = DummyWebSocket([])
    broker.connections['receiver'] = ws_receiver

    called = []
    async def fake_route(frm, to, p):
        called.append(('route', frm, to, p))
    async def fake_broadcast(frm, p):
        called.append(('broadcast', frm, p))

    monkeypatch.setattr(broker, 'route', fake_route)
    monkeypatch.setattr(broker, 'broadcast', fake_broadcast)

    # Now push two messages for the async loop
    ws_sender.push({'to': 'receiver', 'from': 'bob', 'payload': {'x': 1}})
    ws_sender.push({'to': 'broadcast', 'from': 'bob', 'payload': {'y': 2}})

    await broker.handler(ws_sender)

    assert ('route', 'bob', 'receiver', {'x': 1}) in called
    assert ('broadcast', 'bob', {'y': 2}) in called

    out = capfd.readouterr().out
    assert '[Broker] Registered client: bob' in out
    assert '[Broker] Client disconnected: bob' in out


def test_start_invokes_serve_and_run(monkeypatch):
    # Stub out _serve coroutine
    async def fake__serve(self):
        pass

    monkeypatch.setattr(MessageBrokerServer, '_serve', fake__serve)

    recorded = {}
    def fake_run(coro):
        # record the code object
        recorded['code'] = coro.cr_code
        # drive the coroutine to completion so it's not "never awaited"
        try:
            coro.send(None)
        except StopIteration:
            pass
        return None

    # Patch asyncio.run in the module namespace
    monkeypatch.setattr(m_mod.asyncio, 'run', fake_run)

    broker = MessageBrokerServer()
    broker.start()

    assert recorded['code'] is fake__serve.__code__