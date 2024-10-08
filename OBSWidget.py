# Created by LeviSnoot
# https://github.com/LeviSnoot/FNFest-Status

import asyncio
import sys

async def run_player_status():
    print("Starting playerStatus.py...")
    process = await asyncio.create_subprocess_exec(
        'python', 'playerStatus.py',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def read_stream(stream, callback):
        while True:
            line = await stream.readline()
            if line:
                callback(line.decode('utf-8'))
            else:
                break

    await asyncio.gather(
        read_stream(process.stdout, lambda line: print(line, end='')),
        read_stream(process.stderr, lambda line: print(line, end=''))
    )

    await process.wait()
    print("playerStatus.py has exited.")

async def run_web_app():
    print("Starting web/app.py...")
    process = await asyncio.create_subprocess_exec(
        'python', 'web/app.py',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def read_stream(stream, callback):
        while True:
            line = await stream.readline()
            if line:
                decoded_line = line.decode('utf-8')
                if 'Running on' in decoded_line:
                    callback(decoded_line)
            else:
                break

    await asyncio.gather(
        read_stream(process.stdout, lambda line: print(line, end='')),
        read_stream(process.stderr, lambda line: print(line, end=''))
    )

    await process.wait()
    print("web/app.py has exited.")

async def main():
    await asyncio.gather(
        run_player_status(),
        run_web_app()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        try:
            loop = asyncio.get_running_loop()
            if not loop.is_closed():
                loop.run_until_complete(loop.shutdown_asyncgens())
        except RuntimeError as e:
            print(f"RuntimeError during loop shutdown: {e}")
        except Exception as e:
            print(f"Exception during loop shutdown: {e}")