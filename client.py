import asyncio
import json
import websockets

async def main():

    async with websockets.connect(
        "ws://127.0.0.1:8000/ws"
    ) as websocket:

        print("Connected")

        while True:

            msg = await websocket.recv()

            data = json.loads(msg)

            if data["type"] == "flag_update":

                print(
                    f"Flag {data['name']} "
                    f"changed to "
                    f"{data['enabled']}"
                )

asyncio.run(main())