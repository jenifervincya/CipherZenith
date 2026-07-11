import asyncio
import websockets

async def listen():
    uri = "ws://127.0.0.1:8000/ws/dashboard"
    async with websockets.connect(uri) as websocket:
        print("Connected to dashboard socket. Waiting for updates...")
        while True:
            message = await websocket.recv()
            print("Received:", message)

asyncio.run(listen())