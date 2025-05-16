import pytest

from source.BaseDataClient import BaseDataClient

class DummyConn:
    def __init__(self):
        self.connect_called = False
        self.client = None
    def set_client(self, client):
        self.client = client
    async def connect(self):
        self.connect_called = True

class MyClient(BaseDataClient):
    def __init__(self, name, connection):
        super().__init__(name, connection)
        self.ran = False
        self.messages = []

    async def run(self):
        # simple once-through
        self.ran = True

    async def on_message(self, frm, payload):
        self.messages.append((frm, payload))

@pytest.mark.asyncio
async def test_set_client_and_start():
    conn = DummyConn()
    client = MyClient('me', conn)
    # constructor should have called set_client
    assert conn.client is client

    # now start() should call connect() then run()
    await client.start()
    assert conn.connect_called is True
    assert client.ran is True

@pytest.mark.asyncio
async def test_on_message_delegation():
    conn = DummyConn()
    client = MyClient('me', conn)
    # direct on_message
    await client.on_message('you', {'a': 1})
    assert client.messages == [('you', {'a': 1})]
