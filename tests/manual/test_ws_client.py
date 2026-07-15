import asyncio
import websockets
import json

async def test():
    uri = "ws://127.0.0.1:8000/ws/echo"
    async with websockets.connect(uri) as websocket:
        message = {
            "sender": "Jeni",
            "receiver": "Mugunthan",
            "amount": 500
        }
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        parsed = json.loads(response)
        print("Server replied:", parsed)

asyncio.run(test())