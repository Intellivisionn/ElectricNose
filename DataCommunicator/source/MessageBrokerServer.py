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
        self.client_topics: dict[str, set[str]] = {}  # client -> set of topics

    async def handler(self, websocket, path=None):
        try:
            register = await websocket.recv()
            data = json.loads(register)
            if data.get('type') != 'register' or 'name' not in data:
                await websocket.close()
                return

            name = data['name']
            base_name = name.split('_')[0]  # Allow multiple connections from same base name
            connection_id = f"{base_name}_{id(websocket)}"
            
            self.connections[connection_id] = websocket
            self.client_topics[connection_id] = set()
            print(f'[Broker] Registered client: {connection_id}')

            async for message in websocket:
                msg = json.loads(message)
                mtype = msg.get('type')

                if mtype == 'subscribe':
                    topic = msg['topic']
                    self.topics.setdefault(topic, set()).add(connection_id)
                    self.client_topics[connection_id].add(topic)
                    print(f'[Broker] {connection_id} subscribed to {topic}')

                elif mtype == 'unsubscribe':
                    topic = msg['topic']
                    self.topics.get(topic, set()).discard(connection_id)
                    self.client_topics[connection_id].discard(topic)
                    print(f'[Broker] {connection_id} unsubscribed from {topic}')

                elif mtype == 'publish':
                    topic = msg['topic']
                    frm = msg['from']
                    payload = msg['payload']
                    await self.publish(topic, frm, payload)

                else:
                    to = msg.get('to')
                    frm = msg.get('from')
                    payload = msg.get('payload')
                    if to == 'broadcast':
                        await self.broadcast(frm, payload)
                    else:
                        await self.route(frm, to, payload)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f'[Broker] Connection handler failed: {e}')
        finally:
            if 'connection_id' in locals():
                # Clean up all subscriptions for this connection
                for topic in self.client_topics.get(connection_id, set()):
                    self.topics.get(topic, set()).discard(connection_id)
                self.client_topics.pop(connection_id, None)
                self.connections.pop(connection_id, None)
                print(f'[Broker] Client disconnected: {connection_id}')

    async def publish(self, topic: str, frm: str, payload: dict):
        msg = json.dumps({'from': frm, 'topic': topic, 'payload': payload})
        for connection_id in self.topics.get(topic, set()):
            ws = self.connections.get(connection_id)
            if ws:
                try:
                    await ws.send(msg)
                except websockets.exceptions.ConnectionClosed:
                    continue

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

    async def _serve(self):
        server = await websockets.serve(self.handler, self.host, self.port)
        print(f'[Broker] Server listening on {self.host}:{self.port}')
        await server.wait_closed()

    def start(self):
        """Entry point: runs the server until interrupted."""
        asyncio.run(self._serve())

if __name__ == '__main__':
    MessageBrokerServer().start()