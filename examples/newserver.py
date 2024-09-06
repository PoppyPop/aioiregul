import asyncio
import sys
from datetime import datetime

import aiofiles
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


async def get_datas():
    # Get configuration from environment variables
    host = os.getenv("IREGUL_HOST", "i-regul.fr")
    port = int(os.getenv("IREGUL_PORT", "443"))
    device_id = os.getenv("IREGUL_DEVICE_ID")
    device_key = os.getenv("IREGUL_DEVICE_KEY")

    messagecode = 502
    message = f"cdraminfoREDACTED{{{messagecode}#}}"
    writer.write(message.encode())
    await writer.drain()

    while True:
        try:
            msg = await reader.readuntil(b"}")
        except asyncio.LimitOverrunError as e:
            print(e)
            sys.exit(1)
        except asyncio.IncompleteReadError as e:
            # Something else happened, handle error, exit, etc.
            print(e)
            sys.exit(1)
        else:
            if len(msg) == 0:
                print("orderly shutdown on server end")
                sys.exit(0)
            else:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                decoded = msg.decode("utf-8")
                if decoded.startswith("OLD"):
                    filename = f"{messagecode}-OLD-{timestamp}.txt"
                    print(f"Get old mesage of {len(decoded)} bytes")
                    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
                        await f.write(decoded)
                else:
                    filename = f"{messagecode}-NEW-{timestamp}.txt"
                    print(f"Get new mesage of {len(decoded)} bytes")
                    async with aiofiles.open(filename, mode="w", encoding="utf-8") as f:
                        await f.write(decoded)
                    break

    print("Close the connection")
    writer.close()
    await writer.wait_closed()


asyncio.run(get_datas())

# create an INET, STREAMing socket
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.settimeout(5)
# # now connect to the web server on port 80 - the normal http port
# s.connect(("i-regul.fr", 443))

# # 500
# 501 => request DATA refresh
# 502 => DATA + Nom propre
# {203#} => Degivrage


# {550#}" : "{540#}" : "{530#}" : "{520#}" : "{510#}

# Example raw socket code (use IRegulClient instead):
# device_id = os.getenv("IREGUL_DEVICE_ID")
# device_key = os.getenv("IREGUL_DEVICE_KEY")
# s.send(f"cdraminfo{device_id}{device_key}{{502#}}".encode())

# while True:
#     try:
#         msg = s.recv(8192)
#     except socket.timeout as e:
#         err = e.args[0]
#         # this next if/else is a bit redundant, but illustrates how the
#         # timeout exception is setup
#         if err == "timed out":
#             sleep(1)
#             print("recv timed out, retry later")
#             continue
#         else:
#             print(e)
#             sys.exit(1)
#     except socket.error as e:
#         # Something else happened, handle error, exit, etc.
#         print(e)
#         sys.exit(1)
#     else:
#         if len(msg) == 0:
#             print("orderly shutdown on server end")
#             sys.exit(0)
#         else:
#             print(msg.decode("utf-8"))
