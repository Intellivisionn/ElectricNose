import asyncio
import json
import websockets

class MessageBrokerServer:
    """
    The central broker. Clients register on connect, then send JSON
    messages of the form {'to': str, 'from': str, 'payload': dict}.
    """
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.topics: dict[str, set[str]] = {}  # topic -> set of client names
        self.connections: dict[str, websockets.WebSocketServerProtocol] = {}

    async def handler(self, websocket, path=None):
        # First message must be registration: {"type":"register","name": "<client-name>"}
        try:
            register = await websocket.recv()
            data = json.loads(register)
            if data.get('type') != 'register' or 'name' not in data:
                await websocket.close()
                return

            name = data['name']
            self.connections[name] = websocket
            print(f'[Broker] Registered client: {name}')

            async for message in websocket:
                msg = json.loads(message)
                mtype = msg.get('type')

                if mtype == 'subscribe':
                    topic = msg['topic']
                    name = msg['name']
                    self.topics.setdefault(topic, set()).add(name)
                    print(f'[Broker] {name} subscribed to {topic}')

                elif mtype == 'unsubscribe':
                    topic = msg['topic']
                    name = msg['name']
                    self.topics.get(topic, set()).discard(name)
                    print(f'[Broker] {name} unsubscribed from {topic}')

                elif mtype == 'publish':
                    topic = msg['topic']
                    frm = msg['from']
                    payload = msg['payload']
                    await self.publish(topic, frm, payload)

                else:
                    # fallback to old style direct message
                    to   = msg.get('to')
                    frm  = msg.get('from')
                    payload = msg.get('payload')
                    if to == 'broadcast':
                        await self.broadcast(frm, payload)
                    else:
                        await self.route(frm, to, payload)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            # Log unexpected errors without killing the server
            print(f'[Broker] Connection handler failed: {e}')
        finally:
            # clean up if registered
            for client_name, ws in list(self.connections.items()):
                if ws is websocket:
                    del self.connections[client_name]
                    print(f'[Broker] Client disconnected: {client_name}')
                    break

    async def route(self, frm: str, to: str, payload: dict):
        ws = self.connections.get(to)
        if ws:
            await ws.send(json.dumps({'from': frm, 'payload': payload}))
        else:
            print(f'[Broker] No such client to route to: {to}')

    async def broadcast(self, frm: str, payload: dict):
        msg = json.dumps({'from': frm, 'payload': payload})
        for nm, ws in self.connections.items():
            await ws.send(msg)

    async def publish(self, topic: str, frm: str, payload: dict):
        msg = json.dumps({'from': frm, 'topic': topic, 'payload': payload})
        for name in self.topics.get(topic, set()):
            ws = self.connections.get(name)
            if ws:
                await ws.send(msg)

    async def _serve(self):
        server = await websockets.serve(self.handler, self.host, self.port)
        print(f'[Broker] Server listening on {self.host}:{self.port}')
        await server.wait_closed()

    def start(self):
        """Entry point: runs the server until interrupted."""
        asyncio.run(self._serve())

if __name__ == '__main__':
    MessageBrokerServer().start()