import asyncio
import websockets

async def listen():
    uri = "ws://127.0.0.1:8000/ws/app"
    async with websockets.connect(uri) as websocket:
        print("App connected. Waiting for completion notice...")
        while True:
            message = await websocket.recv()
            print("App received:", message)

asyncio.run(listen())