import asyncio
import sys

import websockets

import serverstf.socket


def main():
    server = websockets.serve(serverstf.socket.Service(), "0.0.0.0", 9001)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
